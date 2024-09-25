# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marco Wester <marco.wester@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import SentineloneBase
from ansible.module_utils.basic import AnsibleModule


class SentineloneAgentBase(SentineloneBase):
    def __init__(self, module: AnsibleModule):
        module.params['site_name'] = module.params['site']

        module.params['site_name'] = module.params['site']
        # self.token, self.console_url, self.site_name, self.state, self.api_endpoint_*, self.group_names will be set in
        # super Class
        super().__init__(module)

        # Set module specific parameters
        self.agent_version = module.params["agent_version"]
        self.custom_version = module.params["custom_version"]
        self.os_type = module.params["os_type"]
        self.packet_format = module.params["packet_format"]
        self.architecture = module.params["architecture"]
        self.download_dir = module.params.get("download_dir", None)

        # Do sanity checks
        self.check_sanity(self.os_type, self.packet_format, self.architecture, module)

    @staticmethod
    def check_sanity(os_type: str, packet_format: str, architecture: str, module: AnsibleModule):
        """
        Check if the passed module arguments are contradicting each other

        :param architecture: OS architecture
        :type architecture: str
        :param os_type: The specified OS type
        :type os_type: str
        :param packet_format: The speciefied packet format
        :type packet_format: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        """

        if architecture == "aarch64" and os_type != "Linux":
            module.fail_json(msg="Error: architecture 'aarch64' needs os_type to be 'Linux'")

        if os_type == 'Windows':
            if packet_format not in ['exe', 'msi']:
                module.fail_json(msg="Error: 'packet_format' needs to be 'exe' or 'msi' if os_type is 'Windows'")
        elif packet_format not in ['deb', 'rpm']:
            module.fail_json(msg="Error: 'packet_format' needs to be 'deb' or 'rpm' if os_type is 'Linux'")

    def get_package_obj(self, agent_version: str, custom_version: str, os_type: str, packet_format: str,
                        architecture: str, module: AnsibleModule):
        """
        Queries the API to get the info about the agent package which maches the parameters

        :param agent_version: which version to search for
        :type agent_version: str
        :param custom_version: custom agent version if specified
        :type custom_version: str
        :param os_type: For which OS the package should fit
        :type os_type: str
        :param packet_format: the packet format
        :type packet_format: str
        :param architecture: The OS architecture
        :type architecture: str
        :param module: Ansible module for error handling
        :type module: AnsibleModule
        :return: Returns the found agent object
        :rtype: dict
        """

        # Build query parameters dependend on the Modules input
        # Default parameters which are set always
        query_params = {
            'platformTypes': os_type.lower(),
            'sortOrder': 'desc',
            'sortBy': 'version',
            'fileExtension': f".{packet_format}"
        }

        if self.site_id is not None:
            query_params['siteIds'] = str(self.site_id)

        if agent_version == 'custom':
            query_params['version'] = custom_version
        elif agent_version == 'latest':
            query_params['status'] = 'ga'

        if os_type == 'Linux':
            # Use query parameter to do a free text search matching the 'fileName' field beacause S1 API does not
            # provide the information elementary. 'osArches' parameter applies only for windows
            if architecture == 'aarch64':
                query_params['query'] = 'SentinelAgent-aarch64'
            else:
                query_params['query'] = 'SentinelAgent_linux'
        else:
            query_params['packageType'] = 'AgentAndRanger'
            # osArches is only supported if you query windows packaes
            query_params['osArches'] = architecture.replace('_', ' ')

        # translate dictionary to URI argurments and build full query
        query_params_encoded = urlencode(query_params)
        api_query_agent_package = f"{self.api_endpoint_update_agent_packages}?{query_params_encoded}"

        response = self.api_call(module, api_query_agent_package)
        if response["pagination"]["totalItems"] > 0:
            return response["data"][0]

        module.fail_json(msg="Error: No agent package found in management console. Please check the given parameters.")
