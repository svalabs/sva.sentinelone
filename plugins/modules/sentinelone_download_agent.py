#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marco Wester <marco.wester@sva.de>
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
module: sentinelone_download_agent
short_description: "Download SentinelOne agent from Management Console"
version_added: "1.1.0"
description:
  - "This module is able to download a SentinelOne agent from Management Console"
options:
  console_url:
    description:
      - "Insert your management console URL"
    type: str
    required: true
  site:
    description:
      - "Name of the site from which to download the agent"
      - "If omitted the scope will be on account level"
    type: str
    required: false
  token:
    description:
      - "SentinelOne API auth token to authenticate at the management API"
    type: str
    required: true
  state:
    description:
      - "Choose between download and print info of the agent packages"
    type: str
    default: present
    required: false
    choices:
      - present
      - info
  agent_version:
    description:
      - "Version of the agent to be downloaded."
      - "B(latest) (default) - download latest GA (stable) release for the specified parameters"
      - "B(latest_ea) - same as latest, but also includes EA packages"
      - "B(<explicit agent version number>) - download an explicit version of the agent"
    type: str
    default: latest
    required: false
    choices:
      - latest
      - latest_ea
      - custom
  custom_version:
    description:
      - "Explicit version of the file to be downloaded"
      - "Has to be set when agent_version=custom"
    type: str
    required: false
  os_type:
    description:
      - "The type of the OS for which the agent should be downloaded"
    type: str
    required: true
    choices:
      - Linux
      - Windows
  packet_format:
    description:
      - "The format of the packet which should be downloaded"
    type: str
    required: true
    choices:
      - rpm
      - deb
      - msi
      - exe
  architecture:
    description:
      - "Architecture of the packet which should be downloaded"
    type: str
    required: true
    choices:
      - 32_bit
      - 64_bit
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
  - "Erik Scihndler (@mintalicious) <erik.schindler@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
'''

EXAMPLES = r'''
---
- name: Create / update site
  sentinelone_sites:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    name: "test"
    license_type: "control"
    expiration_date: "2022-06-01T12:00+01:00"
    description: "Testsite"
- name: Delete site
  sentinelone_sites:
    state: "absent"
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    name: "test"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: {'changes': {'values_changed': {"root['description']": {'new_value': 'Test1', 'old_value': 'Test'},
      "root['unlimitedExpiration']": {'new_value': True, 'old_value': False}}}, 'siteName': 'test'}
message:
    description: Get basic infos about the changes made
    type: str
    returned: on success
    sample: Site exists but is not up-to-date. Updating site.
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors
from datetime import datetime, timezone


