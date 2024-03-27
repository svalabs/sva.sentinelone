=============================
Sva.Sentinelone Release Notes
=============================

.. contents:: Topics

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
