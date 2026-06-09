# Configuration

The `ubuntu2604` role exposes five user-configurable variables. All other settings are applied as fixed defaults tuned for container-worker VMs.

## Variables

### `ubuntu2604_disable_ipv6`

Whether to disable IPv6 with persistent sysctl settings.

| Attribute     | Value          |
|---------------|----------------|
| Type          | Boolean        |
| Default       | `true`         |
| Required      | No             |

When `true`, the role sets `net.ipv6.conf.all.disable_ipv6`, `net.ipv6.conf.default.disable_ipv6`, and `net.ipv6.conf.lo.disable_ipv6` to `1` in `/etc/sysctl.d/99-ubuntu2604.conf` and applies the settings immediately. Set this to `false` for Kubernetes or container hosts that need IPv6 or dual-stack networking; OS-level IPv6 disablement can interfere with container networking.

Example: keep IPv6 enabled for hosts that require IPv6 or dual-stack networking.

```yaml
- hosts: workers
  vars:
    ubuntu2604_disable_ipv6: false
  roles:
    - role: ubuntu2604
```

### `ubuntu2604_locale`

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
    ubuntu2604_locale: C.UTF-8
  roles:
    - role: ubuntu2604
```

### `ubuntu2604_timezone`

The system timezone to set and persist.

| Attribute     | Value          |
|---------------|----------------|
| Type          | String         |
| Default       | `UTC`          |
| Required      | No             |

Example: set a different timezone.

```yaml
- hosts: workers
  vars:
    ubuntu2604_timezone: America/New_York
  roles:
    - role: ubuntu2604
```

### `ubuntu2604_ssh_allow_root_login`

Whether to permit root login over SSH.

| Attribute     | Value          |
|---------------|----------------|
| Type          | Boolean        |
| Default       | `false`        |
| Required      | No             |

When `false`, the role sets `PermitRootLogin no` in the SSH hardening drop-in. If you run Ansible as `root`, the role fails before mutating the host unless you explicitly set this to `true`.

Example: allow root SSH for recovery paths.

```yaml
- hosts: workers
  vars:
    ubuntu2604_ssh_allow_root_login: true
  roles:
    - role: ubuntu2604
```

### `ubuntu2604_ssh_allow_tcp_forwarding`

Whether to allow SSH TCP forwarding (tunnels).

| Attribute     | Value          |
|---------------|----------------|
| Type          | Boolean        |
| Default       | `false`        |
| Required      | No             |

When `false`, the role sets `AllowTcpForwarding no` in the SSH hardening drop-in.

Example: allow TCP forwarding.

```yaml
- hosts: workers
  vars:
    ubuntu2604_ssh_allow_tcp_forwarding: true
  roles:
    - role: ubuntu2604
