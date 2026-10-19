# andreygubarev.com.kubernetes

This documentation covers the `andreygubarev.com.kubernetes` role and local playbook. The role provisions a single-node kubeadm cluster on Ubuntu 26.04.

## What it does

- Prepares host kernel, swap, and container runtime settings required by Kubernetes
- Installs containerd, kubeadm, kubelet, and kubectl
- Initializes a single-node control plane and converges control-plane configuration on later runs
- Bounds kube-apiserver memory by halving its Go GC headroom (`GOGC=50`)
- Installs Flannel for pod networking (without NetworkPolicy enforcement)
- Installs metrics-server for resource metrics
- Copies kubeconfig to an existing local operator account

## Recommended first steps

Start with the [Quickstart](getting-started/quickstart.md), then review the [Configuration reference](reference/configuration.md) before changing defaults.

## Documentation sections

### Getting started

- [Quickstart](getting-started/quickstart.md) — Provision a first single-node cluster

### Guides

- [Customize networking](guides/customize-networking.md) — Choose API and cluster network addresses

### Concepts

- [Architecture](concepts/architecture.md) — Single-node design and trade-offs

### Operations

- [Known log noise](operations/known-log-noise.md) — Benign log patterns on a healthy cluster and how to tell them from real failures

### Reference

- [Configuration](reference/configuration.md) — Variables and defaults
- [Requirements](reference/requirements.md) — Control machine, target host, and network requirements

## Support

- Source code and issues: [github.com/andreygubarev/ansible-collection](https://github.com/andreygubarev/ansible-collection)
