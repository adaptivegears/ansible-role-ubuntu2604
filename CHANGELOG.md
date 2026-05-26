# CHANGELOG

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versions follow [CalVer](https://calver.org/) (`YYYY.M.MICRO`).

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
- **Integration test suite**: `ubuntu_2604/tests/test_ubuntu_2604.py` verifies kernel modules, sysctl persistence, PAM limits, transparent hugepages, swap removal, and locale configuration using pytest-testinfra
- **Documentation site**: New `docs/` pages including a quickstart guide, configuration reference, and overview index

### Improvements
- **Parallel test execution**: `make test` runs testinfra checks across 8 workers with `pytest-xdist` for faster verification cycles
- **Makefile organization**: Variables renamed for clarity and separated by tool (Ansible vs. testinfra)

### Internal
- Replaced legacy Ansible role test scaffolding (`tests/test.yml`, `tests/inventory`) with the new pytest-based suite

## [2026.5.1] - 2026-05-26

### Highlights
Initial release of the `ubuntu_2604` role for provisioning Ubuntu 26.04 VMs as disposable container workers. The role favors predictable networking, dense process scheduling, and automatic recovery over general-purpose desktop defaults.

### New Features
- **Container-optimized kernel tuning**: Loads `br_netfilter`, `nf_conntrack`, and `overlay` modules; applies 30+ sysctl parameters for bridge netfilter, IPv4/IPv6 forwarding, connection tracking, file descriptor limits, and VMA mapping
- **PAM limits**: Raises soft and hard `nofile` and `nproc` limits to 65536 so container-launched sessions can use the enlarged kernel ceilings
- **Transparent hugepages policy**: Installs a systemd one-shot service that sets THP to `madvise`, letting runtimes opt in without forcing global hugepages on latency-sensitive workloads
- **Swap disable**: Turns off active swap and scrubs swap entries from `/etc/fstab` to keep OOM behavior predictable and avoid container latency spikes
- **Locale enforcement**: Installs the `locales` package, generates a configurable UTF-8 locale, and sets it as the system default
- **Linting and dependency automation**: `Makefile` targets for `ansible-lint` and collection installation, run via `uvx` for reproducible tooling

### Internal
- Role metadata, handlers, and variable scaffolding established with production-grade `ansible-lint` configuration
