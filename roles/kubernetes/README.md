# andreygubarev.com.kubernetes

Single-node kubeadm cluster on Ubuntu 26.04 with containerd, Flannel, metrics-server, and the k9s terminal UI. Requires ansible-core ≥ 2.20 and root or sudo access.

```bash
ansible-playbook andreygubarev.com.kubernetes -e kubernetes_cluster_name=my-cluster
```

Runs locally; add `-K` if sudo requires a password. Cluster name is required once. All public settings remain in `defaults/main.yml`; the complete validated configuration is saved before application and reused on subsequent runs. Initial API address and kubeconfig owner are remembered too. Conflicting identity changes are rejected. The Ubuntu baseline is not applied automatically.

k9s defaults to `0.51.0`, installed system-wide from the official amd64/arm64 Debian package after SHA256 verification. `kubernetes_k9s_version` overrides the exact version; it is saved with the other settings. Run `k9s` as the kubeconfig owner to use their existing cluster access. The `k9s` tag supports selective installation on an already configured host.

[Task index](tasks/main.yml) uses explicit static imports of numbered `XX-section.yml` files. Preflight and configuration use `always`, including selective runs.

[Quickstart and remote usage](../../docs/kubernetes/getting-started/quickstart.md) · [Configuration](../../docs/kubernetes/reference/configuration.md) · [Architecture](../../docs/kubernetes/concepts/architecture.md)

[Apache-2.0](../../LICENSE). Originally developed by Adaptive Gears in [ansible-role-kubernetes](https://github.com/adaptivegears/ansible-role-kubernetes); packaging, playbook, documentation, and source breadcrumbs adapted for this collection.
