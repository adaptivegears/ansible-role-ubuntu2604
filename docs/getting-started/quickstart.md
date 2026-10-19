# Quickstart

Provision an Ubuntu 26.04 VM as a container worker in a few minutes.

## Goal

Run the `andreygubarev.com.ubuntu2604` playbook on the machine you want to configure and verify that container-optimized settings are active.

## Prerequisites

- Run directly on the host you want to configure, running **Ubuntu 26.04**
- **ansible-core 2.20** or newer installed on that host; 2.20 is the first release supporting Ubuntu 26.04's Python 3.14
- A Python version supported by your ansible-core release: **Python 3.12–3.14 for ansible-core 2.20** ([support matrix](https://docs.ansible.com/projects/ansible-core/2.20/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix))
- A local user with `sudo` privileges; add `-K` to the playbook command if sudo requires a password
- **SSH authorized keys** already provisioned for that user. Execution is local, but the role hardens SSH and refuses to disable password authentication without a non-empty `~/.ssh/authorized_keys` file.
- Running as `root` automatically preserves root SSH access, even when `ubuntu2604_ssh_allow_root_login=false`; no extra parameter is needed. Root authorized keys are still required.

## Step 1 — Install the collection

After the first release is published, install from Ansible Galaxy, including the collection's dependencies:

```bash
ansible-galaxy collection install andreygubarev.com
```

Source code is available at [andreygubarev/ansible-collection](https://github.com/andreygubarev/ansible-collection).

For development from a repository checkout, install the local collection and its dependencies instead:

```bash
make deps
```

After editing the source, run `make deps` again to refresh the installed copy.

## Step 2 — Run the local playbook

No inventory or SSH connection is needed:

```bash
ansible-playbook andreygubarev.com.ubuntu2604
```

This configures the machine running the command, using the invoking account for the SSH access guardrails. It changes SSH policy, removes snap packages and their data, and disables swap and IPv6 by default.

The role waits up to 30 minutes for cloud-init to complete before mutating the host, so fresh cloud or VPS images do not fail on dpkg locks or partial boot-time state. The role does not perform cloud-provider detection and uses direct provider-neutral Canonical APT endpoints.

IPv6 is disabled by default with sysctl settings. If a host requires IPv6 or dual-stack networking, keep IPv6 enabled explicitly:

```bash
ansible-playbook andreygubarev.com.ubuntu2604 -e ubuntu2604_disable_ipv6=false
```

## Step 3 — Verify the changes

From a repository checkout, run the included test suite locally (requires sudo access):

```bash
make test TESTINFRA_HOSTS=local://
```

This runs [pytest-testinfra](https://testinfra.readthedocs.io/) checks to confirm kernel modules, sysctl persistence, IPv6 policy, PAM limits, systemd manager defaults, transparent hugepages, swap removal, APT source configuration, snapd removal and reinstallation block, container-worker package cleanup, unattended-upgrade policy, log pressure controls, locale configuration, and SSH hardening.

You can also spot-check individual settings directly:

```bash
lsmod | grep -E 'br_netfilter|nf_conntrack'
sysctl net.ipv4.ip_forward
swapon --show
timedatectl show --property=Timezone --value
resolvectl status
```

## Remote provisioning

The included playbook always targets localhost. To provision remote hosts over SSH, use the role in your own playbook, for example `workers.yml`:

```yaml
- name: Provision container workers
  hosts: workers
  roles:
    - role: andreygubarev.com.ubuntu2604
```

Provide an inventory with the SSH login user:

```ini
[workers]
worker1.example.com ansible_user=ubuntu
```

```bash
ansible-playbook -i inventory.ini workers.yml
```

## What changed on the host

- Kernel modules `br_netfilter`, `nf_conntrack`, and `overlay` are loaded and persisted
- 30+ sysctl parameters tuned for container networking, density, recovery, and IPv6 policy
- PAM soft and hard limits for `nofile` and `nproc` raised to `65536`
- Systemd service defaults align file descriptor, process, task, and memory accounting behavior with dense container workloads
- Transparent hugepages set to `madvise` via systemd service
- Swap disabled and removed from `/etc/fstab`
- APT sources configured with direct provider-neutral Canonical archive and security endpoints
- Safe package upgrades, autoremove, and autoclean applied during the run, with reboot-required markers reported
- Unattended security upgrades enabled with automatic reboots, shutdown-time installs, and needrestart service restarts blocked
- Journald persistence, retention, and `/var/log` free-space pressure limits configured
- `nftables` owns host firewall state, `ufw` is masked, and iptables compatibility commands use the nft backend
- UTF-8 locale generated and set as system default
- Operational troubleshooting toolbox installed (`htop`, `iotop`, `jq`, `tcpdump`, `tmux`, `bind9-dnsutils`, and others)
- Timezone pinned to UTC with `chrony` time synchronization active
- `systemd-resolved` enabled with Cloudflare fallback DNS (`1.1.1.1`, `1.0.0.1`) for when DHCP resolvers are unavailable
- SSH hardened with a priority drop-in (`PasswordAuthentication no`, key-only algorithms, unresponsive-client cleanup, TCP forwarding disabled) and guardrails that prevent applying the role without key-based access
- All installed snaps and their data purged without removal snapshots, then `snapd` removed and residual directories cleaned, with reinstallation blocked via APT preferences
- Container-worker irrelevant packages purged, including desktop helpers, hardware daemons, storage agents, and interactive tooling
- Dynamic and static MOTD cleared and `motd-news.timer` masked for quiet SSH logins
- Tasks tagged for selective execution

## Run only specific sections

Use `--tags` or `--skip-tags` to run only the sections you need. OS and architecture checks and the cloud-init barrier use `always`, so they also run during selective execution. Do not skip `always` when applying the role. SSH access guardrails run with `ssh`; purging all installed snaps and their data and cleaning up snapd also run with `packages`.

Available tags:

| Tag | Section |
|-----|---------|
| `kernel` | Kernel modules, sysctls, PAM limits, and transparent hugepages |
| `network` | All managed sysctls, including IPv6 policy, and prerequisite kernel modules |
| `ssh` | SSH hardening, drop-in config, and guardrails |
| `systemd` | System manager resource limits and cgroup accounting defaults |
| `swap` | Swap disable and fstab cleanup |
| `apt` | APT sources and cache, snapd removal, package cleanup, upgrades, and reboot reporting |
| `upgrade` | Safe package upgrade, autoremove, and autoclean |
| `packages` | Package installs and removals, including all installed snaps and their data, snapd cleanup, upgrades, and reboot reporting |
| `unattended_upgrades` | Unattended security upgrades, reboot policy, and needrestart |
| `logs` | Journald persistence, retention, and `/var/log` pressure controls |
| `firewall` | nftables service ownership, UFW masking, and iptables compatibility tools |
| `locale` | Locale generation and default locale setting |
| `time` | Timezone and chrony time synchronization |
| `dns` | systemd-resolved stub and fallback DNS configuration |
| `snap` | Purge all installed snaps and their data, remove snapd, and block reinstallation |
| `motd` | MOTD cleanup and motd-news timer masking |

Example: apply only kernel and swap tuning:

```bash
ansible-playbook andreygubarev.com.ubuntu2604 --tags "kernel,swap"
```

Example: skip the package upgrade step on a host that is already current:

```bash
ansible-playbook andreygubarev.com.ubuntu2604 --skip-tags upgrade
```

## Next steps

- [Configuration reference](../reference/configuration.md) — Customize role behavior.
- Review `roles/ubuntu2604/tasks/main.yml` for the full list of applied settings.
