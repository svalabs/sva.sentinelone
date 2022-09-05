# Ansible Collection - sva.sentinelone
[![CI](https://github.com/svalabs/ansible-collection-sva.sentinelone/workflows/CI/badge.svg)](https://github.com/svalabs/ansible-collection-sva.sentinelone/actions)

## Description
This is the unofficial SentinelOne Collection provided by [SVA](https://www.sva.de)

This collection is a community project and is neither provided nor supported by SentinelOne itself.

It provides several modules which helps to configure and manage SentinelOne Management Consoles.

## Included content

- **Modules**:
  - [sentinelone_config_overrides](docs/ansible-docs/markdown/sentinelone_config_overrides_module.md)
  - [sentinelone_filters](docs/ansible-docs/markdown/sentinelone_config_overrides_module.md)
  - [sentinelone_groups](docs/ansible-docs/markdown/sentinelone_config_overrides_module.md)
  - [sentinelone_sites](docs/ansible-docs/markdown/sentinelone_sites_module.md)
  - [sentinelone_upgrade_policies](docs/ansible-docs/markdown/sentinelone_upgrade_policies_module.md)
  - [sentinelone_path_exclusions](docs/ansible-docs/markdown/sentinelone_config_overrides_module.md)
  - [sentinelone_policies](docs/ansible-docs/markdown/sentinelone_config_overrides_module.md)

## Requirements
### Ansible
- ansible >= 3 **or** ansible-core >= 2.10

### Python
- Python >= 3.6 (deepdiff requirement)

### External
This collection needs the following Python modules:
- deepdiff >= 5.6.0 (Lower versions may work but they have not been tested)

## Tested with Ansible and the following Python versions

Tested Ansible versions:
- 2.10
- 2.11
- 2.12
- 2.13

Tested Python versions:
- 3.6
- 3.7
- 3.8
- 3.9
- 3.10

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
The module documentation is found in the [docs/ansible-docs](docs/ansible-docs/) folder.

A HTML and Markdown rendered documentation is available.

### Developer documentation
The technical documentation (docstring documentation) can be found at [docs/python-docs](docs/python-docs).

A HTML and Markdown rendered documentation is available.

## Changelog
**v1.0.0**: Initial release

Detailed Changelog can be found at [CHANGELOG](CHANGELOG.rst)

## Todo (help is welcome)
- [ ] Make the modules usable on account scope
- [ ] Unit tests needs to be written

## Licensing
The SVA SentinelOne collection is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.
