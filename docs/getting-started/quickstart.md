# Quickstart

Provision an Ubuntu 26.04 VM as a container worker in a few minutes.

## Goal

Apply the `ubuntu_2604` role to a target host and verify that container-optimized settings are active.

## Prerequisites

- A target host running **Ubuntu 26.04**
- **Ansible 2.15** or newer on your control node
- SSH access to the target host as a user with `sudo` privileges

## Step 1 — Install dependencies

Install the required Ansible collections:

```bash
make deps
```

Or manually:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Step 2 — Add the host to your inventory

Create or edit your inventory file:

```ini
[workers]
worker1.example.com ansible_user=ubuntu
```

## Step 3 — Run the role

Use the included playbook or add the role to your own:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Or reference the role directly:

```yaml
- hosts: workers
  roles:
    - role: ubuntu_2604
```

## Step 4 — Verify the changes

Run the included test suite against your inventory:

```bash
make test
```

This runs [pytest-testinfra](https://testinfra.readthedocs.io/) checks in parallel across all hosts to confirm kernel modules, sysctl persistence, PAM limits, transparent hugepages, swap removal, and locale configuration.

You can also spot-check individual settings with ad-hoc Ansible commands:

```bash
ansible workers -i inventory.ini -m ansible.builtin.shell -a "lsmod | grep -E 'br_netfilter|overlay|nf_conntrack'" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "sysctl net.ipv4.ip_forward" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "free -h | grep -i swap" --become
```

## What changed on the host

- Kernel modules `br_netfilter`, `nf_conntrack`, and `overlay` are loaded and persisted
- 30+ sysctl parameters tuned for container networking, density, and recovery
- PAM soft and hard limits for `nofile` and `nproc` raised to `65536`
- Transparent hugepages set to `madvise` via systemd service
- Swap disabled and removed from `/etc/fstab`
- UTF-8 locale generated and set as system default

## Next steps

- [Configuration reference](../reference/configuration.md) — Customize role behavior.
- Review `ubuntu_2604/tasks/main.yml` for the full list of applied settings.
