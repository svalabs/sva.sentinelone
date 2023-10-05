# Ansible Collection - sva.sentinelone
[![Sanity checks](https://github.com/svalabs/sva.sentinelone/actions/workflows/ansible-test.yml/badge.svg?branch=main)](https://github.com/svalabs/sva.sentinelone/actions/workflows/ansible-test.yml) [![Collection Docs](https://github.com/svalabs/sva.sentinelone/actions/workflows/build-docs-and-push-to-ghpages.yml/badge.svg?branch=main)](https://github.com/svalabs/sva.sentinelone/actions/workflows/build-docs-and-push-to-ghpages.yml)

## Description
This is the unofficial SentinelOne Collection provided by [SVA](https://www.sva.de)

This collection is a community project and is neither provided nor supported by SentinelOne itself.

It provides several modules which helps to configure and manage SentinelOne Management Consoles.

## Included content

- **Modules**:
  - [sentinelone_config_overrides](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_config_overrides_module.html)
  - [sentinelone_filters](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_filters_module.html)
  - [sentinelone_groups](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_groups_module.html)
  - [sentinelone_sites](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_sites_module.html)
  - [sentinelone_upgrade_policies](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_upgrade_policies_module.html)
  - [sentinelone_path_exclusions](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_path_exclusions_module.html)
  - [sentinelone_policies](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_policies_module.html)

## Requirements
### Ansible
- ansible >= 4 **or** ansible-core >= 2.11

### Python
- Python >= 3.6 (deepdiff requirement)

### External
This collection needs the following Python modules:
- deepdiff >= 5.6.0 (Lower versions may work but they have not been tested)

## Tested with Ansible and the following Python versions

Tested Ansible versions:
- 2.13
- 2.14
- 2.15
- 2.16

Tested Python versions:
- 3.8
- 3.9
- 3.10
- 3.11

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

## Changelog
**v1.0.3**: Increased request timeout and implemented error handling for requests that timed out.

**v1.0.2**: Added detailed error message to module output if an API call fails

**v1.0.1**: Bugfix release

**v1.0.0**: Initial release

Detailed Changelog can be found at [CHANGELOG](CHANGELOG.rst)

## Todo (help is welcome)
- [ ] Make the modules usable on account scope
- [ ] Unit tests needs to be written

## Licensing
The SVA SentinelOne collection is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.
