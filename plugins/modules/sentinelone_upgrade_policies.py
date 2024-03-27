#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marco Wester <marco.wester@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: sentinelone_upgrade_policies
short_description: "Manage SentinelOne Upgrade Policies"
version_added: "1.0.0"
description:
  - "This module is able to update 'Upgrade Policies' in SentinelOne"
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
  inherit_maintenance_windows:
    description:
      - "Inherit 'Maintenance Windows Settings' from upper scope"
      - "If I(inherit_maintenance_windows=yes) I(maintenance_windows) will be ignored and the settings will be inherited from upper scope"
    type: bool
    default: no
    required: false
  inherit_max_concurrent_downloads:
    description:
      - "Inherit 'Maximum Concurrent Downloads' from upper scope"
      - "If I(inherit_max_concurrent_downloads=yes) I(max_concurrent_downloads) will be ignored and "
      - "the settings will be inherited from upper scope"
    type: bool
    default: false
    required: false
  site_name:
    description:
      - "Name of the site in SentinelOne"
    type: str
    required: true
  groups:
    description:
      - "Set this option to set the scope to group level"
      - "A list with groupnames where the upgrade policy should be changed"
    type: list
    elements: str
    default: []
    required: false
  maintenance_windows:
    description:
      - "Define the settings which should be set in policy. Available options can be referred in API documentation"
      - "Usage see examples section"
      - "Required if I(inherit_maintenance_windows=no)"
      - "Will be ignored if I(inherit_maintenance_windows=yes)"
    type: dict
    required: false
  max_concurrent_downloads:
    description:
      - "Set the 'Maximum Concurrent Downloads'. Needs to be lower or equal to the value set in the upper scope"
      - "Required if I(inherit_max_concurrent_downloads=no)"
      - "Will be ignored if I(inherit_max_concurrent_downloads=yes)"
    type: int
    required: false
  timezone:
    description:
      - "Set the timezone"
      - "Example value: +01:00"
    type: str
    required: false
    default: "+00:00"
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
  - "Currently not applicable for account level upgrade policies"
'''

EXAMPLES = r'''
- name: Set custom 'Maximum Concurrent Downloads' on multiple groups
  sva.sentinelone.sentinelone_upgrade_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - group1
      - group2
    max_concurrent_downloads: 1000
- name: Enable inheritance for 'Maximum Concurrent Downloads' and for 'Maintenance Windows Settings' on site scope
  sva.sentinelone.sentinelone_upgrade_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    inherit_max_concurrent_downloads: yes
    inherit_maintenance_windows: yes
- name: Set custom 'Maintenance Windows' for monday and tuesday on single group
  sva.sentinelone.sentinelone_upgrade_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - group1
    inherit_max_concurrent_downloads: yes
    inherit_maintenance_windows: no
    maintenance_windows:
        monday:
            - from: "8:00 am"
              to: "11:00 pm"
        tuesday:
            - from: "8:00 am"
              to: "12:00 pm"
            - from: "3:00 pm"
              to: "7:00 pm"
- name: Set custom 'Maintenance Windows' for monday on single group and use specific timezone
  sva.sentinelone.sentinelone_upgrade_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    groups:
      - group1
    inherit_max_concurrent_downloads: yes
    inherit_maintenance_windows: no
    maintenance_windows:
        monday:
            - from: "8:00 am"
              to: "11:00 pm"
    timezone: "+02:00"
