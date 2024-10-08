# sentinelone_client_legacy

**This role was merged to this collection from the Ansible role [sentinelone_client](https://github.com/stdevel/ansible-sentinelone_client) by [@stdevel](https://github.com/stdevel).**

For greater flexibility, it's recommended to use the install_agent role if you have access to both the management console and an API access token. However, if you don't have console access and need to install the agent packages from an alternate source, this role is designed for that scenario. Please note that the agent package must be accessible via a web server to use this role.

Installs and registers the SentinelOne Endpoint agent with provided os packages (linux only).

## Requirements

No requirements.

## Role Variables

| Variable                                          | Default   | Description                      |
| ------------------------------------------------- | --------- | -------------------------------- |
| `sentinelone_client_filename`                     | *(empty)* | Package file to install          |
| `sentinelone_client_token`                        | *(empty)* | Group/Site token                 |
| `sentinelone_client_gpgkey`                       | *(empty)* | GPG signing key to import        |
| `sentinelone_client_force_new_token`              | `false`   | Set to true to force a new token |
| `sentinelone_client_customer_id`                  | *(empty)* | Set optional customer id         |
| `sentinelone_client_zypper_disable_gpg_check`     | `false`   | Disable GPG Check for zypper     |

## Dependencies

No dependencies.

### Role Documentation
A **[HTML documentation](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_client_legacy_role.html)** in the usual Ansible documentation format can be found [here](https://svalabs.github.io/sva.sentinelone/branch/main/collections/sva/sentinelone/sentinelone_client_legacy_role.html).

## Example Playbook

```yml
- hosts: clients
  roles:
    - role: sva.sentinelone.sentinelone_client_legacy
      sentinelone_client_filename: SentinelAgent_linux_v21_10_3_3.rpm
      sentinelone_client_token: trustno1
```

Repository installation:

```yml
- hosts: clients
  roles:
    - role: sva.sentinelone.sentinelone_client_legacy
      sentinelone_client_filename: https://simone.giertz.dev/SentinelAgent_linux_v13_37.deb
      sentinelone_client_token: trustno1
```

## Development / testing

Use [Ansible Molecule](https://molecule.readthedocs.io/en/latest/index.html) for running tests:

```shell
$ molecule create
$ molecule converge
$ molecule verify
```

## License

BSD

## Author Information

Christian Stankowic
