# ubuntu_2604

Documentation for the `ubuntu_2604` Ansible role, which provisions Ubuntu 26.04 VMs as disposable container workers.

## What this role does

The role turns a fresh Ubuntu 26.04 VM into a host optimized for container workloads. It applies kernel tuning, disables swap, raises resource limits, ensures a consistent UTF-8 locale, and manages APT sources and upgrades so that container runtimes behave predictably across rebuilds.

The role also takes ownership of APT source management with AWS-aware regional mirror selection (requires explicit opt-in), applies safe package upgrades during provisioning, enables unattended security upgrades while blocking automatic reboots and unplanned service restarts, installs a standard troubleshooting toolbox, pins the timezone to UTC with active NTP sync, configures DNS fallback resolvers, and suppresses login noise on container workers.

## Audience

These docs are for operators and platform engineers who manage Ubuntu 26.04 VMs that run containers or Kubernetes workloads.

## Getting started

- [Quickstart](getting-started/quickstart.md) — Apply the role to a VM in minutes.

## Reference

- [Configuration](reference/configuration.md) — Variables, defaults, and customization options.

## Releases

- [Changelog](../../CHANGELOG.md) — Version history and notable changes.
