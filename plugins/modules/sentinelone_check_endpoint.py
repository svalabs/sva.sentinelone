#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Niklas Werker <niklas.werker@sva.de>
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
module: sentinelone_check_endpoints
short_description: "Check if SentinelOne Endpoints are registered"
version_added: "1.1.0"
description:
  - "This module is able to check, if an endpoint is registered in the SentinelOne Management Console"
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
  endpoints:
    description:
      - "List of Endpoint Names which should be checked"
    type: list
    elements: str
    required: true
  sites:
    description:
      - "Sites the given endpoints should be part of"
    type: list
    elements: str
    required: false
  active:
    description:
      - "Whether or not the endpoint is in status active or not"
    type: bool
    required: false
    default: true
  unique:
    description:
      - "Whether or not the endpoint is expected to be unique"
    type: bool
    required: false
    default: false
  additional_fields:
    description:
      - "Additional API filter options you want to set. Available options can be referred in API documentation"
      - "e.g. computerName__contains or osTypes"
    type: dict
    required: false
    default: {}
author:
  - "Niklas Werker (@nwerker) <niklas.werker@sva.de>"
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


class SentineloneEndpoint(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the endpoint object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.endpoint = module.params["endpoint"]
        self.desired_state_filter_fields = module.params["filter_fields"]

        self.current_filter = self.get_current_filter(self.filter_name, module)
        self.current_filter_id = self.current_filter.get('id', '')

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        endpoints=dict(type='list', required=True, elements='str'),
        sites=dict(type='list', required=False, elements='str'),
        active=dict(type='bool', required=False),
        unique=dict(type='bool', required=False),
        additional_fields=dict(type='dict', required=False, elements='str')
    )

module = AnsibleModule(
        argument_spec=module_args,
        #required_if=[
        #    ('state', 'present', ('filter_fields',))
        #],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"),
                         exception=lib_imp_errors['lib_imp_err'])

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
