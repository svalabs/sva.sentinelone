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

DOCUMENTATION = '''
---
module: sentinelone_config_overrides
short_description: "Manage SentinelOne Config Overrides"
version_added: "1.0.0"
description:
  - "This module allows to create/update/delete config overrides on site or group level in SentinelOne management console"
  - "You can only create one config override for the same combination of OS Type, Agent Version and Scope."
  - "These three parameters are the identifiers of the config override"
  - "If I(state=present) you can create or update the override object."
  - "If you update an existing override your config_overide settings will be merged into the existing data."
  - "You can also rename the config override or change the description."
  - "If I(state=absent) the data specified via the config_override parameter will be removed from the current override object."
  - "If I(state=prune) the whole override object will be deleted."
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
  state:
    description:
      - "C(present): Make sure the config override exists. If no override object for the selected scope exists it will be created."
      - "If an override object already exists the new config will get merged into the existing one."
      - "C(absent): Absent will only remove the settings from the override object you specify by C(config_override) parameter."
      - "If the C(config_override) parameter conatins all existing settings the whole object will be deleted instead"
      - "In this mode only the keys of C(config_override) will be used. Values will be igonred."
      - "Absent will let the other overrides in the same scope untouched."
      - "C(prune): The whole config override object will be deleted."
    type: str
    default: present
    required: false
    choices:
      - present
      - absent
      - prune
  site_name:
    description:
      - "Name of the site in SentinelOne"
    type: str
    required: true
  group:
    description:
      - "Enter group name here"
      - "If this option is set the scope is set to group level. Otherwise scope is set to site level"
    type: str
    default: ""
    required: false
  name:
    description:
      - "Name of the config override"
      - "Will be ignored if I(state=absent) or I(state=prune)"
      - "Required if I(state=present)"
    type: str
    required: false
  os_type:
    description:
      - "The os type for which the config is set"
    type: str
    required: true
    choices:
      - windows
      - linux
  agent_version:
    description:
      - "Optional: Set config override for a specific agent version."
      - "If not set the config override will apply on all agent versions"
    type: str
    required: false
    default: "ALL"
  config_override:
    description:
      - "The config override data"
      - "Required when I(state=present) or I(state=absent)"
      - "Will be ignored if I(state=prune)"
    type: dict
    required: false
  description:
    description:
      - "Optional: Set a description for the config override"
      - "Will be ignored if I(state=absent) or I(state=prune)"
    type: str
    required: false
    default: ""
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
  - "Currently not applicable for account level config overrides"
'''