- name: Set custom 'Maintenance Windows' for whole wednesday on site scope
  sva.sentinelone.sentinelone_upgrade_policies:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    site_name: "test"
    inherit_max_concurrent_downloads: yes
    inherit_maintenance_windows: no
    maintenance_windows:
        wednesday:
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the changes made
    type: str
    returned: on success
    sample: [{'changes': {'dictionary_item_removed': ["root['data']['maintenanceWindowsByDay']['Friday']",
      "root['data']['maintenanceWindowsByDay']['Saturday']", "root['data']['maintenanceWindowsByDay']['Sunday']",
      "root['data']['maintenanceWindowsByDay']['Thursday']"], 'values_changed':
      {"root['data']['inheritParentMaintenanceConfig']": {'new_value': False, 'old_value': True},
      "root['data']['maintenanceWindowsByDay']['Monday']['isMaintenanceAllDay']": {'new_value': False, 'old_value': True},
      "root['data']['maintenanceWindowsByDay']['Tuesday']['isMaintenanceAllDay']": {'new_value': False, 'old_value': True}},
      'iterable_item_added': {"root['data']['maintenanceWindowsByDay']['Monday']['maintenanceHours'][0]":
      {'fromTime': '8:00 am', 'toTime': '11:00 pm'},
      "root['data']['maintenanceWindowsByDay']['Tuesday']['maintenanceHours'][0]": {'fromTime': '8:00 am',
      'toTime': '12:00 pm'}, "root['data']['maintenanceWindowsByDay']['Tuesday']['maintenanceHours'][1]":
      {'fromTime': '3:00 pm', 'toTime': '7:00 pm'}}}, 'SiteId': '9999999999999999999'}]
message:
    description: Get basic infos about the changes made
    type: list
    returned: on success
    sample: ["Updating upgrade policy for group group1", "Updating upgrade policy for group group2"]
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase, lib_imp_errors
from datetime import datetime


