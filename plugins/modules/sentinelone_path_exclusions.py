#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marco Wester <marco.wester@sva.de>, Lasse Wackers <lasse.wackers@sva.de>
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
module: sentinelone_path_exclusions
short_description: "Manage SentinelOne Path Exclusions"
version_added: "1.0.0"
description:
  - "This module is able to create, update and delete path exclusions in SentinelOne"
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
      - "Select the I(state) of exclusion"
    type: str
    default: present
    required: false
    choices:
      - present
      - absent
  site_name:
    description:
      - "Name of the site in SentinelOne"
    type: str
    required: true
  groups:
    description:
      - "Set this option to set the scope to group level"
      - "A list with groupnames which the exclusions are to be attached"
    type: list
    elements: str
    default: []
    required: false
  os_type:
    description:
      - "Define the operating system for the exclusion. Required if I(state=present)"
    type: str
    required: false
    choices:
      - windows
      - linux
  os_path:
    description:
      - "Os path of the exclusion."
      - "If the path a folder, the path must end with / (linux) or \\ (windows)"
    type: str
    required: true
  include_subfolders:
    description:
      - "If yes, the exclusion will scope subfolders as well. Is ignored if I(os_path) is not a folder (does not end with / (linux) or \\ (windows))"
    type: bool
    required: false
    default: no
  ef_alerts_mitigation:
    description:
      - "Exclusion Function to exclude I(os_path) for alerts and mitigation"
    type: bool
    required: false
    default: yes
  ef_binary_vault:
    description:
      - "Exclusion Function to exclude I(os_path) for Binary Vaults"
    type: bool
    required: false
    default: no
  mode:
    description:
      - "Defines the exclusion mode for this exclusion. Required if I(state=present)"
    type: str
    required: false
    choices:
      - suppress_alerts
      - interoperability
      - interoperability_extended
      - performance_focus
      - performance_focus_extended
  description:
    description:
      - "A short description to describe the exclusion"
    type: str
    required: false
    default: ""
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
  - "Lasse Wackers (@mordecaine) <lasse.wackers@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
  - "Currently not applicable for account level exclusions"
  - "Currently not applicable for MacOS"
'''

EXAMPLES = r'''
---
- name: Create exclusion in site scope
  sentinelone_path_exclusions:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    os_path: "C:\\Test1234\\"
    mode: "performance_focus"
    os_type: "windows"
- name: Create exclusion in single group
  sentinelone_path_exclusions:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups: "MariaDB"
    os_path: "C:\\Test1234\\"
    mode: "interoperability_extended"
    os_type: "windows"
- name: Create exclusion in multiple groups
  sentinelone_path_exclusions:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - "MariaDB"
      - "MaxDB"
    os_path: "C:\\Test1234\\"
    mode: "performance_focus_extended"
    os_type: "windows"
- name: Create exclusion in multiple groups and disable automatic upload to Binary Vault
  sentinelone_path_exclusions:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - "MariaDB"
      - "MaxDB"
    include_subfolders: true
    os_path: "C:\\Test1234\\"
    mode: "performance_focus_extended"
    os_type: "windows"
    ef_binary_vault: true
- name: Delete exclusion in site scope
  sentinelone_path_exclusions:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "msd"
    os_path: "C:\\Test1234\\"
- name: Delete exclusion in group scope
  sentinelone_path_exclusions:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "msd"
    groups:
      - "MariaDB"
      - "MaxDB"
    os_path: "C:\\Test1234\\"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    returned: on success
    type: str
    sample: [{"changes": {"values_changed": {"root['mode']":
    {"new_value": "disable_all_monitors_deep", "old_value": "disable_all_monitors"}}}, "siteId": ["99999999999999999"]}]
message:
    description: Get basic infos about the changes made
    returned: on success
    type: list
    sample: [ "Exclusion is missing in a group. Creating exclusion." ]
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors
from ansible.module_utils.six.moves.urllib.parse import quote_plus
from ansible.module_utils.urls import re


