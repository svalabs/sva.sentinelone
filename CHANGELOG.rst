=============================
Sva.Sentinelone Release Notes
=============================

.. contents:: Topics

v2.3.0
======

Release Summary
---------------

This release includes a new feature that allows the SentinelOne agent to be installed on Windows systems without requiring a direct connection from the installer to the management console.

Minor Changes
-------------

- Added a new optional variable `win_msi_no_connection_from_installer_to_mgmt` that can be set to true to prevent the MSI installer from checking the connection to the management console during installation. This is useful in scenarios where the installer may fail the connection check but the agent can still connect to the management console after installation.

v2.2.0
======

Release Summary
---------------

Implemented support for Windows ARM machines and more

Major Changes
-------------

- Added molecule tests for ARM Windows machines
- Added molecule tests for Ubuntu 26.04
- download_agent module: Added support for downloading ARM Windows agents

Bugfixes
--------

- install_agent role: Fixed installation of zypper bindings

v2.1.0
======

Release Summary
---------------

This release introduces token-based agent registration and custom source installation
for the ``install_agent`` role, eliminating the API access requirement when both
features are combined. Full Molecule test coverage for Linux and Windows targets has
been added. Additionally, various minor improvements, bug fixes, compatibility updates
for ansible-core 2.20, and a deprecation notice for the ``sentinelone_client_legacy``
role are included.

Major Changes
-------------

- general - Implemented full Molecule test coverage for Linux and Windows targets using Vagrant VirtualBox machines for modules and the ``install_agent`` role.
- install_agent role - Added support for installing agents from a custom source via ``custom_client_url`` variable.
- install_agent role - Added token-based registration support via ``registration_token`` variable, enabling agent installation and registration without API access when combined with ``custom_client_url``.
- install_agent role - If both ``custom_client_url`` and ``registration_token`` are set, no API access is required and ``api_token`` does not need to be provided.

Minor Changes
-------------

