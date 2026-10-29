#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Marco Wester <marco.wester@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: custom_rules
short_description: Manage SentinelOne custom detection rules
version_added: "2.4.0"
description:
  - Create, update and delete site-scoped custom detection rules.
  - Rules are identified by their exact name within the selected site.
options:
  console_url:
    description: Management console URL.
    type: str
    required: true
  token:
    description: SentinelOne API authentication token.
    type: str
    required: true
  state:
    description: Whether the rule should exist.
    type: str
    default: present
    choices: [present, absent]
  site_name:
    description: Name of the site in SentinelOne.
    type: str
    required: true
  name:
    description: Name identifying the rule within the site.
    type: str
    required: true
  description:
    description: Rule description. Omission clears an existing description.
    type: str
    default: ''
  severity:
    description: Rule severity.
    type: str
    default: Medium
    choices: [Info, Low, Medium, High, Critical]
  expiration_date:
    description:
      - Use V(Permanent) for a rule that never expires.
      - Otherwise provide an ISO 8601 timestamp with timezone, for example V(2027-03-15T10:20:00Z).
    type: str
    default: Permanent
  status:
    description:
      - Desired rule status. Transitional and deletion statuses are not accepted as input.
    type: str
    default: Active
    choices: [Active, Disabled, Draft]
  query_lang:
    description: S1 query language version.
    type: str
    default: '2.0'
    choices: ['1.0', '2.0']
  event_query:
    description:
      - Single event query, passed as C(s1ql) with C(queryType=events).
      - Exactly one of O(event_query) and O(correlation_query) is required for O(state=present).
    type: str
  correlation_query:
    description:
      - Correlation object passed unchanged as C(correlationParams) with C(queryType=correlation).
      - Use the API field names, including C(entity), C(matchInOrder) and C(subQueries).
      - Mutually exclusive with O(event_query).
    type: dict
  cool_off_minutes:
    description:
      - Suppress further alerts for this many minutes after the rule triggers, from 1 to 1440.
      - If omitted, new rules are created without C(coolOffSettings).
      - For existing rules with cool-off enabled, omission disables it by sending C(renotifyMinutes=0).
    type: int
  network_quarantine:
    description: Automatically quarantine alerted endpoints.
    type: bool
    default: false
  treat_as_threat:
    description: Treat-as-threat automatic response. V(Undefined) is sent as V(UNDEFINED).
    type: str
    default: UNDEFINED
    choices: [UNDEFINED, Undefined, Suspicious, Malicious]
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
requirements:
  - deepdiff >= 5.6
notes:
  - This module can also be called as C(sva.sentinelone.star_rules).
  - Only single-account management consoles are supported, as with the other collection modules.
  - The API token must have permission to view and manage rules at site scope, including their logic.
  - The API exposes rules only at the token's highest available scope.
  - Defaults are enforced on updates as well as on creation.
  - Check mode performs reads but does not modify rules.
  - Hiding rule logic is not supported. Rules with C(hideLogic=true) were not returned by the API in live testing.
  - Do not manage names already used by hidden rules. Such rules cannot be reliably updated or deleted by this module,
    and their names may cause duplicate rules to be created.
'''

EXAMPLES = r'''
---
- name: Create a single event rule
  sva.sentinelone.custom_rules:
    console_url: https://example.sentinelone.net
    token: "{{ sentinelone_token }}"
    site_name: Production
    name: Suspicious PowerShell
    event_query: 'event.type = "Process Creation" AND tgt.process.name = "powershell.exe"'
    severity: High
    cool_off_minutes: 60

- name: Create a correlation rule
  sva.sentinelone.custom_rules:
    console_url: https://example.sentinelone.net
    token: "{{ sentinelone_token }}"
    site_name: Production
    name: Repeated PowerShell execution
    status: Disabled
    expiration_date: '2027-03-15T10:20:00Z'
    correlation_query:
      entity: endpoint
      matchInOrder: false
      subQueries:
        - subQuery: 'event.type = "Process Creation" AND tgt.process.name = "powershell.exe"'
          matchesRequired: 3
      timeWindow:
        windowMinutes: 10

- name: Delete a custom rule
  sva.sentinelone.custom_rules:
    console_url: https://example.sentinelone.net
    token: "{{ sentinelone_token }}"
    site_name: Production
    name: Suspicious PowerShell
    state: absent
'''

RETURN = r'''
---
original_message:
  description: Details about the changes made or planned.
  type: dict
  returned: success
  sample: {"changes": "Rule is missing in site Production. Adding rule.", "siteName": "Production"}
message:
  description: Summary of the changes made or planned.
  type: str
  returned: success
  sample: Rule is missing in site Production. Adding rule.
