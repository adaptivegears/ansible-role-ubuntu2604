# Configuration

The `ubuntu_2604` role exposes two user-configurable variables. All other settings are applied as fixed defaults tuned for container-worker VMs.

## Variables

### `ubuntu_2604_cloud`

The cloud platform the VM runs on. This enables platform-specific behavior such as regional APT mirror selection.

| Attribute     | Value          |
|---------------|----------------|
| Type          | String         |
| Default       | `""`           |
| Required      | No             |

Set to `"aws"` on EC2 instances to enable AWS-aware tuning. The role reads EC2 instance metadata to discover the region and prefers the regional `ec2.archive.ubuntu.com` mirror. When left empty, the role uses the official Canonical archives directly.

Example: enable AWS-aware behavior.

```yaml
- hosts: workers
  vars:
    ubuntu_2604_cloud: "aws"
  roles:
    - role: ubuntu_2604
```

### `ubuntu_2604_locale`

The system locale to generate and set as the default.

| Attribute     | Value          |
|---------------|----------------|
| Type          | String         |
| Default       | `en_US.UTF-8`  |
| Required      | No             |

Example: set a different locale in your playbook or inventory.

```yaml
- hosts: workers
  vars:
    ubuntu_2604_locale: C.UTF-8
  roles:
    - role: ubuntu_2604
```

## Fixed defaults

The following settings are not exposed as variables because they are intrinsic to the role's purpose. Change them only by forking or overriding the role tasks.

### Kernel modules

Loaded and persisted on every boot:

- `br_netfilter` — enables bridge netfilter for container bridge policy
- `nf_conntrack` — supports NAT capacity tuning before runtimes start

### Sysctl parameters

Applied via `/etc/sysctl.d/99-ubuntu-2604.conf`:

| Category | Parameters | Rationale |
|----------|------------|-----------|
| Bridge netfilter | `net.bridge.bridge-nf-call-arptables`, `bridge-nf-call-ip6tables`, `bridge-nf-call-iptables` | Allow host policy to see L2/L3 container traffic |
| File descriptors | `fs.file-max`, `fs.nr_open` | Size host pool for dense workers |
| File watching | `fs.inotify.max_queued_events`, `max_user_instances`, `max_user_watches` | Absorb bursts from build and reload tools |
| Recovery | `kernel.panic`, `kernel.panic_on_oops` | Reboot automatically after kernel faults |
| Process space | `kernel.pid_max` | Expand global PID space before cgroup limits |
| Observability | `kernel.task_delayacct` | Track per-task CPU, I/O, and memory delays |
| Networking core | `net.core.netdev_max_backlog`, `net.core.somaxconn` | Queue ingress bursts and deeper accept queues |
| IPv4 | `net.ipv4.ip_forward`, `ip_local_port_range`, `ip_unprivileged_port_start`, `neigh.default.gc_thresh*`, `tcp_*` | Routing, NAT, ARP, and TCP tuning for containers |
| IPv6 | `net.ipv6.conf.all.accept_ra`, `all.forwarding`, `default.accept_ra`, `default.forwarding` | Enable IPv6 routing while preserving SLAAC |
| Connection tracking | `net.netfilter.nf_conntrack_max` | Hold more NAT flow state |
| User namespaces | `user.max_user_namespaces` | Permit rootless containers and build sandboxes |
| Memory | `vm.max_map_count`, `vm.min_free_kbytes`, `vm.overcommit_memory`, `vm.panic_on_oom`, `vm.swappiness` | Support mmap-heavy services and predictable OOM behavior |

### PAM limits

Applied for all users (`*` domain):

| Limit | Type | Value |
|-------|------|-------|
| `nofile` | soft | `65536` |
| `nofile` | hard | `65536` |
| `nproc` | soft | `65536` |
| `nproc` | hard | `65536` |

### Swap

Swap is disabled at runtime and all swap entries are removed from `/etc/fstab`.

### Transparent hugepages

A systemd one-shot service (`transparent-hugepages-madvise`) sets THP to `madvise` on boot, letting runtimes opt in without forcing global hugepages.

