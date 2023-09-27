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

from ansible.module_utils.basic import AnsibleModule
import json
import traceback
import copy
import time
from ansible.module_utils.six.moves.urllib.parse import quote_plus
import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.module_utils.urls import fetch_url

lib_imp_errors = {'lib_imp_err': None}
try:
    from deepdiff import DeepDiff
    lib_imp_errors['has_lib'] = True
except ImportError:
    lib_imp_errors['has_lib'] = False
    lib_imp_errors['lib_imp_err'] = traceback.format_exc()


class SentineloneBase:
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the base super class

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # Set URIs for API endpoints
        api_uri_groups = "/web/api/v2.1/groups"
        api_uri_filters = "/web/api/v2.1/filters"
        api_uri_exclusions = "/web/api/v2.1/exclusions"
        api_uri_sites = "/web/api/v2.1/sites"
        api_uri_accounts = "/web/api/v2.1/accounts"
        api_uri_config_overrides = "/web/api/v2.1/config-override"
        api_uri_upgrade_policy = "/web/api/v2.1/tasks-configuration"
        api_uri_update_agent_packages = "/web/api/v2.1/update/agent/packages"

        # Build full API endpoint from base console URL and API URI
        self.api_endpoint_groups = module.params["console_url"] + api_uri_groups
        self.api_endpoint_filters = module.params["console_url"] + api_uri_filters
        self.api_endpoint_exclusions = module.params["console_url"] + api_uri_exclusions
        self.api_endpoint_accounts = module.params["console_url"] + api_uri_accounts
        self.api_endpoint_sites = module.params["console_url"] + api_uri_sites
        self.api_endpoint_config_overrides = module.params["console_url"] + api_uri_config_overrides
        self.api_endpoint_upgrade_policy = module.params["console_url"] + api_uri_upgrade_policy
        self.api_endpoint_update_agent_packages = module.params["console_url"] + api_uri_update_agent_packages

        # Assign passed parameters to class variables
        self.token = module.params["token"]
        self.console_url = module.params["console_url"]
        self.site_name = module.params["site_name"]
        self.state = module.params["state"]
        self.group_names = module.params.get("groups", [])

        # Get AccountID by name
        self.current_account = self.get_account_obj(module)
        self.account_id = self.current_account["id"]

        # Get site object and extract SiteID
        self.current_site = self.get_site(self.site_name, module)
        if self.current_site is None:
            self.site_id = None
        else:
            self.site_id = self.current_site["id"]

        # Get GroupIDs by Name
        if self.group_names:
            self.current_group_ids_names = self.get_group_ids_names(self.group_names, module)
        else:
            self.current_group_ids_names = []

        self.module = module

    def api_call(self, module: AnsibleModule, api_endpoint: str, http_method: str = "get", **kwargs):
        """
        Queries api_endpoint. if no http_method is passed a get request is performed. api_endpoint is mandatory

        :param module:  Ansible module for error handling
        :type module: AnsibleModule
        :param api_endpoint: URL of the API endpoint to query
        :type api_endpoint: str
        :param http_method: HTTP query method. Default is GET but POST, PUT, DELETE, etc. is supported as well
        :type http_method: str
        :param kwargs: See below
        :Keyword Arguments:
            * *headers* (dict) --
              You can pass custom headers or custom body.
              If custom headers is not set default vaules will apply and should be sufficient.
            * *body* (dict) --
              If body is not passed body is empty
            * *error_msg* (str) --
              Start of error message in case of a failed API call
        :return: Returnes parsed json response. Type of return value depends on the data returned by the API.
            Usually dictionary
        :rtype: dict
        """

        request_timeout = 120
        retries = 3
        retry_pause = 3

        headers = {}

        if not kwargs.get("headers", {}):
            headers['Accept'] = 'application/json'
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = f'APIToken {self.token}'

        body = kwargs.get("body", {})

        error_msg = kwargs.get("error_msg", "API call failed.")

        retry_count = 0
        try:
            while True:
                retry_count += 1
                try:
                    if body:
                        body_json = json.dumps(body)
                        response_raw, response_info = fetch_url(module, api_endpoint, headers=headers, data=body_json,
                                                                method=http_method, timeout=request_timeout)
                    else:
                        response_raw, response_info = fetch_url(module, api_endpoint, headers=headers,
                                                                method=http_method, timeout=request_timeout)

                    status_code = response_info['status']
                    if status_code == -1:
                        # If the request runtime exceeds the timout
                        module.exit_json(msg=f"{error_msg} Error: {response_info['msg']} after {request_timeout}s.")
                    elif status_code >= 400:
                        response_unparsed = response_info['body'].decode('utf-8')
                        response = json.loads(response_unparsed)
                        raise response_raw
                    else:
                        response = json.loads(response_raw.read().decode('utf-8'))
                        break
                except Exception as err:
                    if retry_count == retries:
                        raise err

                time.sleep(retry_pause)
        except json.decoder.JSONDecodeError as err:
            module.fail_json(msg=f"API response is no valid JSON. Error: {str(err)}")
        except urllib_error.HTTPError as err:
            module.fail_json(
                msg=f"{error_msg} Status code: {err.code} {err.reason}. Error: {response_unparsed}")

        return response

    def get_account_obj(self, module: AnsibleModule):
        """
        Returns the account obj

        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Account obj as dict
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_accounts}?states=active"
        error_msg = "Failed to get account"
        response = self.api_call(module, api_url, error_msg=error_msg)

        if response["pagination"]["totalItems"] == 1:
            return response["data"][0]
        elif response["pagination"]["totalItems"] > 1:
            module.fail_json(msg="Multiple Accounts found. This module only works with single-account "
                                 "management consoles")
        else:
            module.fail_json(msg="No Accounts found. This error should never appear")

    def get_site(self, site_name: str, module: AnsibleModule):
        """
        Returns site object for given site_name

        :param site_name: Name of the site
        :type site_name: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Site object as dict
        :rtype: dict
        """

        if site_name is None:
            return None

        api_url = f"{self.api_endpoint_sites}?name={quote_plus(site_name)}&state=active"
        error_msg = "Failed to get site."
        response = self.api_call(module, api_url, error_msg=error_msg)

        if response["pagination"]["totalItems"] == 1:
            site_obj = response["data"]["sites"][0]
        elif self.__class__.__name__ == "SentineloneSite":
            return None
        else:
            module.fail_json(msg=f"Site {site_name} not found")
        return site_obj

    def get_group_ids_names(self, group_names: list, module: AnsibleModule):
        """
        Returns group_ids_names for given group_names

        :param group_names: One or more group names
        :type group_names: list
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: List with tuples of group_id and group_name
        :rtype: list
        """

        group_ids_names = []
        for group_name in group_names:
            api_url = f"{self.api_endpoint_groups}?name={quote_plus(group_name)}&siteIds={quote_plus(self.site_id)}"
            error_msg = f"Failed to get group {group_name}."
            response = self.api_call(module, api_url, error_msg=error_msg)

            if response["pagination"]["totalItems"] == 1:
                group_id = response["data"][0]["id"]
                group_ids_names.append((group_id, group_name))
            else:
                module.fail_json(msg=f"Group {group_name} not found")

        return group_ids_names

    def get_current_filter(self, filter_name: str, module: AnsibleModule):
        """
        Returns the filter object of filter_name

        :param filter_name: Filter name
        :type filter_name: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Filter object
        :rtype: dict
        """

        api_url = f"{self.api_endpoint_filters}?siteIds={self.site_id}&query={quote_plus(filter_name)}"
        error_msg = "Failed to get filters from API."
        response = self.api_call(module, api_url, error_msg=error_msg)

        # API parameter "query" also matches substring. Making sure only the exactly matching element is returned
        filtered_response = list(filter(lambda filterobj: filterobj['name'] == filter_name, response['data']))
        count_filters = len(filtered_response)

        if count_filters > 1:
            module.fail_json(msg=("Error in get_current_filter: filtered_response has more than one element. "
                                  "Should only contain zero or one element."))
        elif count_filters == 1:
            return filtered_response[0]
        else:
            return {}

    def merge_compare(self, current_data: dict, desired_state_data: dict, exclude_path: list = None):
        """
        Check if desired_state_data is already set in current_data. Therfore we are merging the two dictionaries.
        current_data is updated by desired_state_data. After the merging current_data is compared to merged_data.
        If no difference is found. No changes are needed. If there are differences the module needs to update the object

        :param current_data: Currently set settings
        :type current_data: dict
        :param desired_state_data: Settings we want to make sure they exist
        :type desired_state_data: dict
        :param exclude_path: Optional parameter. You can exclude some (nested) keys from comparison
        :type exclude_path: str
        :return: Returns a tuple of diff (DeepDiff object) and the merged_dict (dictionary object)
        :rtype: tuple
        """

        if exclude_path is None:
            exclude_path = []
        # Python does not create new objects by assigning one variable to another. It only copies the reference to the
        # same memory address (copies the pointer). You have to use copy oder deepcopy. Deepcopy creates new objects
        # of the nested objects as well
        merged_dict = copy.deepcopy(current_data)
        self.merge(merged_dict, desired_state_data)
        diff = DeepDiff(current_data, merged_dict, exclude_paths=exclude_path)
        return diff, merged_dict

    @staticmethod
    def compare(dict1: dict, dict2: dict, exclude_path: list = None):
        """
        Compare two dictionaries

        :param dict1: First dict
        :type dict1: dict
        :param dict2: Second dict
        :type dict2: dict
        :param exclude_path: Optional parameter. You can exclude some (nested) keys from comparison
        :type exclude_path: str
        :return: DeepDiff object with the differences of the two dictioniaries
        :rtype: DeepDiff
        """

        diff = DeepDiff(dict1, dict2, exclude_paths=exclude_path)

        return diff

    def merge(self, parent: dict, child: dict):
        """
        Merges nested dictionaries as recursive method. It updates the parent dict with items from the child dict.
        No return is needed because it directly updates the variable which is passed for parent to the method

        :param parent: Parent dictionary which will be updated by child dictionary
        :type parent: dict
        :param child: Child dictionary which updates parent dictionary
        :type child: dict
        """

        for key in child:
            if key in parent and isinstance(parent[key], dict) and isinstance(child[key], dict):
                self.merge(parent[key], child[key])
            else:
                parent[key] = child[key]

    def remove_dict_from_dict(self, current_dict: dict, remove_dict: dict):
        """
        Remove nested dictionary keys from current_dict if they exist in remove_dict.
        This method acts as follows:
        Case 1: If current_dict[key] and remove_dict[key] are dictionaries make recursion with subordinated dictionaries
        Case 2: If current_dict[key] and remove_dict[key] are not a dictionary remove the key from current_dict
        Case 3: If current_dict[key] is a dictionary and remove_dict[key] is not remove the key from current_dict
        Case 4: If current_dict[key] is not a dicitonary and remove_dict[key] is a dictionary do nothing

        :param current_dict: The dictionary from which the keys should be removed
        :type current_dict: dict
        :param remove_dict: The dictionary which should be removed from current_dict
        :type remove_dict: dict
        """

        # Iterate over all keys which should get removed
        for key in remove_dict.keys():
            # Check if key exists in current_dict. Check for None type necessary because value of key could be boolean
            if current_dict.get(key) is not None:
                # If current_dict[key] and remove_dict[key] are dictionaries make recursion with subordinated dictionary
                if isinstance(current_dict[key], dict) and isinstance(remove_dict[key], dict):
                    self.remove_dict_from_dict(current_dict[key], remove_dict[key])
                    # If all keys of the subordinated dictionary are removed, remove the parent key as well
                    if current_dict[key] in ('', None, {}):
                        del current_dict[key]
                # If current_dict[key] is a dict and remove_dict[key] is not or current_dict[key] and remove_dict[key]
                # are no dictionaries remove the key.
                elif (isinstance(current_dict[key], dict) and not isinstance(remove_dict[key], dict)) or (
                        not isinstance(current_dict[key], dict) and not isinstance(remove_dict[key], dict)):
                    del current_dict[key]
