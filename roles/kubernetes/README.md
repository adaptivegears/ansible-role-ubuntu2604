# andreygubarev.com.kubernetes

Single-node kubeadm cluster on Ubuntu 26.04 with containerd, Flannel, and metrics-server. Requires ansible-core ≥ 2.20 and root or sudo access.

```bash
ansible-playbook andreygubarev.com.kubernetes -e kubernetes_cluster_name=my-cluster
```

Runs locally; add `-K` if sudo requires a password. Cluster name is required once, then reused from local facts. Other overrides must be supplied on subsequent runs. Kubeconfig defaults to the invoking user's home directory. The Ubuntu baseline is not applied automatically.

[Quickstart and remote usage](../../docs/kubernetes/getting-started/quickstart.md) · [Configuration](../../docs/kubernetes/reference/configuration.md) · [Architecture](../../docs/kubernetes/concepts/architecture.md)

[Apache-2.0](../../LICENSE). Originally developed by Adaptive Gears in [ansible-role-kubernetes](https://github.com/adaptivegears/ansible-role-kubernetes); packaging, playbook, documentation, and source breadcrumbs adapted for this collection.
