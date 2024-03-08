install_agent
=========

This Ansible role is designed to install the SentinelOne agent package and register the new endpoint in the SentinelOne Management Console.

## Supported Operating Systems:
- Red Hat Enterprise Linux (RHEL)
  - 8
  - 9
- SUSE Linux Enterprise Server (SLES)
  - 12
  - 15
- Debian
  - 10
  - 11
  - 12
- Ubuntu
  - 20.04
  - 22.04
  - 24.04

Requirements
------------

An API key is required to use this role. It is considered best practice to create a specific 'API user' role for this purpose.

The API user requires the following permissions:
- Read site info
- Read group info (if the scope is set to group)
- Download agent packages
- Read the site or group registration token
- Read agent information

Role Variables
--------------

### Mandatory Variables

| Variable | Example | Description |
| --- | --- | --- |
| `console_url` | https://my-console.sentinelone.net | The URL of the SentinelOne Management Console |
| `api_token` | XXXXXXXXXXXXXXXXXX | The API token for the API user for authentication |
| `site` | prod | The site to which the new hosts should be assigned |

### Optional Variables

| Variable | Default | Choices | Description |
| --- | --- | --- | --- |
| `group` | | | An optional group which is part of the site. If set, the agent will be assigned to this group instead of the 'Default Group'. |
| `agent_version` | latest | latest, latest_ea, custom | Controls which agent should be installed. latest installs the latest general availability version. If custom is set, `custom_version` is mandatory |
| `custom_version` | | | Install a specific version of the SentinelOne agent. Must be used in combination with `agent_version` set to 'custom' |
| `hide_sensitive` | true | true, false | Hide sensitive information like API keys in module output.Only set to false for debugging purposes |
| `lx_force_new_token` | false | true, false | Linux only: Set the management token on the linux agent even if it is already registered. |
| `win_download_exe` | false | true, false | Windows only: By default, the .msi package is used for installation. If you prefer to use the .exe file, enable this setting |
| `win_allow_reboot` | true | true, false | Windows only: After the removal of a Windows Feature (here Windows Defender) and after the agent installation, a reboot is required. The role is set to reboot at the end of the installation by default. Disable this setting if you wish to skip the reboot. |

### Variables from `vars.yml`

**Note:** These variables are for documentation only. Do not override these unless you fully understand their functionality.

| Variable | Description |
| --- | --- |
| `pkg_format` | Determines the package format (like .exe, .msi, .deb, .rpm) based on the Ansible facts |
| `pkg_arch` | Sets the agent package architecture based on the Ansible facts |
| `os_family` | Identifies the underlying operating system (Linux or Windows) |
| `api_url` | Sets the API base URL |
| `agent_installed` | Determines if the agent is already installed |

## Dependencies
------------

If this role is used for Windows hosts, the `ansible.windows` collection needs to be installed.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

This SVA SentinelOne install_agent role is licensed under the GNU General Public License v3.0+. You can view the complete license text [here](../../LICENSE).

Author Information
------------------

 - Marco Wester (@mwester117)