class SentineloneExclusions(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the Exclusions object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.description = module.params["description"]
        self.exclusion_path = module.params["os_path"]
        self.os_type = module.params["os_type"]
        self.mode = module.params["mode"]
        self.ef_binary_vault = module.params["ef_binary_vault"]
        self.include_subfolders = module.params["include_subfolders"]
        self.ef_alerts_mitigation = module.params["ef_alerts_mitigation"]

        # Do sanity checks
        self.check_sanity(self.ef_alerts_mitigation, self.ef_binary_vault, module)

        # Translate mode to API value
        self.mode_name = self.get_mode_name(self.mode, self.os_type, self.state, module)

        self.path_exclusion_type = self.get_path_exclusion_type(self.include_subfolders, self.exclusion_path)
        self.actions = self.get_actions(self.ef_alerts_mitigation, self.ef_binary_vault)

        self.current_group_ids = list(map(lambda current_group_id_name: current_group_id_name[0],
                                          self.current_group_ids_names))

        self.desired_state_exclusion = self.get_desired_state_exclusion_body()
        self.current_exclusions = self.get_current_exclusions(self.current_group_ids, self.exclusion_path, module)

        self.current_exclusion_ids = list(map(lambda exclusion: exclusion['id'], self.current_exclusions['data']))

    @staticmethod
    def get_mode_name(mode: str, os_type: str, state: str, module: AnsibleModule):
        """
        Map the web UI exclusion mode names to API names

        :param mode: The mode which should be set for the exclusion
        :type mode: str
        :param os_type: The os for which the exclusion will be created
        :type os_type: str
        :param state: Present or absent
        :type state: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API mapping of the exclusion mode
        :rtype: str
        """

        if mode == "suppress_alerts":
            return "suppress"
        elif mode == "interoperability" and os_type == "windows":
            return "disable_in_process_monitor"
        elif mode == "interoperability_extended" and os_type == "windows":
            return "disable_in_process_monitor_deep"
        elif mode == "performance_focus":
            return "disable_all_monitors"
        elif mode == "performance_focus_extended":
            return "disable_all_monitors_deep"
        elif state == "present":
            module.fail_json(msg=f"The mode {mode} is not compatible with os {os_type}")

    @staticmethod
    def get_path_exclusion_type(include_subfolders: bool, exclusion_path: str):
        """
        Set path exclusion type. If trailing slash or backslash is present path is handled as a folder. Here you can
        optionally enable recursive exclusion with include_subfolders. If trailing slash or backslash is not present it
        is automatically handeled as file type exclusion

        :param include_subfolders: True if exclusion should match subfolders. False if not
        :type include_subfolders: bool
        :param exclusion_path: Path wich should be excluded
        :type exclusion_path: str
        :return: API mapping for the exclusion type
        :rtype: str
        """

        # Get path type (folder or file)
        if re.search(r"[/\\]$", exclusion_path) and not include_subfolders:
            path_exclusion_type = "folder"
        elif re.search(r"[/\\]$", exclusion_path) and include_subfolders:
            path_exclusion_type = "subfolders"
        else:
            path_exclusion_type = "file"

        return path_exclusion_type

    @staticmethod
    def get_actions(ef_alerts_mitigation: bool, ef_binary_vault: bool):
        """
        Set actions for Exclusion Function

        :param ef_alerts_mitigation: Enable or disable exclusion for alerts and mitigation
        :type ef_alerts_mitigation:  bool
        :param ef_binary_vault: Enable or disable Binary Vault uploads
        :type ef_binary_vault: bool
        :return: API mapping for exclusion functions
        :rtype: list
        """

        actions = []
        if ef_alerts_mitigation:
            actions.append("detect")
        if ef_binary_vault:
            actions.append("upload")

        return actions

    def get_desired_state_exclusion_body(self):
        """
        Create API object

        :return: API body for create request
        :rtype: dict
        """
        desired_state_exclusion = {
            "filter": {
                "siteIds": [self.site_id]
            },
            "data": {
                "type": "path",
                "value": self.exclusion_path,
                "mode": self.mode_name,
                "source": "user",
                "pathExclusionType": self.path_exclusion_type,
                "description": self.description,
                "actions": self.actions,
                "osType": self.os_type
            }
        }

        if self.current_group_ids_names:
            desired_state_exclusion["filter"]["groupIds"] = self.current_group_ids

        return desired_state_exclusion

    @staticmethod
    def get_delete_exclusion_body(current_exclusion_ids: list):
        """
        Delete API object

        :param current_exclusion_ids: Ids of the exclsions which schould be deleted
        :type current_exclusion_ids: list
        :return: API body for delete request
        :rtype: dict
        """

        delete_body = {
            "data": {
                "ids": current_exclusion_ids,
                "type": "path"
            }
        }

        return delete_body

    def get_current_exclusions(self, current_group_ids: list, exclusion_path: str, module: AnsibleModule):
        """
        Get currently existing exclusion objects from API. If in group scope it returns the exclusion object for every
        group where the exclusion exists

        :param current_group_ids: Group ids of the groups where the exclusion should exist
        :type current_group_ids: list
        :param exclusion_path: path which should be excluded
        :type exclusion_path: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response with exclusion objects if existing
        :rtype: dict
        """

        api_url = self.api_endpoint_exclusions + (f"?siteIds={quote_plus(self.site_id)}&"
                                                  f"value={quote_plus(exclusion_path)}&type=path")
        if current_group_ids:
            # Scope is group level
            api_url += f"&groupIds={quote_plus(','.join(current_group_ids))}"

        error_msg = "Failed to get current exclusions."
        response = self.api_call(module, api_url, error_msg=error_msg)

        return response

    def delete_exclusions(self, module: AnsibleModule):
        """
        Delete existing exclusions

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response of the delete query
        :rtype: dict
        """

        if self.current_exclusion_ids:
            api_url = self.api_endpoint_exclusions
            delete_body = self.get_delete_exclusion_body(self.current_exclusion_ids)
            error_msg = "Failed to delete exclusions."
            response = self.api_call(module, api_url, "DELETE", body=delete_body, error_msg=error_msg)

            if response['data']['affected'] == 0:
                module.fail_json(msg="Exclusions should have been deleted via API but API result was empty")
        else:
            response = "Nothing to delete"

        return response

    def create_exclusions(self, module: AnsibleModule):
        """
        Create exclusions

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response of the create query
        :rtype: dict
        """
        api_url = self.api_endpoint_exclusions
        create_body = self.get_desired_state_exclusion_body()
        error_msg = "Failed to create exclusions."
        response = self.api_call(module, api_url, "POST", body=create_body, error_msg=error_msg)

        if len(response['data']) == 0:
            module.fail_json(msg="Exclusions should have been deleted via API but API result was empty")

        return response

    @staticmethod
    def check_sanity(ef_alerts_mitigation: bool, ef_binary_vault: bool, module: AnsibleModule):
        """
        Check if the passed module arguments are contradicting each other

        :param ef_alerts_mitigation: Enable or disable exclusion for alerts and mitigation
        :type ef_alerts_mitigation: bool
        :param ef_binary_vault: Enable or disable Binary Vault uploads
        :type ef_binary_vault: bool
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        """

        # Check if at least one of ef_alerts_mitigation and ef_binary_vault is true
        if not ef_alerts_mitigation and not ef_binary_vault:
            module.fail_json(msg="One of the following options needs to be true: ef_alerts_mitigation, ef_binary_vault")


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        site_name=dict(type='str', required=True),
        groups=dict(type='list', required=False, elements='str', default=[]),
        os_type=dict(type='str', required=False, choices=['windows', 'linux']),
        os_path=dict(type='str', required=True),
        include_subfolders=dict(type='bool', required=False, default=False),
        ef_alerts_mitigation=dict(type='bool', required=False, default=True),
        ef_binary_vault=dict(type='bool', required=False, default=False),
        mode=dict(type='str', required=False, choices=[
            'suppress_alerts',
            'interoperability',
            'interoperability_extended',
            'performance_focus',
            'performance_focus_extended'
        ]),
        description=dict(type='str', required=False, default=""),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ('mode', 'os_type'))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"),
                         exception=lib_imp_errors['lib_imp_err'])

    # Create exclusion Object
    exclusion_obj = SentineloneExclusions(module)

    current_exclusions = exclusion_obj.current_exclusions
    desired_state_exclusion = exclusion_obj.desired_state_exclusion
    # Groups where the exclusion currently exists
    current_group_ids_names = exclusion_obj.current_group_ids_names

    state = exclusion_obj.state

    diffs = []
    basic_message = []
    if state == 'present':
        if current_group_ids_names:
            # desired_exclusions_count is the count of the currently existing groups because we want the exlusion to
            # exist in every group
            desired_exclusions_count = len(current_group_ids_names)
            # current_exclusions_count is the count of the currently existing exclusions
            current_exclusions_count = current_exclusions['pagination']['totalItems']
            # if scope is group level
            if desired_exclusions_count == current_exclusions_count:
                # All exclusions exist. Check if they differ from desired state
                for current_exclusion in current_exclusions["data"]:
                    diff = exclusion_obj.merge_compare(current_exclusion, desired_state_exclusion['data'])[0]
                    if diff:
                        group_id = current_exclusion['scope']['groupIds'][0]
                        # Get name for group with group_id
                        group_name = list(filter(lambda filterobj: filterobj[0] == group_id,
                                                 current_group_ids_names))[0][1]
                        diffs.append({'changes': dict(diff), 'groupId': group_id})
                        basic_message.append(f"Exclusion exists in group {group_name} but is not up-to-date. "
                                             f"Updating exclusion.")
            else:
                # Not all exclusions exists.
                message = "Exclusion is missing in a group. Creating exclusion."
                basic_message.append(message)
                diffs.append({'changes': message})
        else:
            # if scope is site level
            site_name = exclusion_obj.site_name
            if current_exclusions['pagination']['totalItems'] == 0:
                message = f'Exclusion is missing in site {site_name}. Creating exclusion.'
                basic_message.append(message)
                diffs.append({'changes': message})
            else:
                # Exclusion exits. Check if it differs from desired state.
                current_exclusion = current_exclusions['data'][0]
                diff = exclusion_obj.merge_compare(current_exclusion, desired_state_exclusion['data'])[0]
                if diff:
                    diffs.append({'changes': dict(diff), 'siteId': current_exclusion['scope']['siteIds']})
                    basic_message.append(f"Exclusion exists in site {site_name} but is not up-to-date. "
                                         f"Updating exclusion.")

        if diffs:
            # Delete Exclusions
            exclusion_obj.delete_exclusions(module)

            # Create Exclusions
            exclusion_obj.create_exclusions(module)

    else:
        if current_exclusions['pagination']['totalItems'] != 0:
            # Exclusions should be deleted
            exclusion_obj.delete_exclusions(module)
            diffs.append({'changes': 'Deleted all exclusions in Scope'})

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
