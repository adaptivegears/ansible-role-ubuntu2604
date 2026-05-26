# ubuntu_2604

Documentation for the `ubuntu_2604` Ansible role, which provisions Ubuntu 26.04 VMs as disposable container workers.

## What this role does

The role turns a fresh Ubuntu 26.04 VM into a host optimized for container workloads. It applies kernel tuning, disables swap, raises resource limits, and ensures a consistent UTF-8 locale so that container runtimes behave predictably across rebuilds.

## Audience

These docs are for operators and platform engineers who manage Ubuntu 26.04 VMs that run containers or Kubernetes workloads.

## Getting started

- [Quickstart](getting-started/quickstart.md) — Apply the role to a VM in minutes.

## Reference

- [Configuration](reference/configuration.md) — Variables, defaults, and customization options.

## Releases

- [Changelog](../../CHANGELOG.md) — Version history and notable changes.