class SentineloneUpgradePolicies(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the upgrade policies object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # super class __init__ expects "state" to be present. Workaround here
        module.params["state"] = None

        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        # Translating "state" back to "inherit_maintenance_windows"
        self.inherit_maintenance_windows = module.params["inherit_maintenance_windows"]
        self.inherit_max_concurrent_downloads = module.params["inherit_max_concurrent_downloads"]
        self.desired_state_maintenance_windows = module.params["maintenance_windows"]
        self.desired_state_max_concurrent_downloads = module.params["max_concurrent_downloads"]
        self.desired_state_timezone = module.params["timezone"]

        # Do sanity checks
        self.check_sanity(self.inherit_maintenance_windows, self.desired_state_timezone,
                          self.desired_state_maintenance_windows, module)

    def get_current_upgrade_policy(self, site_group_id: str, module: AnsibleModule):
        """
        Get the upgrade policy which is currently set from API. Can be used on site or group scope

        :param site_group_id: Site or group id
        :type site_group_id: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Upgrade Policy object
        :rtype: dict
        """

        site_id = self.site_id

        # Build API call to get the upgrade policy which is currently set. Can be used on site or group level
        query_options = ["taskType=agents_upgrade"]
        if self.current_group_ids_names:
            query_options.append(f"groupIds={site_group_id}")
        else:
            query_options.append(f"siteIds={site_id}")

        query_uri = '&'.join(query_options)
        api_url = f"{self.api_endpoint_upgrade_policy}?{query_uri}"

        error_msg = f"Failed to get current upgrade policy for site or group with id {site_group_id}."
        response = self.api_call(module, api_url, error_msg=error_msg)

        return response

    def update_upgrade_policy(self, site_group_id: str, update_body: dict, module: AnsibleModule):
        """
        API call to update the upgrade policy. Can be used on site or group level

        :param site_group_id: Site or group id
        :type site_group_id: str
        :param update_body: Dictionary object which is used for updating the existing upgrade policy object
        :type update_body: dict
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: API response
        :rtype: dict
        """

        api_url = self.api_endpoint_upgrade_policy

        error_msg = f"Failed to update the upgrade policy with site or group id {site_group_id}."
        response = self.api_call(module, api_url, "PUT", body=update_body, error_msg=error_msg)

        if not response['data']:
            module.fail_json(msg=(f"Error in update_upgrade_policy with site or group id {site_group_id}: "
                                  f"Upgrade policy should have been updated via API but result was empty"))

        return response

    def get_desired_state_upgrade_policy(self, parent_max_concurrent_downloads: int):
        """
        Generate desired state upgrade policy object

        :param parent_max_concurrent_downloads: maximum concurrent downloads value of upper scope
        :type parent_max_concurrent_downloads: int
        :return: desired state upgrade policy object
        :rtype: dict
        """
        desired_state_upgrade_policy = {
            "data": {
                "inheritParentConcurrencyConfig": self.inherit_max_concurrent_downloads,
                "inheritParentMaintenanceConfig": self.inherit_maintenance_windows,
                "timezoneGmt": f"GMT{self.desired_state_timezone}"
            }
        }
        if self.inherit_max_concurrent_downloads:
            # API needs maxConcurrent to be set even if inheritance is enabled. So settings this to the upper scopes
            # value seems meaningful
            desired_state_upgrade_policy["data"]["maxConcurrent"] = parent_max_concurrent_downloads
        else:
            desired_state_upgrade_policy["data"]["maxConcurrent"] = self.desired_state_max_concurrent_downloads

        maintenance_days = {}
        if not self.inherit_maintenance_windows:
            # Make dictionary keys lower-case
            desired_state_maintenance_windows_lk = {k.lower(): v for k, v in
                                                    self.desired_state_maintenance_windows.items()}
            desired_state_maintenance_windows = {
                "Monday": desired_state_maintenance_windows_lk.get("monday", False),
                "Tuesday": desired_state_maintenance_windows_lk.get("tuesday", False),
                "Wednesday": desired_state_maintenance_windows_lk.get("wednesday", False),
                "Thursday": desired_state_maintenance_windows_lk.get("thursday", False),
                "Friday": desired_state_maintenance_windows_lk.get("friday", False),
                "Saturday": desired_state_maintenance_windows_lk.get("saturday", False),
                "Sunday": desired_state_maintenance_windows_lk.get("sunday", False)
            }
            for day, config in desired_state_maintenance_windows.items():
                # If config is a list and not empty then set the time ranges
                if isinstance(config, list) and config:
                    maintenance_days[day] = {
                        "isMaintenanceAllDay": False,
                        "maintenanceHours": []
                    }
                    for timerange in config:
                        time_from = timerange['from']
                        time_to = timerange['to']
                        maintenance_days[day]["maintenanceHours"].append(
                            {
                                "fromTime": time_from.lstrip("0"),
                                "toTime": time_to.lstrip("0")
                            }
                        )
                # If parameters are parsed from Yaml and no vaule for day is explicity set it is parsed as None Type.
                # We also accept empty lists as input. But boolean types are set by this script to False. This is
                # necessary to differ if day was passed by user (empty list or None Type) or if it was set to
                # False (boolean) by this script. If passed by User we want to set "isMaintenanceAllDay" to True.
                # If it was set to false by this script we want to do nothing.
                elif (isinstance(config, list) and not config) or config is None:
                    maintenance_days[day] = {
                        "isMaintenanceAllDay": True,
                        "maintenanceHours": []
                    }
        desired_state_upgrade_policy['data']['maintenanceWindowsByDay'] = maintenance_days

        return desired_state_upgrade_policy

    def get_update_body(self, desired_state_upgrade_policy: dict, site_group_id: int):
        """
        Create post object. Adding additional keys to the object.

        :param desired_state_upgrade_policy: upgrade policy which should be set
        :type desired_state_upgrade_policy: dict
        :param site_group_id: Site_id or group_id. Depends on the scope
        :type site_group_id: int
        :return: Body which can be used with API
        :rtype: dict
        """
        desired_state_upgrade_policy['filter'] = {'taskType': 'agents_upgrade'}

        if self.current_group_ids_names:
            desired_state_upgrade_policy['filter']['groupIds'] = [site_group_id]
        else:
            desired_state_upgrade_policy['filter']['siteIds'] = [site_group_id]

        return desired_state_upgrade_policy

    def check_max_concurrent_downloads_size(self, current_upgrade_policy: dict, inherit_max_concurrent_downloads: bool,
                                            module: AnsibleModule):
        """
        Check if desired state max concurrent downloads value is lower than upper scopes max concurrent downloads value

        :param current_upgrade_policy: Upgrade policy which is currently set
        :type current_upgrade_policy: dict
        :param inherit_max_concurrent_downloads: Should the maximum concurrent downloads be inherited from upper scope
        :type inherit_max_concurrent_downloads: bool
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Parent max concurrent downloads is returned
        :rtype: int
        """
        parent_max_concurrent_downloads = current_upgrade_policy['data']['parentMaxConcurrent']
        if not inherit_max_concurrent_downloads:
            if parent_max_concurrent_downloads < self.desired_state_max_concurrent_downloads:
                module.fail_json(msg="max_concurrent_downloads is higher than the upper scopes Maximum Concurrent "
                                     "Downloads value. Please use a value lower than or equal to "
                                     f"{parent_max_concurrent_downloads}")
            parent_max_concurrent_downloads = None

        return parent_max_concurrent_downloads

    @staticmethod
    def clean_current_upgrade_policy_object(upgrade_policy_object: dict):
        """
        Remove unnecessary keys from object for comparision with the desired state object

        :param upgrade_policy_object: object from which the keys should be removed
        :type upgrade_policy_object: dict
        """

        # Some items in current_upgrade_policy are not necessary to compare and these keys make the comparison unusable.
        # They are not available in the update the upgrade policy API endpoint and needs to be removed
        current_upgrade_policy_remove_items = ['concurrencyConfigUpdatedAt', 'concurrencyConfigUpdatedBy',
                                               'maintenanceConfigUpdatedAt', 'maintenanceConfigUpdatedBy',
                                               'parentMaxConcurrent', 'taskType']
        for key in current_upgrade_policy_remove_items:
            del upgrade_policy_object["data"][key]

    @staticmethod
    def check_sanity(inherit_maintenance_windows: bool, timezone: str, maintenance_windows: dict,
                     module: AnsibleModule):
        """
        Check if the passed module arguments are contradicting each other

        :param inherit_maintenance_windows: Should Maintenance Windows be inherited from upper scope
        :type inherit_maintenance_windows: bool
        :param timezone: The timezone passed to the module
        :type timezone: str
        :param maintenance_windows: The maintenance_windows passed by the module
        :type maintenance_windows: dict
        :param module: Ansible module for error handling
        :type module:AnsibleModule
        """

        valid_timezones = ["-11:00", "-10:00", "-09:30", "-09:00", "-08:00", "-07:00", "-06:00", "-05:00", "-04:00",
                           "-03:30", "-03:00", "-02:00", "-01:00", "+00:00", "+01:00", "+02:00", "+03:00", "+03:30",
                           "+04:00", "+04:30", "05:00", "+05:30", "+05:45", "+06:00", "+06:30", "+07:00", "+08:00",
                           "+08:45", "+09:00", "+09:30", "+10:00", "+10:30", "+11:00", "+12:00", "+13:00", "+13:45",
                           "+14:00"]

        if timezone not in valid_timezones:
            module.fail_json(msg="Timezone is invalid. Please choose one of the following values: "
                                 f"{' ,'.join(valid_timezones)}")

        if not inherit_maintenance_windows:
            for day, windows in maintenance_windows.items():
                # Check if maintenance windows are a list with content. Else skip check
                if isinstance(windows, list) and windows:
                    for window in windows:
                        # Check if correct data structure is present
                        if not isinstance(window, dict):
                            module.fail_json(msg=f"Please check the entered maintenance window time values for {day}. "
                                                 f"Maintenance window is no dict object. Expecting dict with "
                                                 f"'from:' and 'to'")

                        # Check if from and to is present. Negated check was necessarry because if condition also
                        # evaluates to true if from or to is filled
                        from_value = window.get("from", False)
                        to_value = window.get("to", False)
                        if not from_value or not to_value:
                            module.fail_json(msg=f"Please check the entered maintenance window time values for {day}. "
                                                 f"Expecting dict with 'from:' and 'to'. At least one is missing")

                        try:
                            # Check if entered time is valid
                            time1 = datetime.strptime(from_value, "%I:%M %p")
                            time2 = datetime.strptime(to_value, "%I:%M %p")
                        except ValueError as err:
                            module.fail_json(msg=f"Please check the entered maintenance window time values for {day}. "
                                             f"The entered time value is not valid. Exception is: {err}")

                        if time1 >= time2:
                            module.fail_json(msg=f"Please check the entered maintenance window time values for {day}. "
                                                 f"The 'from' value needs to be smaller than the 'to' value. "
                                                 f"Your values: 'from': {from_value}, 'to': {to_value}")


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        inherit_maintenance_windows=dict(type='bool', required=False, default=False),
        inherit_max_concurrent_downloads=dict(type='bool', required=False, default=False),
        site_name=dict(type='str', required=True),
        groups=dict(type='list', required=False, elements='str', default=[]),
        maintenance_windows=dict(type='dict', required=False),
        max_concurrent_downloads=dict(type='int', required=False),
        timezone=dict(type='str', required=False, default="+00:00"),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('inherit_maintenance_windows', False, ('maintenance_windows',)),
            ('inherit_max_concurrent_downloads', False, ('max_concurrent_downloads',))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create upgrade policy Object
    upgrade_policy_obj = SentineloneUpgradePolicies(module)
    current_group_ids_names = upgrade_policy_obj.current_group_ids_names
    inherit_maintenance_windows = upgrade_policy_obj.inherit_maintenance_windows
    inherit_max_concurrent_downloads = upgrade_policy_obj.inherit_max_concurrent_downloads

    # The API will give us 'maintenanceWindowsByDay' and 'maxConcurrent' even if inheritance is enabled. Therefore, we
    # need to ignore it. Otherwise, it will not be idempotent.
    exclude_path = []
    if inherit_maintenance_windows:
        exclude_path.append("root['data']['maintenanceWindowsByDay']")

    if inherit_max_concurrent_downloads:
        exclude_path.append("root['data']['maxConcurrent']")

    diffs = []
    basic_message = []
    # if we want to set custom Maintenance Windows
    if current_group_ids_names:
        # if scope is group level
        for current_group_id_name in current_group_ids_names:
            current_group_id = current_group_id_name[0]
            # check if every group has the desired settings already
            current_upgrade_policy = upgrade_policy_obj.get_current_upgrade_policy(current_group_id, module)

            parent_max_concurrent_downloads = upgrade_policy_obj.check_max_concurrent_downloads_size(
                current_upgrade_policy, inherit_max_concurrent_downloads, module)

            upgrade_policy_obj.clean_current_upgrade_policy_object(current_upgrade_policy)

            desired_state_upgrade_policy = upgrade_policy_obj.get_desired_state_upgrade_policy(
                parent_max_concurrent_downloads)

            diff = upgrade_policy_obj.compare(current_upgrade_policy, desired_state_upgrade_policy,
                                              exclude_path=exclude_path)
            if diff:
                # if upgrade policy is different from desired state, update it
                current_group_name = current_group_id_name[1]
                diffs.append({'changes': dict(diff), 'groupId': current_group_id})
                basic_message.append(f"Updating upgrade policy for group {current_group_name}")
                update_body = upgrade_policy_obj.get_update_body(desired_state_upgrade_policy, current_group_id)
                upgrade_policy_obj.update_upgrade_policy(current_group_id, update_body, module)
    else:
        # if scope is site level
        # check if site has the desired settings already
        site_name = upgrade_policy_obj.site_name
        site_id = upgrade_policy_obj.site_id
        current_upgrade_policy = upgrade_policy_obj.get_current_upgrade_policy(site_id, module)

        parent_max_concurrent_downloads = upgrade_policy_obj.check_max_concurrent_downloads_size(
            current_upgrade_policy, inherit_max_concurrent_downloads, module)

        upgrade_policy_obj.clean_current_upgrade_policy_object(current_upgrade_policy)

        desired_state_upgrade_policy = upgrade_policy_obj.get_desired_state_upgrade_policy(
            parent_max_concurrent_downloads)

        diff = upgrade_policy_obj.compare(current_upgrade_policy, desired_state_upgrade_policy,
                                          exclude_path=exclude_path)
        if diff:
            # if upgrade policy is different from desired state, update it
            diffs.append({'changes': dict(diff), 'SiteId': site_id})
            basic_message.append(f"Updating upgrade policy for site {site_name}")
            update_body = upgrade_policy_obj.get_update_body(desired_state_upgrade_policy, site_id)
            upgrade_policy_obj.update_upgrade_policy(site_id, update_body, module)

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