### APT and unattended upgrades

The role manages APT deterministically so package resolution is consistent across rebuilds and does not rely on cloud-init defaults.

**Mirror selection**

When `ubuntu_2604_cloud` is set to `"aws"`, the role gathers EC2 metadata via IMDS to discover the region and prefers the regional `ec2.archive.ubuntu.com` mirror with `priority:1`. The official Canonical archives are kept as fallback so a regional outage does not block provisioning. When the cloud variable is empty or set to another value, the role uses the official archive directly.

Mirror lists are written to:

- `/etc/apt/ubuntu-mirrors.txt` — primary archive mirrors
- `/etc/apt/ubuntu-security-mirrors.txt` — security archive mirrors

Sources are configured in DEB822 format at `/etc/apt/sources.list.d/ubuntu.sources` and use the `mirror+file` URI scheme so APT respects the priority lists.

**Safe upgrades**

During each role run the role applies `upgrade: safe`, `autoremove`, and `autoclean`. This keeps fresh VMs current without accepting disruptive dependency changes or leaving orphaned packages on small disks.

**Unattended security upgrades**

The role explicitly installs `unattended-upgrades` and enables periodic security updates while blocking behavior that could disrupt workloads outside a maintenance window:

- Automatic reboot is disabled
- Reboot-with-users is disabled
- Install-on-shutdown is disabled
- `needrestart` is set to list-only mode so stale processes are reported but not restarted automatically

The APT daily and daily-upgrade timers are enabled so metadata and security patches are fetched on schedule.

### Operational packages

The role installs a standard troubleshooting toolbox so incident response does not start by changing package state. Installed packages include `bind9-dnsutils`, `curl`, `exip`, `htop`, `iotop`, `jq`, `less`, `lsof`, `tcpdump`, `tmux`, `traceroute`, `tree`, `unzip`, and `wget`.

### Time

The timezone is pinned to `UTC` and the `chrony` NTP service is enabled and started. UTC everywhere keeps logs from regional workers correlating without timezone translation. The role expects stock Ubuntu 26.04 images where `chrony` is the default time synchronization service; it does not install or replace the time-sync stack.

### DNS

The role ensures `systemd-resolved` is enabled and running, links `/etc/resolv.conf` to the systemd stub resolver, and configures fallback DNS servers (`1.1.1.1` and `1.0.0.1`) in a drop-in file at `/etc/systemd/resolved.conf.d/60-ubuntu-2604-fallback-dns.conf`. Fallback DNS is only consulted when no per-link servers are known, so DHCP-provided resolvers remain primary and internal zone resolution is preserved.

### MOTD

Dynamic MOTD entries under `/etc/update-motd.d` are removed, the static `/etc/motd` file is cleared, transient cache files (`/run/motd.dynamic`, `/var/cache/motd-news`) are removed, and the `motd-news.timer` is stopped, disabled, and masked. The dynamic MOTD framework remains installed but produces no output, keeping SSH logins quiet on container workers.

## Task tags

All tasks carry semantic tags so you can run or skip sections with `ansible-playbook --tags` or `--skip-tags`.

| Tag | Covers |
|-----|--------|
| `kernel` | Kernel modules, sysctls, PAM limits, transparent hugepages service |
| `swap` | Swap disable and `/etc/fstab` cleanup |
| `aws` | EC2 metadata gathering and regional APT mirror selection |
| `apt` | Mirror lists, sources list, and cache update |
| `upgrade` | Safe package upgrade, autoremove, and autoclean |
| `packages` | Package installs and removals across all sections |
| `unattended_upgrades` | Unattended upgrades config, reboot policy, needrestart, and timers |
| `locale` | Locale generation and default locale setting |
| `time` | Timezone and chrony time synchronization |
| `dns` | systemd-resolved stub and fallback DNS configuration |
| `motd` | MOTD cleanup and motd-news timer masking |

Example: run only APT and upgrade tasks:

```bash
ansible-playbook -i inventory.ini playbook.yml --tags "apt,upgrade"
```

## Related pages

- [Quickstart](../getting-started/quickstart.md) — Apply the role and verify results.
