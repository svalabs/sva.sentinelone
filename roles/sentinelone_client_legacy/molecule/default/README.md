# Testing

In order to test the role you'll need Ansible, Molecule and a supported provider such as Vagrant.

If you also want to test registration, add the following line to [`converge.yml`](converge.yml):

```yml
sentinelone_client_token: "..."
```

Copy the SentinelONE installation files (`sentinelone_latest.deb`, `sentinelone_latest.rpm`) into this directory and run `molecule`:

```shell
$ molecule create
$ molecule converge
```
