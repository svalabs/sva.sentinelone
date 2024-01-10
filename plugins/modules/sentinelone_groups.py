#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marco Wester <marco.wester@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: sentinelone_groups
short_description: "Manage SentinelOne Groups"
version_added: "1.0.0"
description:
  - "This module is able to create, update and delete static and dynamic groups in SentinelOne"
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
      - "Select the I(state) of the group"
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
  name:
    description:
      - "Name of the group or groups to create. You can pass multiple groups as a list"
    type: list
    elements: str
    required: true
  filter_name:
    description:
      - "If set this module creates a dynamic group based on the passed filter_name. If not set a static group is created"
      - "Can only be used if you create a single group."
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
  - "Can not convert from static to dynamic group or vice versa"
  - "Always inherits policy from site level. To change the policy please use the sentinelone_policy module."
'''

EXAMPLES = r'''
---
- name: Create single static group
  sentinelone_groups:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyGroup"

- name: Create single dynamic group
  sentinelone_groups:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyGroup"
    filter_name: "MyFilter"

- name: Create multiple static groups
  sentinelone_groups:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name:
      - "MyGroup1"
      - "MyGroup2"
      - "MyGroup3"

- name: Delete single static/dynamic group
  sentinelone_groups:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyGroup"

- name: Delete multiple static/dynamic groups
  sentinelone_groups:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name:
      - "MyGroup1"
      - "MyGroup2"
      - "MyGroup3"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: [{"changes": {"values_changed": {"root['filterId']":
    {"new_value": "999999999999999999", "old_value": "888888888888888888"}}}, "groupName": "test123"}]
message:
    description: Get basic infos about the changes made
    type: list
    returned: on success
    sample: ["Group test123 created."]
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors
from ansible.module_utils.six.moves.urllib.parse import quote_plus