class SentineloneDownloadAgent(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the site object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        module.params['site_name'] = module.params['name']

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.site_type = module.params["site_type"]
        self.license_type = module.params["license_type"]
        self.total_agents = module.params["total_agents"]
        self.expiration_date = module.params["expiration_date"]
        self.description = module.params["description"]

        # Do sanity checks
        self.check_sanity(self.state, self.license_type, self.total_agents, self.expiration_date,
                          self.current_account, module)

    def desired_state_site_body(self):
        """
        Create body for site API requests

        :return: Body for site API requests
        :rtype: dict
        """

        desired_state_site_body = {
            "accountId": self.account_id,
            "siteType": self.site_type,
            "inherits": True,
            "name": self.site_name,
            "licenses": {
                "bundles": [
                    {
                        "name": self.license_type,
                        "surfaces": [
                            {
                                "name": "Total Agents",
                                "count": self.total_agents
                            }
                        ]
                    }
                ]
            }
        }

        if self.expiration_date == "-1":
            if self.current_account["unlimitedExpiration"]:
                desired_state_site_body["unlimitedExpiration"] = True
            else:
                desired_state_site_body["unlimitedExpiration"] = False
                desired_state_site_body["expiration"] = self.current_account["expiration"]
        else:
            desired_state_site_body["unlimitedExpiration"] = False
            desired_state_site_body["expiration"] = self.expiration_date

        if self.description:
            desired_state_site_body["description"] = self.description

        return desired_state_site_body

    def check_sanity(self, state: str, license_type: str, total_agents: int, expiration_date: str,
                     current_account: dict, module: AnsibleModule):
        """
        Check if the passed module arguments are contradicting each other


        :param state: The state parameter passed to the module
        :type state: str
        :param license_type: The license_type parameter passed to the module
        :type license_type: str
        :param total_agents: The total_agents parameter passed to the module
        :type total_agents: int
        :param expiration_date: The expiration_date parameter passed to the module
        :type expiration_date: str
        :param current_account: Account information
        :type current_account: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        """

        if state == 'present' and not (total_agents == -1 or total_agents > 0):
            module.fail_json(msg="Error: 'total_agents' has to be > 0 or -1.")

        if state == 'present' and not (expiration_date == '' or expiration_date == '-1'):
            try:
                offset = expiration_date[-5:].replace(':', '')
                expiration_date = expiration_date[:-5] + offset

                timeformat = "%Y-%m-%dT%H:%M%z"
                expiration_date_parsed = datetime.strptime(expiration_date, timeformat)
            except Exception as err:
                module.fail_json(msg=f"Error: 'expiration_date' could not be parsed as date. Error: {str(err)}")

            self.expiration_date = expiration_date_parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")

        elif state == 'present' and expiration_date == '':
            module.fail_json(msg="Error: 'expiration_date' has to be -1 or in date format")

        available_license_types = list(map(lambda lic: lic['name'], current_account['licenses']['bundles']))
        if state == 'present' and license_type not in available_license_types:
            module.fail_json(msg=f"Error: 'license_type' '{license_type}' not available in account. Available license "
                                 f"types are: {', '.join(available_license_types)}")


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        site=dict(type='str', required=False),
        token=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'info']),
        agent_version=dict(type='str', required=False, default='latest', choices=['latest', 'latest_ea', 'custom']),
        custom_version=dict(type='str', required=False),
        os_type=dict(type='str', required=True, choices=['Linux', 'Windows']),
        packet_format=dict(type='str', required=True, choices=['rpm', 'deb', 'msi', 'exe']),
        architecture=dict(type='str', required=True, choices=['32_bit', '64_bit']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"),
                         exception=lib_imp_errors['lib_imp_err'])

    # Create site Object
    site_obj = SentineloneSite(module)

    site_name = site_obj.site_name
    site_id = site_obj.site_id
    state = site_obj.state

    diffs = ''
    basic_message = ''
    if state == 'present':
        desired_state_site = site_obj.desired_state_site_body()
        if site_id is not None:
            # If site exists, check if it is up-to-date
            current_site = site_obj.current_site
            # Set ignore keys for merge_compare. These settings are not relevant
            exclude_path = [
                "root['inherits']", "root['licenses']['bundles'][0]['displayName']",
                "root['licenses']['bundles'][0]['majorVersion']", "root['licenses']['bundles'][0]['minorVersion']",
                "root['licenses']['bundles'][0]['totalSurfaces']"
            ]
            diff = site_obj.merge_compare(current_site, desired_state_site, exclude_path)[0]
            if diff:
                # Update site if it is not up-to-date
                diffs = {'changes': dict(diff), 'siteName': site_name}
                basic_message = 'Site exists but is not up-to-date. Updating site.'
                site_obj.update_site(desired_state_site, module)
        else:
            # Creates the site if it is missing
            basic_message = f'Site is missing. Adding site {site_name}'
            diffs = {'changes': basic_message}
            site_obj.create_site(desired_state_site, module)
    else:
        # Site should be deleted
        if site_id is not None:
            # Check if site exists
            basic_message = f'Site {site_name} exists. Deleting site'
            diffs = {'changes': basic_message}
            site_obj.delete_site(module)

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