'''

import copy
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors


class SentineloneCustomRules(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        super().__init__(module)
        self.rule_name = module.params["name"]
        self.desired_rule = self.get_desired_rule(module) if self.state == "present" else {}
        self.current_rule = self.get_current_rule(module)

    @staticmethod
    def normalize_expiration(value):
        expiration = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if expiration.tzinfo is None:
            raise ValueError("A timezone is required")
        return expiration.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def get_desired_rule(self, module: AnsibleModule):
        params = module.params
        if not params["name"].strip():
            module.fail_json(msg="name must not be empty.")
        if params["event_query"] is not None and not params["event_query"].strip():
            module.fail_json(msg="event_query must not be empty.")
        if params["correlation_query"] is not None and not params["correlation_query"]:
            module.fail_json(msg="correlation_query must not be empty.")
        if params["cool_off_minutes"] is not None and not 1 <= params["cool_off_minutes"] <= 1440:
            module.fail_json(msg="cool_off_minutes must be between 1 and 1440.")
        if len(params["description"]) > 2000:
            module.fail_json(msg="description must not exceed 2000 characters.")

        data = {
            "name": self.rule_name,
            "description": params["description"],
            "severity": params["severity"],
            "expirationMode": "Permanent",
            "status": params["status"],
            "queryLang": params["query_lang"],
            "networkQuarantine": params["network_quarantine"],
            "treatAsThreat": "UNDEFINED" if params["treat_as_threat"] == "Undefined" else params["treat_as_threat"],
        }
        if params["expiration_date"] != "Permanent":
            try:
                data["expiration"] = self.normalize_expiration(params["expiration_date"])
            except ValueError as err:
                module.fail_json(msg=f"expiration_date must be Permanent or an ISO 8601 timestamp with timezone: {err}")
            data["expirationMode"] = "Temporary"
        if params["event_query"] is not None:
            data["queryType"] = "events"
            data["s1ql"] = params["event_query"]
        else:
            data["queryType"] = "correlation"
            data["correlationParams"] = copy.deepcopy(params["correlation_query"])
        if params["cool_off_minutes"] is not None:
            data["coolOffSettings"] = {"renotifyMinutes": params["cool_off_minutes"]}
        return data

    def get_current_rule(self, module: AnsibleModule):
        query = {"siteIds": self.site_id, "scopeLevel": "site", "limit": 1000}
        if len(self.rule_name) >= 2:
            query["name__contains"] = self.rule_name
        matches = []
        seen_cursors = set()
        while True:
            response = self.api_call(
                module, f"{self.api_endpoint_custom_rules}?{urlencode(query)}",
                error_msg="Failed to get custom rules."
            )
            for rule in response["data"]:
                if (rule["name"] == self.rule_name and rule.get("scope") == "site"
                        and (self.site_id in (rule.get("scopeId") or []) or rule.get("siteId") == self.site_id)):
                    matches.append(rule)
            cursor = response["pagination"]["nextCursor"]
            if not cursor:
                break
            if cursor in seen_cursors:
                module.fail_json(msg="Failed to get custom rules: API returned a repeated pagination cursor.")
            seen_cursors.add(cursor)
            query["cursor"] = cursor
        if len(matches) > 1:
            module.fail_json(msg=f"Multiple custom rules named {self.rule_name} found in site {self.site_name}.")
        return matches[0] if matches else {}

    def get_rule_body(self):
        data = copy.deepcopy(self.desired_rule)
        if "coolOffSettings" not in data and self.current_rule.get("coolOffSettings"):
            data["coolOffSettings"] = {"renotifyMinutes": 0}
        return {"filter": {"siteIds": [self.site_id]}, "data": data}

    def get_diff(self, module: AnsibleModule):
        current = {key: self.current_rule.get(key) for key in self.desired_rule}
        desired = copy.deepcopy(self.desired_rule)
        current["description"] = current.get("description") or ""
        if current["treatAsThreat"] is None:
            current["treatAsThreat"] = "UNDEFINED"
        if desired["expirationMode"] == "Temporary" and current.get("expiration"):
            try:
                current["expiration"] = self.normalize_expiration(current["expiration"])
            except ValueError as err:
                module.fail_json(msg=f"Invalid expiration timestamp returned by API: {err}")
        current["status"] = self.normalize_status(current["status"])
        if "coolOffSettings" not in desired:
            current["coolOffSettings"] = self.current_rule.get("coolOffSettings") or None
            desired["coolOffSettings"] = None
        if desired["queryType"] == "correlation":
            # The API supplies this documented default even when omitted from the request.
            for data in (current, desired):
                if isinstance(data.get("correlationParams"), dict):
                    data["correlationParams"] = copy.deepcopy(data["correlationParams"])
                    data["correlationParams"].setdefault("timeWindow", {"windowMinutes": 480})
        return self.compare(current, desired)

    @staticmethod
    def normalize_status(status):
        return {"Activating": "Active", "Disabling": "Disabled"}.get(status, status)

    def ensure_rule_status(self, rule: dict, module: AnsibleModule):
        desired_status = self.desired_rule["status"]
        if self.normalize_status(rule.get("status")) == desired_status:
            return rule

        rule_id = rule["id"]
        if desired_status == "Draft":
            response = self.api_call(
                module, f"{self.api_endpoint_custom_rules}/{rule_id}", "PUT", body=self.get_rule_body(),
                error_msg="Failed to set custom rule status to Draft."
            )
            if not isinstance(response.get("data"), dict) or response["data"].get("id") != rule_id:
                module.fail_json(msg="API did not confirm the rule ID when setting status to Draft.",
                                 changed=True, rule_id=rule_id)
        else:
            action = "enable" if desired_status == "Active" else "disable"
            response = self.api_call(
                module, f"{self.api_endpoint_custom_rules}/{action}", "PUT",
                body={"filter": {"siteIds": [self.site_id], "ids": [rule_id]}},
                error_msg=f"Failed to set custom rule status to {desired_status}."
            )
            if not isinstance(response.get("data"), dict) or response["data"].get("affected") != 1:
                module.fail_json(msg=f"API did not confirm exactly one rule when setting status to {desired_status}.",
                                 changed=True, rule_id=rule_id)

        current = self.get_current_rule(module)
        if current.get("id") != rule_id:
            module.fail_json(msg="Could not read the custom rule after enforcing its status.",
                             changed=True, rule_id=rule_id)
        if self.normalize_status(current.get("status")) != desired_status:
            module.fail_json(
                msg=f"Custom rule status is {current.get('status')}, expected {desired_status} after enforcement.",
                changed=True, rule_id=rule_id
            )
        return current

    def create_rule(self, module: AnsibleModule):
        response = self.api_call(
            module, self.api_endpoint_custom_rules, "POST", body=self.get_rule_body(),
            error_msg="Failed to create custom rule."
        )
        if not isinstance(response.get("data"), dict) or not response["data"].get("id"):
            module.fail_json(msg="Custom rule should have been created but API result did not contain a rule ID.")
        response["data"] = self.ensure_rule_status(response["data"], module)
        return response

    def update_rule(self, module: AnsibleModule):
        response = self.api_call(
            module, f"{self.api_endpoint_custom_rules}/{self.current_rule['id']}", "PUT",
            body=self.get_rule_body(), error_msg="Failed to update custom rule."
        )
        if not isinstance(response.get("data"), dict) or not response["data"].get("id"):
            module.fail_json(msg="Custom rule should have been updated but API result did not contain a rule ID.")
        response["data"] = self.ensure_rule_status(response["data"], module)
        return response

    def delete_rule(self, module: AnsibleModule):
        response = self.api_call(
            module, self.api_endpoint_custom_rules, "DELETE",
            body={"filter": {"siteIds": [self.site_id], "ids": [self.current_rule["id"]]}},
            error_msg="Failed to delete custom rule."
        )
        if not isinstance(response.get("data"), dict) or response["data"].get("affected") != 1:
            module.fail_json(msg="Exactly one custom rule should have been deleted but API result did not confirm it.")
        return response


def run_module():
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        site_name=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        severity=dict(type='str', default='Medium', choices=['Info', 'Low', 'Medium', 'High', 'Critical']),
        expiration_date=dict(type='str', default='Permanent'),
        status=dict(type='str', default='Active', choices=['Active', 'Disabled', 'Draft']),
        query_lang=dict(type='str', default='2.0', choices=['1.0', '2.0']),
        event_query=dict(type='str'),
        correlation_query=dict(type='dict'),
        cool_off_minutes=dict(type='int'),
        network_quarantine=dict(type='bool', default=False),
        treat_as_threat=dict(type='str', default='UNDEFINED', choices=['UNDEFINED', 'Undefined', 'Suspicious', 'Malicious']),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('event_query', 'correlation_query')],
        required_if=[('state', 'present', ('event_query', 'correlation_query'), True)],
        supports_check_mode=True,
    )
    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    rule_obj = SentineloneCustomRules(module)
    message = ''
    diffs = {}
    if rule_obj.state == 'present':
        if rule_obj.current_rule:
            diff = rule_obj.get_diff(module)
            if diff:
                message = f'Rule exists in site {rule_obj.site_name} but is not up-to-date. Updating rule.'
                diffs = {'changes': json.loads(diff.to_json()), 'siteName': rule_obj.site_name}
                if not module.check_mode:
                    rule_obj.update_rule(module)
        else:
            message = f'Rule is missing in site {rule_obj.site_name}. Adding rule.'
            diffs = {'changes': message, 'siteName': rule_obj.site_name}
            if not module.check_mode:
                rule_obj.create_rule(module)
    elif rule_obj.current_rule:
        message = f'Rule exists in site {rule_obj.site_name}. Deleting rule.'
        diffs = {'changes': message, 'siteName': rule_obj.site_name}
        if not module.check_mode:
            rule_obj.delete_rule(module)
    module.exit_json(changed=bool(diffs), original_message=diffs, message=message)


def main():
    run_module()


if __name__ == '__main__':
    main()
