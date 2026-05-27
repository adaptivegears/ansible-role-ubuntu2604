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

If your VMs run on AWS, enable AWS-aware behavior such as regional APT mirror selection:

```yaml
- hosts: workers
  vars:
    ubuntu_2604_cloud: "aws"
  roles:
    - role: ubuntu_2604
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

This runs [pytest-testinfra](https://testinfra.readthedocs.io/) checks in parallel across all hosts to confirm kernel modules, sysctl persistence, PAM limits, transparent hugepages, swap removal, APT source and mirror configuration, unattended-upgrade policy, and locale configuration.

You can also spot-check individual settings with ad-hoc Ansible commands:

```bash
ansible workers -i inventory.ini -m ansible.builtin.shell -a "lsmod | grep -E 'br_netfilter|nf_conntrack'" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "sysctl net.ipv4.ip_forward" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "free -h | grep -i swap" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "timedatectl show --property=Timezone --value" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "resolvectl status" --become
```

## What changed on the host

- Kernel modules `br_netfilter` and `nf_conntrack` are loaded and persisted
- 30+ sysctl parameters tuned for container networking, density, and recovery
- PAM soft and hard limits for `nofile` and `nproc` raised to `65536`
- Transparent hugepages set to `madvise` via systemd service
- Swap disabled and removed from `/etc/fstab`
- APT sources configured with AWS-aware regional mirror selection (when `ubuntu_2604_cloud: "aws"`) and official-archive fallback
- Safe package upgrades, autoremove, and autoclean applied during the run
- Unattended security upgrades enabled with automatic reboots, shutdown-time installs, and needrestart service restarts blocked
- UTF-8 locale generated and set as system default
- Operational troubleshooting toolbox installed (`htop`, `iotop`, `jq`, `tcpdump`, `tmux`, `bind9-dnsutils`, and others)
- Timezone pinned to UTC with `chrony` time synchronization active
- `systemd-resolved` enabled with Cloudflare fallback DNS (`1.1.1.1`, `1.0.0.1`) for when DHCP resolvers are unavailable
- Dynamic and static MOTD cleared and `motd-news.timer` masked for quiet SSH logins
- Tasks tagged for selective execution

## Run only specific sections

Every task is tagged with a semantic selector. Use `--tags` or `--skip-tags` to run only the sections you need.

Available tags:

| Tag | Section |
|-----|---------|
| `kernel` | Kernel modules, sysctls, PAM limits, and transparent hugepages |
| `swap` | Swap disable and fstab cleanup |
| `aws` | EC2 metadata gathering and regional APT mirror selection |
| `apt` | APT source configuration, mirror lists, and cache update |
| `upgrade` | Safe package upgrade, autoremove, and autoclean |
| `packages` | Package installs and removals across all sections |
| `unattended_upgrades` | Unattended security upgrades, reboot policy, and needrestart |
| `locale` | Locale generation and default locale setting |
| `time` | Timezone and chrony time synchronization |
| `dns` | systemd-resolved stub and fallback DNS configuration |
| `motd` | MOTD cleanup and motd-news timer masking |

Example: apply only kernel and swap tuning:

```bash
ansible-playbook -i inventory.ini playbook.yml --tags "kernel,swap"
```

Example: skip the package upgrade step on a host that is already current:

```bash
ansible-playbook -i inventory.ini playbook.yml --skip-tags upgrade
```

## Next steps

- [Configuration reference](../reference/configuration.md) — Customize role behavior.
- Review `ubuntu_2604/tasks/main.yml` for the full list of applied settings.
