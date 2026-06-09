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
  - [sentinelone_client_legacy](roles/sentinelone_client_legacy/README.md) *(deprecated – see [Migration](#migration))*

## Migration

### sentinelone_client_legacy → install_agent

> ⚠️ **Deprecated:** The role `sentinelone_client_legacy` is deprecated and will be removed in a future release. Please migrate to the `install_agent` role.

The `install_agent` role now incorporates all functionality previously provided by `sentinelone_client_legacy`, including support for environments **without API access**. `install_agent` role now supports these two cases:
- Download agent from provided download URL
- Register agent with a provided registration_token

**If both is provided no API access is needed.**
Please see [install_agent role documentation](roles/install_agent/README.md#api-less-installation-no-api-token-required) for more details.

## Requirements
### Ansible
- ansible >= 10 **or** ansible-core >= 2.17 (Lower versions may work but they have not been tested)

### Python
- Python >= 3.10 (Ansible control node requirement)

### External
This collection needs the following Python modules:
- deepdiff >= 5.6.0 (Lower versions may work but they have not been tested)

## Tested with Ansible and the following Python versions

Tested Ansible versions:
- 2.17
- 2.18
- 2.19
- 2.20
- 2.21

Tested Python versions:
- 3.10
- 3.11
- 3.12
- 3.13
- 3.14

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
Detailed Changelog can be found at [CHANGELOG](CHANGELOG.rst)

## Todo (help is welcome)
- [ ] Unit tests needs to be written

## Licensing
The SVA SentinelOne collection is licensed under the GNU General Public License v3.0+. See [LICENSE](LICENSE) for the full license text.
