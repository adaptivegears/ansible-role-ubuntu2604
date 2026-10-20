# andreygubarev.com.kubernetes

Provision a single-node Kubernetes cluster on Ubuntu 26.04, using containerd, kubeadm, Flannel, and metrics-server.

## Requirements

- ansible-core 2.20 or newer
- Ubuntu 26.04 on amd64 or arm64
- Root or sudo access
- `community.general` (installed as a collection dependency)

## Local playbook

```bash
ansible-playbook andreygubarev.com.kubernetes -e kubernetes_cluster_name=my-cluster
```

A non-empty cluster name is mandatory on the first run, with no interactive prompt. Later runs reuse the name from `/etc/ansible/facts.d/kubernetes.fact` without repeating the variable. An explicit different name is rejected before mutation; custom version and subnet overrides still need to be repeated.

The playbook targets localhost without inventory or SSH. Kubeconfig is copied to the invoking user's home directory, even when role tasks use sudo. Add `-K` if sudo requires a password.

The Kubernetes API advertises the host's default IPv4 address. Override `kubernetes_advertise_address` or `kubernetes_kubeconfig_user` when those defaults are not correct for your host.

## Remote role example

```yaml
---
- name: Provision a single-node Kubernetes cluster
  hosts: kubernetes
  become: true
  vars:
    kubernetes_cluster_name: my-cluster
  roles:
    - andreygubarev.com.kubernetes
```

Set `ansible_user` in inventory or set `kubernetes_kubeconfig_user` explicitly. The role does not require or automatically apply `andreygubarev.com.ubuntu2604`.

See [defaults](defaults/main.yml), the [quickstart](../../docs/kubernetes/getting-started/quickstart.md), and the [configuration reference](../../docs/kubernetes/reference/configuration.md).

## License and origin

[Apache-2.0](../../LICENSE). Originally developed by Adaptive Gears in [ansible-role-kubernetes](https://github.com/adaptivegears/ansible-role-kubernetes); packaging, playbook, documentation, and source breadcrumbs have been adapted for this collection.
