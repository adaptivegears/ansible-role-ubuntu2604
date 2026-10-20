# Kubernetes requirements

- Ubuntu 26.04 on amd64 or arm64; ansible-core ≥ 2.20.
- Root or sudo access; add `-K` if sudo requires a password.
- A stable API address and an existing kubeconfig owner account.
- `kubernetes_cluster_name` supplied on the first run.
- `community.general`, installed with the collection or by `make deps`.

The local playbook runs on the target host. For remote roles, set `ansible_user` or explicitly set `kubernetes_kubeconfig_user`.

## Network

Allow outbound access to Ubuntu APT repositories and HTTPS access to:

| Endpoint | Purpose |
|---|---|
| `pkgs.k8s.io` | Kubernetes packages |
| `github.com` | Flannel and metrics-server manifests |
| `registry.k8s.io` | Kubernetes images |
| `ghcr.io` | Flannel images |

Restrict access to API TCP/6443 externally; the role does not configure firewall rules.

Installed packages: `apt-transport-https`, `ca-certificates`, `curl`, `gnupg`, `containerd`, `containernetworking-plugins`, `kubeadm`, `kubectl`, and `kubelet`.

[Quickstart](../getting-started/quickstart.md) · [Configuration](configuration.md)