EXAMPLES = r'''
---
- name: Create/Update config_override for all agents on site
  sentinelone_config_overrides:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "test_override"
    os_type: "windows"
    config_override: { powershellProtection: true }
- name: Create/Update config_override for all agents on group
  sentinelone_config_overrides:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    group: "testgroup"
    name: "test_override"
    os_type: "windows"
    config_override:
      powershellProtection: true
- name: Create/Update config_override for specific agent version on group
  sentinelone_config_overrides:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    group: "testgroup"
    name: "test_override"
    os_type: "windows"
    agent_version: "21.7.2.1038"
    config_override:
      powershellProtection: true
- name: Delete config_override for all agents on group
  sentinelone_config_overrides:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    state: "absent"
    group: "testgroup"
    os_type: "windows"
- name: Delete config_override for specific agent version on site
  sentinelone_config_overrides:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    state: absent
    os_type: "windows"
    agent_version: "21.7.2.1038"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: {"changes": "Creating non existing site level config override: test", "siteId": "99999999999999"}
message:
    description: Get basic infos about the changes made
    type: list
    returned: on success
    sample: "Creating non existing site config override: test"
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors
from ansible.module_utils.six.moves.urllib.parse import quote_plus
import copy


class SentineloneConfigOverrides(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the ConfigOverrides object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # super class __init__ only expects "groups" as list not "group" as string. Translating it here
        if module.params["group"]:
            # Pass group as single itemed list if group is set
            module.params["groups"] = [module.params["group"]]
        else:
            # Pass empty list when group is not set
            module.params["groups"] = []

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.config_override_name = module.params["name"]
        self.os_type = module.params["os_type"]
        if module.params["agent_version"]:
            self.agent_version = module.params["agent_version"]
        else:
            self.agent_version = "ALL"
        self.config_override = module.params["config_override"]
        self.description = module.params["description"]
        if self.current_group_ids_names:
            # If group is passed, desired_state_group_ids should be filled with one group_id
            # after super.__init__(module). Extract group_id
            self.group_id = self.current_group_ids_names[0][0]
            self.group_name = self.current_group_ids_names[0][1]
        else:
            self.group_id = ""

        self.current_config_override = self.get_current_config_override(module)
        self.current_config_override_id = self.current_config_override.get('id', None)

        self.desired_state_object = self.create_desired_state_object()

    def create_desired_state_object(self):
        """
        Creates the desired state config overrides object based on the parameters passed to the module

        :return: The config override desired_state_object
        :rtype: dict
        """

        desired_state_object = {
            'config': self.config_override,
            'description': self.description,
            'osType': self.os_type,
            'name': self.config_override_name
        }

        if self.agent_version == "ALL":
            # If override should apply for all agent versions
            desired_state_object['versionOption'] = 'ALL'
        else:
            # If override should apply for specific agent version
            desired_state_object['versionOption'] = 'SPECIFIC'
            desired_state_object['agentVersion'] = self.agent_version
        if self.group_id:
            # If scope is group level
            desired_state_object['group'] = {'id': self.group_id}
            desired_state_object['scope'] = "group"
        else:
            # If scope is site level
            desired_state_object['site'] = {'id': self.site_id}
            desired_state_object['scope'] = "site"

        return desired_state_object

    def get_current_config_override(self, module: AnsibleModule):
        """
        API call to get the current config override which is currently set. Can be used on site or group level

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Config override object
        :rtype: dict
        """

        # Build API query depending on scope and agent_version
        query_options = [f"osTypes={quote_plus(self.os_type)}"]

        if self.group_id:
            query_options.append(f"groupIds={self.group_id}")
            error_msg = f"Failed to get current config_override for group with id {self.group_id}."
        else:
            query_options.append(f"siteIds={self.site_id}")
            error_msg = f"Failed to get current config_override for site with id {self.site_id}."

        if self.agent_version == "ALL":
            query_options.append("versionOption=ALL")
        else:
            query_options.append("versionOption=SPECIFIC")
            query_options.append(f"agentVersions={self.agent_version}")

        query_uri = '&'.join(query_options)
        api_url = f"{self.api_endpoint_config_overrides}?{query_uri}"
        response = self.api_call(module, api_url, error_msg=error_msg)

        response_data = response['data']
        count_config_overrides = len(response_data)

        if count_config_overrides > 1:
            module.fail_json(msg=("Error in get_current_config_override: filtered_response has more than one element. "
                                  "Should only contain zero or one element."))
        elif count_config_overrides == 1:
            return response_data[0]
        else:
            return {}

    def delete_config_override(self, current_config_override_id: str, module: AnsibleModule):
        """
        Method to delete existing config override

        :param current_config_override_id: id of the config override which should be deleted
        :type current_config_override_id: str or None
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        if current_config_override_id:
            # API call to delete the config override which is currently set. Can be used on site or group level
            api_url = f"{self.api_endpoint_config_overrides}/{current_config_override_id}"
            error_msg = "Failed to delete config override."
            response = self.api_call(module, api_url, "DELETE", error_msg=error_msg)

            if not response['data']['success']:
                module.fail_json(msg=("Error in delete_config_override: Config override should have been deleted via "
                                      "API but API result was not 'success'"))
        else:
            response = "Nothing to delete"

        return response

    def create_config_override(self, create_body: dict, module: AnsibleModule):
        """
        API call to create the config override

        :param create_body: Body for the create API call
        :type create_body: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        api_url = self.api_endpoint_config_overrides
        error_msg = "Failed to create config override."
        response = self.api_call(module, api_url, "POST", body=create_body, error_msg=error_msg)

        if not response['data']:
            module.fail_json(msg=("Error in create_config_override: config override should have been created via API "
                                  "but API result was empty"))

        return response

    def prune_config_override(self, current_config_override_id: str, current_config_override_obj: dict,
                              module: AnsibleModule):
        """
        Deletes the whole config override object

        :param current_config_override_id: id of the currently existing config override
        :type current_config_override_id: str
        :param current_config_override_obj: object containing the current config override
        :type current_config_override_obj: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Returns the module messages basic_message and diffs
        :rtype: tuple
        """

        override_name = current_config_override_obj['name']
        self.delete_config_override(current_config_override_id, module)
        if self.group_id:
            # if scope is group level
            group_name = self.group_name
            diffs = {'changes': f"Config override: {override_name} pruned", 'groupId': self.group_id}
            basic_message = f"Config override {override_name} for group {group_name} pruned"
        else:
            # if scope is site level
            site_name = self.site_name
            site_id = self.site_id
            diffs = {'changes': f"Config override: {override_name} pruned", 'siteId': site_id}
            basic_message = f"Config override {override_name} for site {site_name} pruned"

        return basic_message, diffs

    def recreate_config_override(self, current_config_override_id: str, new_config_override_obj: dict,
                                 module: AnsibleModule):
        """
        Recreates the config override with new_config_override_obj data

        :param current_config_override_id: The id of the currently existing config override
        :type current_config_override_id: str
        :param new_config_override_obj: object of the new config override
        :type new_config_override_obj: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        """

        self.delete_config_override(current_config_override_id, module)
        # Use new_config_override_obj as body for the create request. But we have to remove 'id' first
        new_config_override_obj.pop('id', None)
        create_body = {'data': new_config_override_obj}
        self.create_config_override(create_body, module)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent', 'prune']),
        site_name=dict(type='str', required=True),
        group=dict(type='str', required=False, default=""),
        name=dict(type='str', required=False),
        os_type=dict(type='str', required=True, choices=['windows', 'linux']),
        agent_version=dict(type='str', required=False, default="ALL"),
        config_override=dict(type='dict', required=False),
        description=dict(type='str', required=False, default="")
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ('name', 'config_override')),
            ('state', 'absent', ('config_override',))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create config_override Object
    config_override_obj = SentineloneConfigOverrides(module)
    group_id = config_override_obj.group_id
    state = config_override_obj.state
    override_name = config_override_obj.config_override_name
    current_config_override_obj = config_override_obj.current_config_override
    current_config_override_id = config_override_obj.current_config_override_id

    diffs = ""
    basic_message = ""

    if state == "present":
        # if we want to create/update config override
        if group_id:
            # if scope is group level
            group_name = config_override_obj.group_name
            desired_state_object = config_override_obj.desired_state_object
            diff, merged_config_override = config_override_obj.merge_compare(current_config_override_obj,
                                                                             desired_state_object)
            if current_config_override_obj:
                if diff:
                    # if group config override is different from desired state, update it
                    diffs = {'changes': dict(diff), 'groupId': group_id}
                    basic_message = f"Config override {override_name} for group {group_name} updated"
            else:
                diffs = {'changes': f"Non existing config override {override_name} created",
                         'groupId': group_id}
                basic_message = f"Non existing config override {override_name} for group {group_name} created"

        else:
            # if scope is site level
            # check if site has the desired settings already
            site_name = config_override_obj.site_name
            site_id = config_override_obj.site_id
            desired_state_object = config_override_obj.desired_state_object
            diff, merged_config_override = config_override_obj.merge_compare(current_config_override_obj,
                                                                             desired_state_object)
            if current_config_override_obj:
                if diff:
                    # if site config override is different from desired state, update it
                    diffs = {'changes': dict(diff), 'SiteId': site_id}
                    basic_message = f"Config override {override_name} for site {site_name} updated"
            else:
                diffs = {'changes': f"Non existing config override {override_name} created",
                         'siteId': site_id}
                basic_message = f"Non existing config override {override_name} for site {site_name} created"

        if diffs:
            # Delete and recreate the config override object if changes were made to the object
            config_override_obj.recreate_config_override(current_config_override_id, merged_config_override, module)

    elif state == "absent":
        if current_config_override_obj:
            # DeepCopy to be able to check if changes were made
            new_config_override_obj = copy.deepcopy(current_config_override_obj)
            current_config_override = current_config_override_obj['config']
            # Pointer to the subobject in 'config'.
            # Updates in new_config_override will also affect new_config_override_obj['config']
            new_config_override = new_config_override_obj['config']
            delete_config_override = config_override_obj.config_override
            config_override_obj.remove_dict_from_dict(new_config_override, delete_config_override)
            diff = config_override_obj.compare(current_config_override, new_config_override)
            if not new_config_override:
                # Delete the whole config override object if new_config_override is empty. This meens the passed
                # config_override parameter deletes all Settings in the object. So deletion is necessary
                basic_message, diffs = config_override_obj.prune_config_override(current_config_override_id,
                                                                                 current_config_override_obj, module)
            elif diff:
                # Delete and recreate the config override object if changes were made to the object
                config_override_obj.recreate_config_override(current_config_override_id, new_config_override_obj,
                                                             module)
                if group_id:
                    diffs = {'changes': dict(diff), 'groupId': group_id}
                    basic_message = f"Config override settings from existing config override for " \
                                    f"group {group_id} removed"
                else:
                    site_name = config_override_obj.site_name
                    site_id = config_override_obj.site_id
                    diffs = {'changes': dict(diff), 'siteId': site_id}
                    basic_message = f"Config override settings from existing config override for " \
                                    f"site {site_name} removed"
    else:
        # if we want to delete config_override (state = prune)
        if current_config_override_obj:
            basic_message, diffs = config_override_obj.prune_config_override(current_config_override_id,
                                                                             current_config_override_obj,
                                                                             module)

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
