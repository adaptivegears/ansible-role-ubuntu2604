# andreygubarev.com

Personal Ansible collection of public infrastructure roles and playbooks.

The collection includes two independent roles and local playbooks:

- `andreygubarev.com.ubuntu2604` — Prepare Ubuntu 26.04 VMs for container workloads.
- `andreygubarev.com.kubernetes` — Provision a single-node kubeadm cluster; see the [Kubernetes documentation](kubernetes/index.md).

## Ubuntu 26.04 role

The role turns a fresh Ubuntu 26.04 VM into a host optimized for container workloads. It applies kernel and systemd tuning, disables swap and IPv6 by default, raises resource limits, ensures a consistent UTF-8 locale, and manages APT sources and upgrades so that container runtimes behave predictably across rebuilds.

The role also takes ownership of APT source management with direct provider-neutral Canonical endpoints, applies safe package upgrades during provisioning with reboot-required reporting, enables unattended security upgrades while blocking automatic reboots and unplanned service restarts, controls journald retention and `/var/log` pressure, makes `nftables` the host firewall manager, installs a standard troubleshooting toolbox, pins the timezone to UTC with active NTP sync, configures DNS fallback resolvers, suppresses login noise on container workers, and hardens SSH with guardrails that prevent accidental lockout.

## Audience

These docs are for operators and platform engineers who manage Ubuntu 26.04 VMs that run containers or Kubernetes workloads.

## Getting started

- [Ubuntu quickstart](getting-started/quickstart.md) — Prepare a VM for container workloads.
- [Kubernetes quickstart](kubernetes/getting-started/quickstart.md) — Provision a single-node cluster locally.

## Reference

- [Configuration](reference/configuration.md) — Variables, defaults, and customization options.

## Releases

- [Changelog](../CHANGELOG.md) — Version history and notable changes.
