=============================
Sva.Sentinelone Release Notes
=============================

.. contents:: Topics

v2.0.2
======

Release Summary
---------------

This is a bugfix release

Bugfixes
--------

- install_agent role: Fixed a bug where idepotency in the 'Windows: Remove agent package from target machine' task was broken.

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
