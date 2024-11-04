# Ansible Collection - sva.sentinelone
[![Sanity checks](https://github.com/svalabs/sva.sentinelone/actions/workflows/ansible-test.yml/badge.svg?branch=main)](https://github.com/svalabs/sva.sentinelone/actions/workflows/ansible-test.yml) [![Collection Docs](https://github.com/svalabs/sva.sentinelone/actions/workflows/build-docs-and-push-to-ghpages.yml/badge.svg?branch=main)](https://github.com/svalabs/sva.sentinelone/actions/workflows/build-docs-and-push-to-ghpages.yml)

## Description
This is the unofficial SentinelOne Collection provided by [SVA](https://www.sva.de)

This collection is a community project and is neither provided nor supported by SentinelOne itself.

It provides several modules which helps to configure and manage SentinelOne Management Consoles.

## Included content

- **Modules**:
  - [sentinelone_agent_info](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_agent_info_module.html)
  - [sentinelone_config_overrides](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_config_overrides_module.html)
  - [sentinelone_download_agent](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_download_agent_module.html)
  - [sentinelone_filters](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_filters_module.html)
  - [sentinelone_groups](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_groups_module.html)
  - [sentinelone_sites](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_sites_module.html)
  - [sentinelone_upgrade_policies](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_upgrade_policies_module.html)
  - [sentinelone_path_exclusions](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_path_exclusions_module.html)
  - [sentinelone_policies](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_policies_module.html)

- **Roles:**
  - [install_agent](roles/install_agent/README.md)
  - [sentinelone_client_legacy](roles/sentinelone_client_legacy/README.md)

## Requirements
### Ansible
- ansible >= 8 **or** ansible-core >= 2.15 (Lower versions may work but they have not been tested)

### Python
- Python >= 3.9 (Ansible control node requirement)

### External
This collection needs the following Python modules:
- deepdiff >= 5.6.0 (Lower versions may work but they have not been tested)

## Tested with Ansible and the following Python versions

Tested Ansible versions:
- 2.15
- 2.16
- 2.17

Tested Python versions:
- 3.9
- 3.10
- 3.11
- 3.12

## Using this collection
### Installing the collection from Ansible Galaxy
Before using this collection, you need to install it with the Ansible Galaxy command-line tool:
```bash
ansible-galaxy collection install sva.sentinelone
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:
```yaml
---
collections:
  - name: sva.sentinelone
```

Note that if you install the collection from Ansible Galaxy, it will not be upgraded automatically when you upgrade the `ansible` package. To upgrade the collection to the latest available version, run the following command:
```bash
ansible-galaxy collection install sva.sentinelone --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax to install version `1.0.0`:

```bash
ansible-galaxy collection install sva.sentinelone:==1.0.0
```

See [Ansible Using collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

## Documentation
### User documentation
The module documentation can be found [here](https://svalabs.github.io/sva.sentinelone/branch/main/collections/index_module.html).

The role documentation can be found [here](https://svalabs.github.io/sva.sentinelone/branch/main/collections/index_role.html).

## Changelog
**v2.0.1**: Bugfix release. Fixed an idempotency bug in install_agent role

**v2.0.0**:
- Added new sentinelone_agent_info module and [@stdevels](https://github.com/stdevel/ansible-sentinelone_client) sentinelone_client role as sentinelone_client_legacy.
- install_agent role: Added configurable retries and delays in the step which checks if the agent appears in the management console.
- **Breaking Changes**: The download_agent modules `state` parameter is no longer available. If you used `state: info` please use the new agent_info module instead. `state` parameter has been removed from download_agent module.

**v1.1.1**: Bugfix release. Changed privilege escalation behaviour

**v1.1.0**: Added new sentinelone_download_agent module and install_agent role

**v1.0.3**: Increased request timeout and implemented error handling for requests that timed out

**v1.0.2**: Added detailed error message to module output if an API call fails

**v1.0.1**: Bugfix release

**v1.0.0**: Initial release

Detailed Changelog can be found at [CHANGELOG](CHANGELOG.rst)

## Todo (help is welcome)
- [ ] Make the modules usable on account scope
- [ ] Unit tests needs to be written

## Licensing
The SVA SentinelOne collection is licensed under the GNU General Public License v3.0+. See [LICENSE](LICENSE) for the full license text.
