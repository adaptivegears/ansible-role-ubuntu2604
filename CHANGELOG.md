# CHANGELOG

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versions follow [CalVer](https://calver.org/) (`YYYY.M.MICRO`).

## [2026.5.6] - 2026-05-30

### Highlights
This release makes SSH hardening safer and sequencing more robust by adding guardrails and a cloud-init wait barrier.

### New Features
- **SSH lockout guardrails**: Before disabling password authentication or root login, the role asserts that the Ansible user has an authorized_keys file and that root SSH remains reachable when connected as root
- **cloud-init wait barrier**: The role waits up to 30 minutes for cloud-init to complete before mutating the host, accepting completion-with-errors and warning when boot-time initialization issues remain

### Improvements
- **APT lock timeout**: Safe upgrades now wait up to 10 minutes for dpkg locks instead of failing when cloud-init or unattended upgrades hold the lock at boot

### Internal
- **Concise comments**: Rationale comments throughout tasks, ansible.cfg, and docs were tightened to reduce verbosity without losing intent
- **Role description**: Rephrased from "disposable container workers" to "container workloads"

## [2026.5.5] - 2026-05-28

### Highlights
This release adds SSH hardening, systemd manager density defaults, journald log pressure controls, nftables firewall ownership, and prerequisite assertions. APT mirror selection is safer, and more settings are exposed as user-configurable defaults.

### New Features
- **SSH hardening**: Priority drop-in (`00-ubuntu2604-hardening.conf`) pins a restricted algorithm set, disables password authentication, and limits forwarding; root login and TCP forwarding are configurable via `ubuntu2604_ssh_allow_root_login` and `ubuntu2604_ssh_allow_tcp_forwarding`
- **Systemd density defaults**: Manager drop-in sets `DefaultLimitNOFILE`, `DefaultLimitNPROC`, and `DefaultTasksMax` to `65536`, plus enables memory and task cgroup accounting so service-launched workloads inherit the same headroom as login sessions
- **Journald log pressure controls**: Persistent journals capped at 1 GB total, 128 MB per file, 30-day retention, with reserved free space on `/var/log` and `/run` so log bursts cannot crowd out packages or workload state
- **Firewall manager selection**: `nftables` is enabled as the host firewall manager, `ufw` is masked, and iptables-family compatibility commands are switched to the nft backend
- **Reboot-required reporting**: After safe upgrades, the role surfaces `/var/run/reboot-required` and the list of triggering packages without rebooting the host
- **Prerequisite assertions**: Role fails fast with a clear message when run on a non-Ubuntu 26.04 host or an unsupported architecture

### Improvements
- **APT mirror safety**: Canonical archives are now primary, with EC2 regional mirrors as fallback, avoiding stale-index sync races; arm64 hosts use the standard archive instead of `ports.ubuntu.com`
- **User-configurable defaults**: `ubuntu2604_locale`, `ubuntu2604_timezone`, and the new SSH toggles are now defined in `defaults/main.yml` instead of `vars/main.yml`
- **Expanded testinfra coverage**: New parametrized tests verify systemd manager settings, journald persistence, firewall state, SSH hardening, reboot markers, and APT mirror priorities

### Internal
- Added `ansible.cfg` with SSH connection multiplexing, pipelining, and retry tuning for faster playbook runs
- New task tags: `systemd`, `logs`, `firewall`, and `ssh`

## [2026.5.4] - 2026-05-27

### Highlights
This release adds operational troubleshooting packages, UTC time synchronization, systemd-resolved DNS fallback, and quiet MOTD handling. AWS integration now requires explicit opt-in instead of automatic platform detection.

### New Features
- **Operational packages**: Installs a standard troubleshooting toolbox (`htop`, `iotop`, `jq`, `tcpdump`, `tmux`, `bind9-dnsutils`, and others) so incident response does not start by changing package state
- **UTC timezone with chrony**: Pins the system timezone to UTC and ensures the `chrony` time synchronization service is active for predictable cross-region log correlation
- **systemd-resolved fallback DNS**: Configures `systemd-resolved` with Cloudflare fallback resolvers (`1.1.1.1`, `1.0.0.1`) that are only consulted when DHCP-supplied DNS is unavailable, preserving internal zone resolution
- **Quiet MOTD**: Removes dynamic MOTD entries, clears static `/etc/motd`, masks the `motd-news.timer`, and scrubs transient cache files for low-noise SSH logins on container workers

### Breaking Changes
- **AWS detection is now explicit**: The role no longer auto-detects EC2 via platform heuristics. Set `ubuntu2604_cloud: "aws"` to enable AWS-aware behavior such as regional APT mirror selection

### Improvements
- **Concise sysctl comments**: Rationale comments for kernel tuning settings were tightened to reduce redundancy without losing intent
- **Retained `overlay` module preload**: The role continues to force-load `overlay` so OverlayFS readiness is explicit for container runtimes that use overlay snapshotters
- **Expanded documentation**: Quickstart and configuration reference now cover task tag selectors and APT/unattended-upgrade behavior

### Internal
- New `aws` task tag for EC2 metadata gathering and regional mirror selection

## [2026.5.3] - 2026-05-26

### Highlights
This release adds deterministic APT source management with AWS regional mirror awareness, safe package upgrades, and explicit unattended security upgrade policies that block automatic reboots.

### New Features
- **AWS-aware APT mirror selection**: Detects EC2 instances via platform facts and IMDS, preferring regional `ec2.archive.ubuntu.com` mirrors with fallback to Canonical-operated endpoints; replaces cloud-init defaults with deterministic source lists
- **Safe APT upgrades**: Applies `safe` upgrades, `autoremove`, and `autoclean` during role runs so fresh VMs stay current without accepting disruptive dependency changes
- **Unattended security upgrades**: Explicitly enables periodic security updates while disabling automatic reboots, shutdown-time installs, and needrestart automatic service restarts; container workloads remain stable outside operator-controlled maintenance windows
- **Task tags**: All tasks tagged with semantic selectors (`kernel`, `swap`, `apt`, `locale`, `unattended_upgrades`, `upgrade`, `packages`) for selective execution

### Improvements
- **Expanded testinfra coverage**: New parametrized tests verify APT mirror lists, source file syntax, unattended-upgrade settings, needrestart policy, and APT maintenance timer state

### Internal
- Added `amazon.aws` collection dependency (`10.1.2`) for EC2 metadata fact gathering
- Removed unused `templates/.gitkeep` scaffolding

## [2026.5.2] - 2026-05-26

### Highlights
This release adds a comprehensive pytest-testinfra verification suite, user-facing documentation, and faster parallel test execution.

### New Features
- **Integration test suite**: `ubuntu2604/tests/test_ubuntu2604.py` verifies kernel modules, sysctl persistence, PAM limits, transparent hugepages, swap removal, and locale configuration using pytest-testinfra
- **Documentation site**: New `docs/` pages including a quickstart guide, configuration reference, and overview index

### Improvements
- **Parallel test execution**: `make test` runs testinfra checks across 8 workers with `pytest-xdist` for faster verification cycles
- **Makefile organization**: Variables renamed for clarity and separated by tool (Ansible vs. testinfra)

### Internal
- Replaced legacy Ansible role test scaffolding (`tests/test.yml`, `tests/inventory`) with the new pytest-based suite

## [2026.5.1] - 2026-05-26

### Highlights
Initial release of the `ubuntu2604` role for provisioning Ubuntu 26.04 VMs for container workloads. The role favors predictable networking, dense process scheduling, and automatic recovery over general-purpose desktop defaults.

### New Features
- **Container-optimized kernel tuning**: Loads `br_netfilter`, `nf_conntrack`, and `overlay` modules; applies 30+ sysctl parameters for bridge netfilter, IPv4/IPv6 forwarding, connection tracking, file descriptor limits, and VMA mapping
- **PAM limits**: Raises soft and hard `nofile` and `nproc` limits to 65536 so container-launched sessions can use the enlarged kernel ceilings
- **Transparent hugepages policy**: Installs a systemd one-shot service that sets THP to `madvise`, letting runtimes opt in without forcing global hugepages on latency-sensitive workloads
- **Swap disable**: Turns off active swap and scrubs swap entries from `/etc/fstab` to keep OOM behavior predictable and avoid container latency spikes
- **Locale enforcement**: Installs the `locales` package, generates a configurable UTF-8 locale, and sets it as the system default
- **Linting and dependency automation**: `Makefile` targets for `ansible-lint` and collection installation, run via `uvx` for reproducible tooling

### Internal
- Role metadata, handlers, and variable scaffolding established with production-grade `ansible-lint` configuration
