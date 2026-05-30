# Quickstart

Provision an Ubuntu 26.04 VM as a container worker in a few minutes.

## Goal

Apply the `ubuntu2604` role to a target host and verify that container-optimized settings are active.

## Prerequisites

- A target host running **Ubuntu 26.04**
- **Ansible 2.15** or newer on your control node
- SSH access to the target host as a user with `sudo` privileges
- **SSH key-based access** for the Ansible user. The role disables password authentication and will fail if the current Ansible user has no `~/.ssh/authorized_keys` file.

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

The role waits up to 30 minutes for cloud-init to complete before mutating the host, so fresh cloud VMs do not fail on dpkg locks or partial boot-time state.

If your VMs run on AWS, enable AWS-aware behavior such as regional APT mirror selection:

```yaml
- hosts: workers
  vars:
    ubuntu2604_cloud: "aws"
  roles:
    - role: ubuntu2604
```

Or reference the role directly:

```yaml
- hosts: workers
  roles:
    - role: ubuntu2604
```

## Step 4 — Verify the changes

Run the included test suite against your inventory:

```bash
make test
```

This runs [pytest-testinfra](https://testinfra.readthedocs.io/) checks in parallel across all hosts to confirm kernel modules, sysctl persistence, PAM limits, systemd manager defaults, transparent hugepages, swap removal, APT source and mirror configuration, snapd removal and reinstallation block, VPS package cleanup, unattended-upgrade policy, log pressure controls, locale configuration, and SSH hardening.

You can also spot-check individual settings with ad-hoc Ansible commands:

```bash
ansible workers -i inventory.ini -m ansible.builtin.shell -a "lsmod | grep -E 'br_netfilter|nf_conntrack'" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "sysctl net.ipv4.ip_forward" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "free -h | grep -i swap" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "timedatectl show --property=Timezone --value" --become
ansible workers -i inventory.ini -m ansible.builtin.shell -a "resolvectl status" --become
```

## What changed on the host

- Kernel modules `br_netfilter`, `nf_conntrack`, and `overlay` are loaded and persisted
- 30+ sysctl parameters tuned for container networking, density, and recovery
- PAM soft and hard limits for `nofile` and `nproc` raised to `65536`
- Systemd service defaults align file descriptor, process, task, and memory accounting behavior with dense container workloads
- Transparent hugepages set to `madvise` via systemd service
- Swap disabled and removed from `/etc/fstab`
- APT sources configured with AWS-aware regional mirror selection (when `ubuntu2604_cloud: "aws"`) and official-archive fallback
- Safe package upgrades, autoremove, and autoclean applied during the run, with reboot-required markers reported
- Unattended security upgrades enabled with automatic reboots, shutdown-time installs, and needrestart service restarts blocked
- Journald persistence, retention, and `/var/log` free-space pressure limits configured
- `nftables` owns host firewall state, `ufw` is masked, and iptables compatibility commands use the nft backend
- UTF-8 locale generated and set as system default
- Operational troubleshooting toolbox installed (`htop`, `iotop`, `jq`, `tcpdump`, `tmux`, `bind9-dnsutils`, and others)
- Timezone pinned to UTC with `chrony` time synchronization active
- `systemd-resolved` enabled with Cloudflare fallback DNS (`1.1.1.1`, `1.0.0.1`) for when DHCP resolvers are unavailable
- SSH hardened with a priority drop-in (`PasswordAuthentication no`, key-only algorithms, idle timeouts, TCP forwarding disabled) and guardrails that prevent applying the role without key-based access
- `snapd` removed and residual directories cleaned when no snaps are installed, with reinstallation blocked via APT preferences
- ~20 VPS-irrelevant packages purged, including desktop helpers, hardware daemons, cloud agents, and interactive tooling
- Dynamic and static MOTD cleared and `motd-news.timer` masked for quiet SSH logins
- Tasks tagged for selective execution

## Run only specific sections

Every task is tagged with a semantic selector. Use `--tags` or `--skip-tags` to run only the sections you need.

Available tags:

| Tag | Section |
|-----|---------|
| `kernel` | Kernel modules, sysctls, PAM limits, and transparent hugepages |
| `network` | (reserved) |
| `ssh` | SSH hardening, drop-in config, and guardrails |
| `systemd` | System manager resource limits and cgroup accounting defaults |
| `swap` | Swap disable and fstab cleanup |
| `aws` | EC2 metadata gathering and regional APT mirror selection |
| `apt` | APT source configuration, mirror lists, and cache update |
| `upgrade` | Safe package upgrade, autoremove, and autoclean |
| `packages` | Package installs and removals across all sections |
| `unattended_upgrades` | Unattended security upgrades, reboot policy, and needrestart |
| `logs` | Journald persistence, retention, and `/var/log` pressure controls |
| `firewall` | nftables service ownership, UFW masking, and iptables compatibility tools |
| `locale` | Locale generation and default locale setting |
| `time` | Timezone and chrony time synchronization |
| `dns` | systemd-resolved stub and fallback DNS configuration |
| `snap` | Snapd removal, guardrails, and reinstallation block |
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
- Review `ubuntu2604/tasks/main.yml` for the full list of applied settings.
