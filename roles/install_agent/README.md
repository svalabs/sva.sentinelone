install_agent
=========

This Ansible role is designed to install the SentinelOne agent package and register the new endpoint in the SentinelOne Management Console.

Supported Operating Systems:
------------
- Red Hat Enterprise Linux (RHEL) / Rocky 8 & 9 & 10
- Fedora 43 & 44
- SUSE Linux Enterprise Server (SLES) / OpenSuse Leap 16
- Debian 12 & 13
- Ubuntu 22.04 & 24.04 & 26.04
- Windows Server 2022 & Server 2025 & Desktop 11

Requirements
------------
### API Token
An API key is required to use this role unless both `custom_client_url` and `registration_token` are set (see [API-less installation](#api-less-installation-no-api-token-required)). It is considered best practice to create a specific 'API user' role for this purpose.

The API user requires the following permissions:
- Endpoints -> View
- Accounts -> View
- Agent Packages -> View
- Groups -> View (If the scope is set to "group")
- Roles -> View
- Sites -> View

### GPG Key (rpm-based linux only)
The GPG key is used to validate the package signatures. If the `gpg_key` variable is not provided, the role will **automatically download** the required key. You can optain the key from the SentinelOne Help page ("**How to Install on a Linux Endpoint with Yum**").

If you prefer to provide the key manually, place it on the host executing the playbook and set the `gpg_key` variable accordingly.

### Become user
**Linux:** On the control-node, where the playbook is executed, only user permissions are required. On the remote node you have to provide a become user since some tasks need to run as root. Either provide a _become_user_ on playbook or _include_role_ task scope or set the variable _ansible_become_user_ accordingly. The remote user must be configured with sudo permissions or other privilege escalation methods.

**Windows:** _ansible_user_ has to be an administrator account. Therefore no privilege escalation is needed.

### Role Documentation
A **[HTML documentation](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/install_agent_role.html)** in the usual Ansible documentation format can be found [here](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/install_agent_role.html).

Role Variables
--------------

### Mandatory Variables

> **Note:** The variables below are only required when using the role **with API access**. If both `custom_client_url` and `registration_token` are defined, these variables are not needed. See [API-less installation](#api-less-installation-no-api-token-required).

| Variable | Example | Description |
| --- | --- | --- |
| `console_url` | https://my-console.sentinelone.net | The URL of the SentinelOne Management Console |
| `api_token` | XXXXXXXXXXXXXXXXXX | The API token for the API user for authentication |
| `site` | prod | The site to which the new hosts should be assigned |

### Optional Variables

| Variable | Default | Choices | Description |
| --- | --- | --- | --- |
| `group` | '' | | An optional group which is part of the site. If set, the agent will be assigned to this group instead of the 'Default Group'. |
| `gpg_key` | '' | | **Linux** only. Provide a local path to a GPG key to be installed and used for package signature verification. If no path is provided, the role will automatically download the required key. |
| `agent_version` | latest | latest, latest_ea, custom | Controls which agent should be installed. latest installs the latest general availability version. If custom is set, `custom_version` is mandatory |
| `check_console_retries` | 3 | | How many times the ansible role tries to find the agent in the management console after installation |
| `check_console_retry_delay` | 20 | | The delay in s between two attempts to find the agent in the management console |
| `custom_version` | | | Install a specific version of the SentinelOne agent. Must be used in combination with `agent_version` set to 'custom' |
| `hide_sensitive` | true | true, false | Hides sensitive information like API keys in module output. Only set to false for debugging purposes |
| `lx_force_new_token` | false | true, false | Linux only: Set the management token on the linux agent even if it is already registered. |
| `win_use_exe` | false | true, false | Windows only: By default, the .msi package is used for installation. If you prefer to use the .exe file, enable this setting |
| `win_allow_reboot` | true | true, false | Windows only: After the removal of a Windows Feature (here Windows Defender) and after the agent installation, a reboot is required. The role is set to reboot at the end of the installation by default. Disable this setting if you wish to skip the reboot. |
| `custom_client_url` | | | Optional URL to a package source to download the SentinelOne client package. If not set, SentinelOne client will be downloaded via SentinelOne Console. When set together with `registration_token`, no API access is required. |
| `registration_token` | | | Optional registration token to manually register the agent. Useful if no API access is available but a registration token was provided by an administrator. If not set, the registration token will be gathered from the API. When set together with `custom_client_url`, no API access is required. |

### Variables from `vars.yml`

**Note:** These variables are for documentation only. Do not override these unless you fully understand their functionality.

| Variable | Description |
| --- | --- |
| `install_agent_pkg_format` | Determines the package format (like .exe, .msi, .deb, .rpm) based on the Ansible facts |
| `install_agent_pkg_arch` | Sets the agent package architecture based on the Ansible facts |
| `install_agent_custom_os_family` | Identifies the underlying operating system (Linux or Windows) |
| `install_agent_api_url` | Sets the API base URL |
| `install_agent_agent_installed` | Determines if the agent is already installed |

Dependencies
------------

If this role is used for Windows hosts, the `ansible.windows` collection needs to be installed.

## API-less Installation (no API token required)

When both `custom_client_url` and `registration_token` are defined, the role operates completely without API access. In this mode, the mandatory variables `console_url`, `api_token`, and `site` are **not required**.

| Variable | Description |
| --- | --- |
| `custom_client_url` | Direct URL to the SentinelOne agent package |
| `registration_token` | Registration token provided by an administrator |

> **Note:** If only one of the two variables is set, API access is still required and `console_url`, `api_token`, and `site` remain mandatory.

Example Playbook
----------------

This is an example how to use this role in your Playbooks:
```yaml
- name: Sentinelone Agent Deployment
  hosts: all
  gather_facts: true
  tasks:
    - name: "Install agent on Linux"
      ansible.builtin.include_role:
        name: sva.sentinelone.install_agent
      vars:
        console_url: "https://your-instance.sentinelone.net"
        api_token: "YOUR_S1_API_TOKEN"
        site: "ansible-test"
        group: "linux" # optional
        gpg_key: "/tmp/sentinel_one.gpg" # optional, downloaded automatically if not set
      when: ansible_facts.ansible_system | default('') == "Linux"

    - name: "Install specific agent version on Linux"
      ansible.builtin.include_role:
        name: sva.sentinelone.install_agent
      vars:
        console_url: "https://your-instance.sentinelone.net"
        api_token: "YOUR_S1_API_TOKEN"
        site: "ansible-test"
        agent_version: 'custom'
        custom_version: '23.4.2.14'
      when: ansible_facts.ansible_system | default('') == "Linux"

    - name: "Install agent on Windows"
      ansible.builtin.include_role:
        name: sva.sentinelone.install_agent
      vars:
        console_url: "https://your-instance.sentinelone.net"
        api_token: "YOUR_S1_API_TOKEN"
        site: "ansible-test"
        group: "windows" # optional
        win_use_exe: true # optional
        win_allow_reboot: false # optional
      when: ansible_facts.os_family == "Windows"

    - name: "Install agent with no API access"
      ansible.builtin.include_role:
        name: sva.sentinelone.install_agent
      vars:
        custom_client_url: "https://example.com/SentinelOne-Agent.deb"
        registration_token: "YOUR_REGISTRATION_TOKEN"
      when: ansible_facts.os_family == "Debian"
```

License
-------

This SVA SentinelOne install_agent role is licensed under the GNU General Public License v3.0+. You can view the complete license text [here](../../LICENSE).

Author Information
------------------

 - Marco Wester (@mwester117)