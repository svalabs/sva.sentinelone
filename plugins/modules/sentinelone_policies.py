#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Marco Wester <marco.wester@sva.de>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: sentinelone_policies
short_description: "Manage SentinelOne Policies"
version_added: "1.0.0"
description:
  - "This module is able to update policies in SentinelOne"
options:
  console_url:
    description:
      - "Insert your management console URL"
    type: str
    required: true
  token:
    description:
      - "SentinelOne API auth token to authenticate at the management API"
    type: str
    required: true
  inherit:
    description:
      - "Inherit policy from upper scope"
      - "If set to yes I(policy) will be ignored and the policy will be inherited from upper scope"
    type: bool
    default: no
    required: false
  site_name:
    description:
      - "Name of the site in SentinelOne"
    type: str
    required: true
  groups:
    description:
      - "Set this option to set the scope to group level"
      - "A list with groupnames where the policy should be changed"
    type: list
    elements: str
    default: []
    required: false
  policy:
    description:
      - "Define the settings which should be set in policy. Available options can be referred in API documentation"
      - "e.g. agentUiOn or snapshotsOn"
      - "Required if I(inherit=no)"
      - "Will be ignored if I(inherit=yes)"
    type: dict
    required: false
    default: {}
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
  - "Currently not applicable for account level policies"
'''

EXAMPLES = r'''
---
- name: Set custom policy on multiple groups
  sentinelone_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - group1
      - group2
    policy:
      agentUiOn: false
      agentUi:
        agentUiOn: false
- name: Set custom policy on site
  sentinelone_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    policy:
      agentUiOn: false
      agentUi:
        agentUiOn: false
- name: Revert to group default policy inherited from site
  sentinelone_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    inherit: "yes"
    groups:
      - group1
      - group2
- name: Revert to site default policy inherited from account
  sentinelone_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    inherit: "yes"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: [{"changes": {"values_changed": {"root['agentUi']['agentUiOn']": {"new_value": false, "old_value": true},
    "root['agentUiOn']": {"new_value": false, "old_value": true}}}, "groupId": "99999999999999"},
    {"changes": {"values_changed": {"root['agentUi']['agentUiOn']": {"new_value": false, "old_value": true},
    "root['agentUiOn']": {"new_value": false, "old_value": true}}}, "groupId": "99999999999999"}]
message:
    description: Get basic infos about the changes made
    type: list
    returned: on success
    sample: ["Updating policy in group with id 99999999999999", "Updating policy in group with id 99999999999999"]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors


class SentinelonePolicies(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the policies object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # super class __init__ only expects "state" not "inherit". Translating it here
        module.params["state"] = module.params["inherit"]

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        # Translating "state" back to "inherit"
        self.inherit = self.state
        self.desired_state_policy = module.params["policy"]

    def get_current_policy(self, site_group_id: str, module: AnsibleModule):
        """
        Get the policy which is currently set from API. Can be used on site or group scope

        :param site_group_id: Site or group id
        :type site_group_id: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Policy object
        :rtype: dict
        """

        # API call to get the policy which is currently set. Can be used on site or group level
        if self.current_group_ids_names:
            api_url = f"{self.api_endpoint_groups}/{site_group_id}/policy"
        else:
            api_url = f"{self.api_endpoint_sites}/{site_group_id}/policy"

        error_msg = f"Failed to get current policy for site or group with id {site_group_id}."
        response = self.api_call(module, api_url, error_msg=error_msg)

        return response

    def update_policy(self, site_group_id: str, update_body: dict, module: AnsibleModule):
        """
        API call to update the policy. Can be used on site or group level

        :param site_group_id: Site or group id
        :type site_group_id: str
        :param update_body: Dictionary object which is used for updating the existing policy object
        :type update_body: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        if self.current_group_ids_names:
            # group level scope
            api_url = f"{self.api_endpoint_groups}/{site_group_id}/policy"
        else:
            # site level scope
            api_url = f"{self.api_endpoint_sites}/{site_group_id}/policy"

        error_msg = f"Failed to update policy with site or group id {site_group_id}."
        response = self.api_call(module, api_url, "PUT", body=update_body, error_msg=error_msg)

        if not response['data']:
            module.fail_json(msg=(f"Error in update_policy with site or group id {site_group_id}: Policy should have "
                                  "been updated via API but result was empty"))

        return response

    def revert_policy(self, site_group_id: str, module: AnsibleModule):
        """
        API-call to enable policy inheritance. Can be used on site or group level

        :param site_group_id: site or group id
        :type site_group_id: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        if self.current_group_ids_names:
            api_url = f"{self.api_endpoint_groups}/{site_group_id}/revert-policy"
        else:
            api_url = f"{self.api_endpoint_sites}/{site_group_id}/revert-policy"

        error_msg = f"Failed to revert policy with site or group id {site_group_id}."
        response = self.api_call(module, api_url, "PUT", error_msg=error_msg)

        if not response['data']['success']:
            module.fail_json(msg=(f"Error in revert_pollicy with site or group id {site_group_id}: Policy should have "
                                  "been updated via API but result was empty"))

        return response

    @staticmethod
    def get_update_body(policy_settings: dict):
        """
        Prepare the merged object for post request

        :param policy_settings: desired state policy settings
        :type policy_settings: dict
        :return: update body for API
        :rtype: dict
        """

        # Remove deprecated policy settings. The module would not work correctly in some circumstances
        del policy_settings['agentNotification']
        del policy_settings['agentUiOn']

        policy_object = {'data': policy_settings}

        return policy_object


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        inherit=dict(type='bool', required=False, default='false'),
        site_name=dict(type='str', required=True),
        groups=dict(type='list', required=False, elements='str', default=[]),
        policy=dict(type='dict', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('inherit', False, ('policy',))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create policy Object
    policy_obj = SentinelonePolicies(module)
    current_group_ids_names = policy_obj.current_group_ids_names
    inherit = policy_obj.inherit

    diffs = []
    basic_message = []
    if not inherit:
        # if we want to set a custom policy
        if current_group_ids_names:
            # if scope is group level
            for current_group_id_name in current_group_ids_names:
                current_group_id = current_group_id_name[0]
                # check if every group has the desired settings already
                current_policy = policy_obj.get_current_policy(current_group_id, module)
                desired_state_policy = policy_obj.desired_state_policy
                diff, merged_policy = policy_obj.merge_compare(current_policy['data'], desired_state_policy)
                if diff:
                    # if group policy is different from desired state, update it
                    current_group_name = current_group_id_name[1]
                    diffs.append({'changes': dict(diff), 'groupId': current_group_id})
                    basic_message.append(f"Updating policy for group {current_group_name}")
                    update_body = policy_obj.get_update_body(merged_policy)
                    policy_obj.update_policy(current_group_id, update_body, module)
        else:
            # if scope is site level
            # check if site has the desired settings already
            site_name = policy_obj.site_name
            site_id = policy_obj.site_id
            current_policy = policy_obj.get_current_policy(site_id, module)
            desired_state_policy = policy_obj.desired_state_policy
            diff, merged_policy = policy_obj.merge_compare(current_policy['data'], desired_state_policy)
            if diff:
                # if site policy is different from desired state, update it
                diffs.append({'changes': dict(diff), 'SiteId': site_id})
                basic_message.append(f"Updating policy for site {site_name}")
                update_body = policy_obj.get_update_body(merged_policy)
                policy_obj.update_policy(site_id, update_body, module)
    else:
        # if we want to enable inheritance
        if current_group_ids_names:
            # if scope is group level
            for current_group_id_name in current_group_ids_names:
                current_group_id = current_group_id_name[0]
                current_policy = policy_obj.get_current_policy(current_group_id, module)
                if not current_policy["data"]["inheritedFrom"]:
                    # If inheritedFrom is "None" it will enable inheritance
                    current_group_name = current_group_id_name[1]
                    diffs.append({'changes': "Inheritance from site scope enabled", 'groupId': current_group_id})
                    basic_message.append(f"Enable inheritance from site scope in group {current_group_name}")
                    policy_obj.revert_policy(current_group_id, module)
        else:
            # if scope is site level
            site_name = policy_obj.site_name
            site_id = policy_obj.site_id
            current_policy = policy_obj.get_current_policy(site_id, module)
            if not current_policy["data"]["inheritedFrom"]:
                # If inheritedFrom is "None" it will enable inheritance
                diffs.append({'changes': "Inheritance from account scope enabled", 'siteId': site_id})
                basic_message.append(f"Enable inheritance from account scope in site {site_name}")
                policy_obj.revert_policy(site_id, module)

    result = dict(
        changed=False,
        original_message=str(diffs),
        message=basic_message
    )

    # If we made changes to the objects the list diffs is not empty.
    # So we can use it to update result['changes'] to True if necessary
    if diffs:
        result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
