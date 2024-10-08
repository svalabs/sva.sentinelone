#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marco Wester <marco.wester@sva.de>
#                      Erik Schindler <erik.schindler@sva.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
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
  agent_version:
    description:
      - "Version of the agent to be downloaded."
      - "B(latest) (default) - download latest GA (stable) release for the specified parameters"
      - "B(latest_ea) - same as latest, but also includes EA packages"
      - "B(custom) - custom_version is required when agent_versioin is custom"
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
      - "Will be ignored if B(agent_version) is not B(custom)"
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
      - "Windows: Only B(32_bit) and B(64_bit) are allowed"
      - "Linux: If not set 64 bit agent will be downloaded. If set to B(aarch64) the ARM agent will be downloaded"
    type: str
    required: false
    default: 64_bit
    choices:
      - 32_bit
      - 64_bit
      - aarch64
  download_dir:
    description:
      - "Set the path where the agent should be downloaded."
      - "If not set the agent will be downloaded to the working directory."
      - "If the directory does not exists it will be created"
    type: str
    required: false
    default: ./
author:
  - "Marco Wester (@mwester117) <marco.wester@sva.de>"
  - "Erik Schindler (@mintalicious) <erik.schindler@sva.de>"
requirements:
  - "deepdiff >= 5.6"
notes:
  - "Python module deepdiff. Tested with version >=5.6. Lower version may work too"
  - "Currently only supported in single-account management consoles"
'''

EXAMPLES = r'''
---
- name: Download latest agent for linux
  sva.sentinelone.sentinelone_download_agent:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    os_type: "Linux"
    packet_format: "rpm"
    download_path: "/tmp"
    architecture: "64_bit"
- name: Download latest agent for linux and include EA packages
  sva.sentinelone.sentinelone_download_agent:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    os_type: "Linux"
    packet_format: "rpm"
    download_path: "/tmp"
    architecture: "64_bit"
    agent_version: "latest_ea"
- name: Download specific agent version
  sva.sentinelone.sentinelone_download_agent:
    console_url: "https://XXXXX.sentinelone.net"
    token: "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    os_type: "Windows"
    packet_format: "msi"
    architecture: "64_bit"
    agent_version: "custom"
    custom_version: "23.2.3.358"
'''

RETURN = r'''
---
original_message:
    description: Get detailed infos about the downloaded package
    type: str
    returned: on success
    sample: >-
      {'download_path': './', 'filename': 'SentinelInstaller_windows_64bit_v23_2_3_358.msi',
      'full_path': './SentinelInstaller_windows_64bit_v23_2_3_358.msi'}
message:
    description: Get basic infos about the downloaded package in an human readable format
    type: str
    returned: on success
    sample: Downloaded file SentinelInstaller_windows_64bit_v23_2_3_358.msi to ./
'''

from os import path, makedirs, remove

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_agent_base import SentineloneAgentBase
from ansible_collections.sva.sentinelone.plugins.module_utils.sentinelone.sentinelone_base import lib_imp_errors


class SentineloneDownloadAgent(SentineloneAgentBase):
    def __init__(self, module: AnsibleModule):
        """
        Initialization of the DownloadAgent object

        :param module: Requires the AnsibleModule Object for parsing the parameters
        :type module: AnsibleModule
        """

        # super Class
        super().__init__(module)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        console_url=dict(type='str', required=True),
        site=dict(type='str', required=False),
        token=dict(type='str', required=True, no_log=True),
        agent_version=dict(type='str', required=False, default='latest', choices=['latest', 'latest_ea', 'custom']),
        custom_version=dict(type='str', required=False),
        os_type=dict(type='str', required=True, choices=['Linux', 'Windows']),
        packet_format=dict(type='str', required=True, choices=['rpm', 'deb', 'msi', 'exe']),
        architecture=dict(type='str', required=False, choices=['32_bit', '64_bit', 'aarch64'], default="64_bit"),
        download_dir=dict(type='str', required=False, default='./')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('agent_version', 'custom', ('custom_version',))
        ],
        supports_check_mode=False
    )

    if not lib_imp_errors['has_lib']:
        module.fail_json(msg=missing_required_lib("DeepDiff"), exception=lib_imp_errors['lib_imp_err'])

    # Create DownloadAgent Object
    download_agent_obj = SentineloneDownloadAgent(module)

    agent_version = download_agent_obj.agent_version
    custom_version = download_agent_obj.custom_version
    os_type = download_agent_obj.os_type
    packet_format = download_agent_obj.packet_format
    architecture = download_agent_obj.architecture

    # Get package object from API with given parameters
    package_obj = download_agent_obj.get_package_obj(agent_version, custom_version, os_type, packet_format, architecture, module)

    changed = False
    download_dir = download_agent_obj.download_dir
    url = package_obj['link']
    filename = package_obj['fileName']
    sha1_expected = package_obj['sha1']
    filepath = f"{download_dir.rstrip('/')}/{filename}"

    if path.exists(filepath):
        basic_message = f"File {filename} already exists in {download_dir} - nothing to do."
    else:
        # Ensure download_dir exists and is a directory
        dest_is_dir = path.isdir(download_dir)
        if not dest_is_dir:
            if path.exists(download_dir):
                module.fail_json(msg=f"{download_dir} is a file but should be a directory.")
            else:
                makedirs(download_dir)

        result = download_agent_obj.api_call(module, url, parse_response=False)

        with open(filepath, 'wb') as file:
            file.write(result.read())

        # Check SHA1 checksum
        sha1_file = module.sha1(filepath)
        if sha1_file != sha1_expected:
            remove(filepath)
            module.fail_json(msg="Download failed. SHA1 checksum mismatch. Deleted broken file.")

        changed = True
        basic_message = f"Downloaded file {filename} to {download_dir}"
    original_message = {'download_dir': download_dir, 'filename': filename, 'full_path': filepath}

    result = dict(
        changed=changed,
        original_message=original_message,
        message=basic_message
    )

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
