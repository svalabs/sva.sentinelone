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
module: sentinelone_filters
short_description: "Manage SentinelOne Filters"
version_added: "1.0.0"
description:
  - "This module is able to create, update and delete filters in SentinelOne"
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
      - "Select the I(state) of the filter"
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
      - "The name of the filter"
    type: str
    required: true
  filter_fields:
    description:
      - "Set the filter options you want to set. Available options can be referred in API documentation"
      - "e.g. computerName__contains or osTypes"
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
  - "Currently not applicable for account level filters"
'''

EXAMPLES = r'''
---
- name: Create filter
  sentinelone_filters:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyFilter"
    filter_fields:
      computerName__contains: "MyComputerName"
      osTypes:
        - windows
- name: Update filter
  sentinelone_filters:
    state: "present"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyFilter"
    filter_fields:
      computerName__contains:
        - MyComputerName
        - MyOtherComputerName
      osTypes:
        - windows
- name: Delete filter
  sentinelone_filters:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    name: "MyFilter"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: {"changes": {"iterable_item_added": {"root['computerName__contains'][1]": "test123"}}, "siteName": "msd"}
message:
    description: Get basic infos about the changes made
    type: str
    returned: on success
    sample: Filter is missing in site. Adding filter.
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors


class SentineloneFilter(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the filter object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.filter_name = module.params["name"]
        self.desired_state_filter_fields = module.params["filter_fields"]

        self.current_filter = self.get_current_filter(self.filter_name, module)
        self.current_filter_id = self.current_filter.get('id', '')

    def get_update_body(self):
        """
        Create body for update filter API request

        :return: Body for update filter API request
        :rtype: dict
        """

        desired_state_filter_body = {
            "data": {
                "filterFields": self.desired_state_filter_fields,
                "name": self.filter_name
            }
        }

        return desired_state_filter_body

    def get_create_body(self):
        """
        Create body for create filter API request

        :return: Body for create filter API request
        :rtype: dict
        """

        desired_state_filter_body = {
            "filter": {
                "siteIds": [self.site_id]
            },
            "data": {
                "filterFields": self.desired_state_filter_fields,
                "scopeLevel": "site",
                "siteId": self.site_id,
                "name": self.filter_name
            }
        }

        return desired_state_filter_body

    def create_filter(self, module: AnsibleModule):
        """
        API call to create the filter

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        api_url = self.api_endpoint_filters
        create_body = self.get_create_body()
        error_msg = "Failed to create filter."
        response = self.api_call(module, api_url, "POST", body=create_body, error_msg=error_msg)

        if not response['data']:
            module.fail_json(msg=("Error in create_filter: filter should have been created via API "
                                  "but API result was empty"))

        return response

    def delete_filter(self, module: AnsibleModule):
        """
        API call to delete the filter

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_filters}/{self.current_filter_id}"
        error_msg = "Failed to delete filter."
        response = self.api_call(module, api_url, "DELETE", error_msg=error_msg)

        if not response['data']['success']:
            module.fail_json(msg=("Error in delete_filter: Filter should have been deleted via API "
                                  "but API result was not 'success'"))

        return response

    def update_filter(self, module: AnsibleModule):
        """
        API call to update the filter

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_filters}/{self.current_filter_id}"
        update_body = self.get_update_body()
        error_msg = "Failed to update filter."
        response = self.api_call(module, api_url, "PUT", body=update_body, error_msg=error_msg)

        if not response['data']:
            module.fail_json(msg=("Error in update_filter: Filter should have been updated via API "
                                  "but API result was empty"))

        return response


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        site_name=dict(type='str', required=True),
        name=dict(type='str', required=True),
        filter_fields=dict(type='dict', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ('filter_fields',))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create filter Object
    filter_obj = SentineloneFilter(module)

    current_filter = filter_obj.current_filter
    desired_state_filter_fields = filter_obj.desired_state_filter_fields
    site_name = filter_obj.site_name
    state = filter_obj.state

    diffs = ''
    basic_message = ''
    if state == 'present':
        if current_filter:
            # If filter exists, check if it is up-to-date
            current_filter_fields = current_filter['filterFields']
            diff = filter_obj.merge_compare(current_filter_fields, desired_state_filter_fields)[0]
            if diff:
                # Update filter if it is not up-to-date
                diffs = {'changes': dict(diff), 'siteName': site_name}
                basic_message = f'Filter exists in site {site_name} but is not up-to-date. Updating Filter.'
                filter_obj.update_filter(module)
        else:
            # Creates the filter if it is missing
            basic_message = f'Filter is missing in site {site_name}. Adding filter'
            diffs = {'changes': basic_message}
            filter_obj.create_filter(module)

    else:
        # Filter should be deleted
        if current_filter:
            # Check if it exists
            basic_message = f'Filter exists in site {site_name}. Deleting filter'
            diffs = {'changes': basic_message}
            filter_obj.delete_filter(module)

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