```

## Fixed defaults

The following settings are not exposed as variables because they are intrinsic to the role's purpose. Change them only by forking or overriding the role tasks.

### Kernel modules

Loaded and persisted on every boot:

- `br_netfilter` — enables bridge netfilter for container bridge policy
- `nf_conntrack` — supports NAT capacity tuning before runtimes start
- `overlay` — makes OverlayFS readiness explicit for runtimes that use overlay snapshotters

### Sysctl parameters

Applied via `/etc/sysctl.d/99-ubuntu2604.conf`:

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
| IPv6 | `all.disable_ipv6`, `default.disable_ipv6`, `lo.disable_ipv6`, `all.accept_ra`, `all.forwarding`, `default.accept_ra`, `default.forwarding` | Disable IPv6 by default, or keep IPv6 routing/SLAAC enabled when `ubuntu2604_disable_ipv6` is false |
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

### Systemd manager defaults

System services inherit density-oriented defaults from `/etc/systemd/system.conf.d/60-ubuntu2604-density.conf` so container runtimes and agents launched by systemd do not fall back to lower manager defaults than PAM-launched sessions.

| Setting | Value | Rationale |
|---------|-------|-----------|
| `DefaultLimitNOFILE` | `65536` | Align service file-descriptor limits with the role's kernel and PAM ceilings |
| `DefaultLimitNPROC` | `65536` | Keep service process trees from hitting systemd defaults before explicit cgroup or runtime policy |
| `DefaultTasksMax` | `65536` | Give dense units headroom for colocated service and container process trees |
| `DefaultMemoryAccounting` | `yes` | Attribute memory pressure to service units during incidents |
| `DefaultTasksAccounting` | `yes` | Track per-unit task counts so PID pressure is visible before exhaustion |

Ubuntu 26.04 uses systemd on the unified cgroup hierarchy, where CPU usage accounting is always available and `DefaultCPUAccounting` is deprecated. The role therefore does not set that no-op option. Changing the managed defaults requires a systemd manager re-exec, so the role notifies a handler to apply that re-exec when the drop-in changes.

### Swap

Swap is disabled at runtime and all swap entries are removed from `/etc/fstab`.

### Transparent hugepages

A systemd one-shot service (`transparent-hugepages-madvise`) sets THP to `madvise` on boot, letting runtimes opt in without forcing global hugepages.

### SSH

The role hardens SSH through a priority drop-in at `/etc/ssh/sshd_config.d/00-ubuntu2604-hardening.conf` so site-specific or cloud-init snippets in later drop-ins do not silently override the policy. Before applying hardening, the role runs guardrails that prevent accidental lockout:

- If Ansible is connected as `root`, the role refuses to continue unless `ubuntu2604_ssh_allow_root_login` is `true`.
- If the current Ansible user has no `~/.ssh/authorized_keys` file, the role refuses to continue because disabling password authentication would lock you out.

The drop-in enforces the following settings:

| Setting | Value | Rationale |
|---------|-------|-----------|
| `PasswordAuthentication` | `no` | Require key-based authentication |
| `PermitRootLogin` | `no` (unless opted in) | Reduce root attack surface |
| `PubkeyAuthentication` | `yes` | Ensure key access works |
| `PermitEmptyPasswords` | `no` | Block empty password logins |
| `HostbasedAuthentication` | `no` | Disable legacy trust |
| `IgnoreRhosts` | `yes` | Disable `.rhosts` trust |
| `PermitUserEnvironment` | `no` | Prevent user-controlled environment injection |
| `AllowTcpForwarding` | `no` (unless opted in) | Avoid unaudited tunnels on workers |
| `X11Forwarding` | `no` | Disable desktop forwarding |
| `ClientAliveInterval` | `300` | Bound idle sessions |
| `ClientAliveCountMax` | `0` | Terminate unresponsive sessions |
| `LoginGraceTime` | `60` | Limit unauthenticated window |
| `MaxAuthTries` | `3` | Slow brute-force attempts |
| `MaxSessions` | `3` | Limit concurrent sessions per connection |
| `MaxStartups` | `10:30:60` | Rate-limit unauthenticated connections |
| `LogLevel` | `VERBOSE` | Aid recovery without debug noise |
| Ciphers | `aes256-ctr,aes192-ctr,aes128-ctr` | Small audited set |
| MACs | `hmac-sha2-512,hmac-sha2-256` | Small audited set |
| KexAlgorithms | `ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256` | Small audited set |
| HostKeyAlgorithms | `ecdsa-sha2-nistp521,ecdsa-sha2-nistp384,ecdsa-sha2-nistp256` | Small audited set |

The role also tightens permissions on `/etc/ssh/sshd_config` and host keys, validates the configuration with `sshd -t`, and ensures the `ssh` service is enabled and running.

### APT and unattended upgrades

The role manages APT deterministically so package resolution is consistent across rebuilds and does not rely on cloud-init defaults.

**Mirror selection**

The role uses provider-neutral Canonical archive endpoints directly and does not perform cloud-provider detection or metadata probing. Primary packages come from `archive.ubuntu.com`; security packages prefer `security.ubuntu.com` with `archive.ubuntu.com` as fallback.

Ubuntu 26.04 publishes arm64 packages through the normal archive and security endpoints. Aarch64 hosts therefore intentionally use the same mirror lists as amd64 instead of switching to `ports.ubuntu.com`, which older Ubuntu releases commonly required.

Mirror lists are written to:

- `/etc/apt/ubuntu-mirrors.txt` — primary archive mirrors
- `/etc/apt/ubuntu-security-mirrors.txt` — security archive mirrors

Sources are configured in DEB822 format at `/etc/apt/sources.list.d/ubuntu.sources` and use the `mirror+file` URI scheme so APT respects the priority lists.

**cloud-init wait**

On cloud images, the role waits up to 30 minutes for cloud-init to complete before mutating the host. This prevents failures from dpkg locks held by boot-time package operations. If cloud-init exits with errors, the role warns and continues because the sequencing barrier is satisfied; inspect `cloud-init status --long` if you need details.

**Safe upgrades**

During each role run the role applies `upgrade: safe`, `autoremove`, and `autoclean`. The `apt` task uses a 10-minute lock timeout so cloud-init or unattended upgrades at boot do not cause immediate failure. This keeps fresh VMs current without accepting disruptive dependency changes or leaving orphaned packages on small disks. If upgraded packages create `/var/run/reboot-required`, the role reports the marker and package list but does not reboot the host.

**Unattended security upgrades**

The role explicitly installs `unattended-upgrades` and enables periodic security updates while blocking behavior that could disrupt workloads outside a maintenance window:

- Automatic reboot is disabled
- Reboot-with-users is disabled
- Install-on-shutdown is disabled
- `needrestart` is set to list-only mode so stale processes are reported but not restarted automatically

The APT daily and daily-upgrade timers are enabled so metadata and security patches are fetched on schedule.

### Logs

The role keeps journald persistent for post-reboot recovery while bounding disk usage on container workers that can emit large runtime and workload log bursts. The managed drop-in is `/etc/systemd/journald.conf.d/60-ubuntu2604-log-pressure.conf`.

| Setting | Value | Rationale |
|---------|-------|-----------|
| `Storage` | `persistent` | Preserve host logs across VM reboots and kernel panic recovery |
| `Compress` | `yes` | Reduce disk pressure from older journal files without losing recent context |
| `SystemMaxUse` | `1G` | Cap persistent journal growth on small worker disks |
| `SystemMaxFileSize` | `128M` | Rotate journal files before individual files become expensive to inspect or vacuum |
| `MaxRetentionSec` | `30day` | Keep enough local history for incident review without indefinite retention |
| `MaxFileSec` | `1week` | Ensure time-based rotation happens even during low-volume periods |
| `SystemKeepFree` | `2G` | Preserve free space on the filesystem that backs `/var/log` so log bursts do not crowd out package operations or workload state |
| `RuntimeMaxUse` | `256M` | Bound volatile journal growth before persistent storage is available |
| `RuntimeKeepFree` | `512M` | Preserve free space on `/run` during early boot or degraded storage states |

The role also ensures `/var/log/journal` exists with the standard `systemd-journal` group and vacuums existing journal files to the configured size/time limits during convergence. It does not manage application-specific logrotate policy.

### Firewall

The role makes `nftables` the host firewall manager on Ubuntu 26.04. It installs `conntrack`, `iptables`, and `nftables`, enables the `nftables` service, masks `ufw`, and pins the iptables-family compatibility commands to the nft backend. The role does not manage `/etc/nftables.conf` or define filtering policy; site-specific firewall rules can own that file without fighting this role.

### Snap

The role removes `snapd` from server images when no snap packages are installed. Before removal, it checks for installed snaps and fails with a clear message if any are present, so workload ownership is not accidentally destroyed.

When safe to proceed, the role:

- Stops `snapd.service`, `snapd.socket`, and `snapd.seeded.service`
- Purges the `snapd` package
- Blocks reinstallation by pinning `snapd` at negative priority in `/etc/apt/preferences.d/99-ubuntu2604-nosnap.pref`
- Removes residual directories: `/snap`, `/var/cache/snapd`, `/var/lib/snapd`, `/var/snap`
- Reloads systemd units so stale mount and service references are dropped

If your workload relies on snaps, either migrate them to another packaging format or skip the `snap` tag.

### Container-worker package removal

The role purges packages that are relevant to desktops, physical hardware, SAN-style storage, or broad interactive server images but unnecessary for the provider-neutral container-worker baseline. Removed packages include:

- **Hardware daemons**: `modemmanager`, `fwupd`, `udisks2`, `bolt`
- **Storage agents**: `multipath-tools`, `open-iscsi`
- **GUI/package helpers**: `software-properties-common`, `packagekit`, `polkitd`
- **Crash reporting**: `apport`, `apport-core-dump-handler`
- **Interactive/update tooling**: `pollinate`, `networkd-dispatcher`, `ubuntu-pro-client`, `ubuntu-pro-client-l10n`, `update-manager-core`, `update-notifier-common`, `ubuntu-minimal`, `sysstat`

These removals reduce image size, idle services, and boot-time noise without assuming a specific cloud provider. The role does not purge arbitrary dependencies; only the listed packages are targeted.

### Operational packages

The role installs a standard troubleshooting toolbox so incident response does not start by changing package state. Installed packages include `bind9-dnsutils`, `curl`, `exip`, `htop`, `iotop`, `jq`, `less`, `lsof`, `tcpdump`, `tmux`, `traceroute`, `tree`, `unzip`, and `wget`.

### Time

The timezone is pinned to `UTC` and the `chrony` NTP service is enabled and started. UTC everywhere keeps logs from regional workers correlating without timezone translation. The role expects stock Ubuntu 26.04 images where `chrony` is the default time synchronization service; it does not install or replace the time-sync stack.

### DNS

The role ensures `systemd-resolved` is enabled and running, links `/etc/resolv.conf` to the systemd stub resolver, and configures fallback DNS servers (`1.1.1.1` and `1.0.0.1`) in a drop-in file at `/etc/systemd/resolved.conf.d/60-ubuntu2604-fallback-dns.conf`. Fallback DNS is only consulted when no per-link servers are known, so DHCP-provided resolvers remain primary and internal zone resolution is preserved.

### MOTD

Dynamic MOTD entries under `/etc/update-motd.d` are removed, the static `/etc/motd` file is cleared, and the `motd-news.timer` is stopped, disabled, and masked. The dynamic MOTD framework remains installed but produces no output, keeping SSH logins quiet on container workers.

## Task tags

All tasks carry semantic tags so you can run or skip sections with `ansible-playbook --tags` or `--skip-tags`.

| Tag | Covers |
|-----|--------|
| `kernel` | Kernel modules, sysctls, PAM limits, transparent hugepages service |
| `network` | IPv6 sysctl policy |
| `ssh` | SSH hardening, drop-in config, and guardrails |
| `systemd` | System manager resource limits and cgroup accounting defaults |
| `swap` | Swap disable and `/etc/fstab` cleanup |
| `apt` | Mirror lists, sources list, and cache update |
| `upgrade` | Safe package upgrade, autoremove, and autoclean |
| `packages` | Package installs and removals across all sections |
| `unattended_upgrades` | Unattended upgrades config, reboot policy, needrestart, and timers |
| `logs` | Journald persistence, retention, and `/var/log` pressure controls |
| `firewall` | nftables service ownership, UFW masking, and iptables compatibility tools |
| `locale` | Locale generation and default locale setting |
| `time` | Timezone and chrony time synchronization |
| `dns` | systemd-resolved stub and fallback DNS configuration |
| `snap` | Snapd removal, guardrails, and reinstallation block |
| `motd` | MOTD cleanup and motd-news timer masking |

Example: run only APT and upgrade tasks:

```bash
ansible-playbook -i inventory.ini playbook.yml --tags "apt,upgrade"
```

## Related pages

- [Quickstart](../getting-started/quickstart.md) — Apply the role and verify results.
