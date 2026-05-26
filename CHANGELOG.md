# CHANGELOG

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versions follow [CalVer](https://calver.org/) (`YYYY.M.MICRO`).

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