class SentineloneGroups(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the groups object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.group_names = module.params["name"]
        self.filter_name = module.params["filter_name"]

        # Do sanity checks
        self.check_sanity(self.state, self.group_names, self.filter_name, module)

        self.current_groups = self.get_groups(self.group_names, module)
        if self.filter_name:
            # check if given filter for dynamic group exists
            self.filter_obj = self.get_current_filter(self.filter_name, module)
            if not self.filter_obj:
                module.fail_json(msg=f"Error: Filter {self.filter_name} does not exist.")
            self.filter_id = self.filter_obj['id']

    def get_groups(self, group_names: list, module: AnsibleModule):
        """
        API call to get the existing group objects

        :param group_names: name of the groups to get
        :type group_names: list
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: List of group objects
        :rtype: list
        """

        current_groups = []
        for group_name in group_names:
            api_url = self.api_endpoint_groups + (f"?siteIds={self.site_id}&"
                                                  f"name={quote_plus(group_name)}")
            error_msg = f"Failed to query group {group_name} from API"
            response = self.api_call(module, api_url, error_msg=error_msg)

            if response['pagination']['totalItems'] > 0:
                current_groups.append(response['data'][0])

        return current_groups

    def get_desired_state_group_body(self, group_name: str):
        """
        Create body

        :param group_name: Name of the group
        :type group_name: str
        :return: Group body object
        :rtype: dict
        """
        desired_state_groups = {
            "data": {
                "inherits": True,
                "siteId": self.site_id,
                "name": group_name
            }
        }

        if self.filter_name:
            # if we are creating a dynamic group add the filter id to body
            desired_state_groups['data']['filterId'] = self.filter_id

        return desired_state_groups

    def create_group(self, create_body: dict, error_msg: str, module: AnsibleModule):
        """
        API call to create a group

        :param create_body: Body for the create query
        :type create_body: dict
        :param error_msg: Message used if an API request failes
        :type error_msg: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: create query response object
        :rtype: dict
        """

        api_url = self.api_endpoint_groups
        response = self.api_call(module, api_url, "POST", body=create_body, error_msg=error_msg)

        if response['data']['name'] != create_body['data']['name']:
            module.fail_json(msg=(f"Group {create_body['data']['name']} should be created via API but "
                                  f"result was empty"))

        return response

    def update_group(self, update_body: dict, groupid: str, error_msg: str, module: AnsibleModule):
        """
        API call to update a group

        :param update_body: Body for the update query
        :type update_body: dict
        :param groupid: ID of the group which should be updated
        :type groupid: str
        :param error_msg: Message used if an API request failes
        :type error_msg: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response of the update query
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_groups}/{groupid}"
        response = self.api_call(module, api_url, "PUT", body=update_body, error_msg=error_msg)

        if response['data']['name'] != update_body['data']['name']:
            module.fail_json(msg=(f"Group {update_body['data']['name']} should have been updated via API"
                                  f"but API result was empty"))

        return response

    def delete_group(self, group_id: str, error_msg: str, module: AnsibleModule):
        """
        API call to delete a group

        :param group_id: ID of the group which should be deleted
        :type group_id: str
        :type error_msg: Message used if an API request failes
        :type error_msg: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response of the delete-query
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_groups}/{group_id}"
        response = self.api_call(module, api_url, "DELETE", error_msg=error_msg)

        if not response['data']['success']:
            module.fail_json(msg="Group should have been deleted via API but API result was empty")

        return response

    @staticmethod
    def check_sanity(state: str, group_names: list, filter_name: str, module: AnsibleModule):
        """
        Check if the passed module arguments are contradicting each other

        :param state: Present or absent
        :type state: str
        :param group_names: List of the group names which should be created or deleted
        :type group_names: list
        :param filter_name: Name of the optional filter for creating a dynamic group
        :type filter_name: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        """

        if state == 'present' and len(group_names) > 1 and filter_name:
            module.fail_json(msg=("Error: You passed multiple groups to the module while creating a dynamic group. "
                                  "Please either remove filter_name or pass only one group."))


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        site_name=dict(type='str', required=True),
        name=dict(type='list', required=True, elements='str'),
        filter_name=dict(type='str', required=False, default=""),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create exclusion Object
    groups_obj = SentineloneGroups(module)

    # List with all found groups.
    current_groups = groups_obj.current_groups
    group_names = groups_obj.group_names
    state = groups_obj.state

    diffs = []
    basic_message = []

    if state == 'present':
        for group_name in group_names:
            # Check if group exists
            desired_state_group = groups_obj.get_desired_state_group_body(group_name)
            current_group = list(filter(lambda filterobj: filterobj['name'] == group_name, current_groups))
            if current_group:
                # Group exists. Check if it differs from desired state, ignoring inhertiance property.
                diff = groups_obj.merge_compare(current_group[0], desired_state_group['data'], ["root['inherits']"])[0]
                # Check if diff exists and do not want to convert dynamic to static group and vice versa
                if diff:
                    if ((current_group[0]['type'] == 'dynamic' and module.params['filter_name']) or
                            (current_group[0]['type'] == 'static' and not module.params['filter_name'])):
                        group_id = current_group[0]['id']
                        # Inheritance and policy should not be maintained by this module.
                        # Removing the key because if not the module will update the inherintance property
                        del desired_state_group['data']['inherits']
                        error_msg = f"Failed to update group {group_name}."
                        groups_obj.update_group(desired_state_group, group_id, error_msg, module)
                        basic_message.append(f"Group {group_name} updated")
                        diffs.append({'changes': dict(diff), 'groupName': group_name})
                    else:
                        basic_message.append("Can not convert dynamic to static group and vice versa. Nothing changed.")
            else:
                # Group does not exist. Creating the group
                error_msg = f"Failed to create group {group_name}."
                groups_obj.create_group(desired_state_group, error_msg, module)
                basic_message.append(f"Group {group_name} created.")
                diffs.append({'changes': "Group created", 'groupName': group_name})
    else:
        # state is set to absent. Removing the group if exist
        for group_name in group_names:
            # check if group exits
            current_group = list(filter(lambda filterobj: filterobj['name'] == group_name, current_groups))
            if current_group:
                # if group exists delete it
                error_msg = f"Failed to delete group {group_name}."
                group_id = current_group[0]['id']
                groups_obj.delete_group(group_id, error_msg, module)
                basic_message.append(f"Group {group_name} deleted.")
                diffs.append({'changes': 'Group deleted', 'groupName': group_name})

    result = dict(
        changed=False,
        original_message=diffs,
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
