# Ubuntu quickstart

## Requirements

- Ubuntu 26.04 on amd64 or arm64; ansible-core ≥ 2.20.
- A compatible control-node Python version: 3.12–3.14 for ansible-core 2.20 ([support matrix](https://docs.ansible.com/projects/ansible-core/2.20/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix)).
- Root or sudo access and a non-empty `~/.ssh/authorized_keys` for the provisioning user.

## Run locally

```bash
ansible-galaxy collection install andreygubarev.com --upgrade
ansible-playbook andreygubarev.com.ubuntu2604
```

No inventory or SSH transport is required. Add `-K` if sudo requires a password.

Set a hostname once:

```bash
ansible-playbook andreygubarev.com.ubuntu2604 -e ubuntu2604_hostname=worker-1
```

Later runs reuse the saved hostname. Without an explicit or saved name, the existing name is unchanged. Other overrides are not remembered; for IPv6/dual-stack hosts, keep supplying `-e ubuntu2604_disable_ipv6=false` or define it in inventory/playbooks.

## Operational cautions

- Intended for fresh container-host VMs. All snaps and their data are purged without backups; use `--skip-tags snap` to retain them.
- Password SSH authentication is disabled. Root provisioning always retains root SSH access, regardless of `ubuntu2604_ssh_allow_root_login`; non-root sudo escalation does not trigger this override.
- First SSH configuration regenerates host keys. Verify new fingerprints through a trusted channel before updating `known_hosts`. See [SSH policy](../reference/configuration.md#ssh-policy) for client requirements.
- Package upgrades run by default. Reboot requirements are reported, but the role does not reboot the host.
- Cloud-init is allowed up to 30 minutes to finish; completed runs with errors produce a warning.

## Select sections

```bash
ansible-playbook andreygubarev.com.ubuntu2604 --tags hostname
ansible-playbook andreygubarev.com.ubuntu2604 --skip-tags upgrade
```

See [tags](../reference/configuration.md#tags). Do not skip `always`; SSH key checks run with `ssh`.

## Remote provisioning

Use the role in your own `workers.yml`:

```yaml
- name: Configure container hosts
  hosts: workers
  roles:
    - andreygubarev.com.ubuntu2604
```

Set the SSH login user in inventory, for example `worker1 ansible_user=ubuntu`, then run:

```bash
ansible-playbook -i inventory.ini workers.yml
```

## Verify

From a repository checkout on the configured host:

```bash
make test TESTINFRA_HOSTS=local://
```

[Configuration](../reference/configuration.md) · [Tasks](../../roles/ubuntu2604/tasks/main.yml)
