# Requirements

System, software, and network requirements for `andreygubarev.com.kubernetes`.

## Control machine

| Requirement | Notes |
|---|---|
| ansible-core 2.20 or newer | For the included local playbook, the control machine is also the target host. |
| `community.general` collection | Installed with the collection or by `make deps` from a checkout. |

## Target host

| Requirement | Notes |
|---|---|
| Ubuntu 26.04 | The role fails before mutation on other releases. |
| amd64 or arm64 | Kubernetes upstream packages must be available for the architecture. |
| Root or sudo | Required for package installation, kernel settings, and kubeadm; add `-K` if sudo requires a password. |
| Existing kubeconfig user | Defaults to the invoking account in the local playbook, or the Ansible SSH user for remote roles; override `kubernetes_kubeconfig_user` if needed. |
| Stable API address | Defaults to the host default IPv4 address; override `kubernetes_advertise_address` on multi-interface hosts. |

## Network access

The target host needs outbound HTTPS access to:

- `https://pkgs.k8s.io` for Kubernetes packages
- `https://github.com` for Flannel and metrics-server manifests
- `https://registry.k8s.io` for Kubernetes control-plane and pause images
- `https://ghcr.io` for Flannel and Flannel CNI plugin images

## Installed by the role

- `apt-transport-https`
- `ca-certificates`
- `curl`
- `gnupg`
- `containerd`
- `containernetworking-plugins`
- `kubeadm`
- `kubectl`
- `kubelet`

## Related pages

- [Quickstart](../getting-started/quickstart.md)
- [Configuration](configuration.md)