- general - Added ``tox-ansible.ini`` to fix sanity check runs.
- general - Added dedicated ``README.md`` for Molecule tests.
- install_agent role - GPG key is now downloaded automatically if ``gpg_key`` is not provided.
- install_agent role - Renamed internal variables to meet Ansible best practices and linting requirements (added install_agent variable prefix).
- install_agent role - Switched from bare Ansible facts (e.g. ``ansible_os_family``) to the ``ansible_facts`` dictionary to comply with ansible-core 2.20 deprecation.
- install_agent role - Updated ``README.md`` with current usage instructions and variable reference.
- modules - Renaming: Removed ``sentinelone_`` prefix from module names; old names remain available as aliases via ``meta/runtime.yml``.
- modules - Updated inline module documentation.
- sentinelone_download_agent module - Fixed wrong variable used in task example (https://github.com/svalabs/sva.sentinelone/issues/64).

Deprecated Features
-------------------

- sentinelone_client_legacy role - The ``sentinelone_client_legacy`` role is deprecated and will be removed in release 3.0.0. Please migrate to the ``install_agent`` role as documented in the ``README.md``.

Bugfixes
--------

- general - Fixed multiple linting errors across roles and removed previous linting exclusions.
- install_agent role - Clarified exact API role permissions required in documentation.
- install_agent role - Explicitly set ``become: false`` for localhost tasks to prevent failures when a global ``ansible.cfg`` specifies ``become: true`` (https://github.com/svalabs/sva.sentinelone/pull/72).
- install_agent role - Fixed compatibility with newer Ansible versions where OS fact values are no longer capitalized; added ``| lower`` filter for robust matching.
- install_agent role - Fixed error handling when waiting for the agent to appear; authentication failures or unexpected response formats now surface the real error instead of a parsing error.
- install_agent role - Fixed nested variable expansion when constructing the endpoint URL; previously the URL still contained unexpanded strings like ``/api/{{ siteid }}/path``.
- upgrade_policies module - Fixed idempotency issue that caused unnecessary task re-runs.
- upgrade_policies module - Fixed locale issue that caused failures on systems using a 24h locale.

v2.0.6
======

Release Summary
---------------

Added the ability to install own s1 packaged with the role without API usage

v2.0.5
======

Minor Changes
-------------

- add filter on os_type while get request on exclusions
- output URL in failure message of api_call
- when updating s1 exclusions do put request instead of delete and post

v2.0.4
======

Release Summary
---------------

This is a bugfix release

Bugfixes
--------

- config_override: Fixed an error where multiple config_override objects where returned by API which caused module to fail in certain situations

v2.0.3
======

Release Summary
---------------

This is a bgfix release

Bugfixes
--------

- install_agent role: Fixed a bug which broke OpenSUSE compatibility

v2.0.2
======

Release Summary
---------------

This is a bugfix release

Bugfixes
--------

- Reversed changes made in v2.0.1.
- install_agent role: Fixed a bug where idempotency in the 'Windows: Remove agent package from target machine' task was broken.

v2.0.1
======

Release Summary
---------------

Bugfix release

Bugfixes
--------

- Fixed a bug where the install_agent role fails on local tasks if "ansible_connection" var is set in playbook.

v2.0.0
======

Release Summary
---------------

- Added new agent_info module and merged sentinelone_client_legacy from @stdevel.
- Added new `check_console_retries` and `check_console_retry_delay` in install_agent role.
- Switched to ansible-content-actions in pipelines

Minor Changes
-------------

- Pipelines: Switched ansible-content-actions when performing sanity checks, linting and release to ansible galaxy

Breaking Changes / Porting Guide
--------------------------------

- The download_agent modules `state` parameter is no longer available. If you used `state: info` please use the new agent_info module instead.
- `state` parameter has been removed from download_agent module.

New Modules
-----------

- sva.sentinelone.sentinelone_agent_info - Get info about the SentinelOne agent package

New Roles
---------

- sva.sentinelone.sentinelone_client_legacy - Entrypoint for sentinelone_client_legacy role

v1.1.1
======

Release Summary
---------------

Maintenance release

Bugfixes
--------

- install_agent role: Added 'become: true' to necessary linux tasks. It is no longer necessary to use 'become: true' on playbook level. Fixes https://github.com/svalabs/sva.sentinelone/issues/30
- install_agent role: Added missing 'urlencode' filter so special characters like space can be used in site or group names. Fixes https://github.com/svalabs/sva.sentinelone/issues/28

v1.1.0
======

Release Summary
---------------

This is the release v1.1.0 of the ``sva.sentinelone`` collection. It introduces new modules and roles.
Modules: sentinelone_download_agent
Roles: install_agent

New Modules
-----------

- sva.sentinelone.sentinelone_download_agent - Download SentinelOne agent from Management Console

New Roles
---------

- sva.sentinelone.install_agent - A role to download and install SentinelAgent on Windows and Linux hosts

v1.0.3
======

Release Summary
---------------

Increased request timeout and implemented error handling for requests that timed out.

v1.0.2
======

Release Summary
---------------

Added detailed error message to module output if an API call fails

v1.0.1
======

Release Summary
---------------

This is a bugfix release

Bugfixes
--------

- sentinelone_policies module: When a group policy inherited from the site scope was updated with a custom setting, all other settings were reset to the default values. Now the inherited settings are updated by the settings passed to the module and the other inherited settings are retained.

v1.0.0
======

Release Summary
---------------

This is the initial version of the ``sva.sentinelone`` collection

New Modules
-----------

- sva.sentinelone.sentinelone_config_overrides - Manage SentinelOne Config Overrides
- sva.sentinelone.sentinelone_filters - Manage SentinelOne Filters
- sva.sentinelone.sentinelone_groups - Manage SentinelOne Groups
- sva.sentinelone.sentinelone_path_exclusions - Manage SentinelOne Path Exclusions
- sva.sentinelone.sentinelone_policies - Manage SentinelOne Policies
- sva.sentinelone.sentinelone_sites - Manage SentinelOne Sites
- sva.sentinelone.sentinelone_upgrade_policies - Manage SentinelOne Upgrade Policies
