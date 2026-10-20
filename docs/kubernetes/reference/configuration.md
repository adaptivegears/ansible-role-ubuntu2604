# Kubernetes configuration

## Variables

| Variable | Default | Effect |
|---|---|---|
| `kubernetes_cluster_name` | Required once | Immutable cluster name; reused from local facts |
| `kubernetes_version` | `1.37` | Immutable minor version for the upstream APT repository |
| `kubernetes_advertise_address` | Default IPv4 address | API advertise/bind address, endpoint, certificate SAN |
| `kubernetes_pod_subnet` | `10.244.0.0/16` | Immutable pod CIDR; must match the Flannel manifest |
| `kubernetes_service_subnet` | `10.96.0.0/16` | Immutable service CIDR |
| `kubernetes_kubeconfig_user` | Ansible user | Existing account receiving `~/.kube/config`; invoking account for local execution |
| `kubernetes_apiserver_gogc` | `50` | API server Go GC target; empty string uses upstream default |
| `kubernetes_apiserver_gomemlimit` | Empty | Optional API server Go memory limit, e.g. `1536MiB` |
| `kubernetes_flannel_manifest_url` | [Flannel v0.28.10 manifest](https://github.com/flannel-io/flannel/releases/download/v0.28.10/kube-flannel.yml) | Applied only when Flannel is absent |
| `kubernetes_metrics_server_version` | `v0.9.0` | Release applied on installation or image-version drift |

See [defaults](../../../roles/kubernetes/defaults/main.yml) for exact expressions. An overly restrictive `GOMEMLIMIT` can cause GC thrashing.

## `kubernetes_cluster_name`

No role default or interactive prompt. The first run requires an explicit non-empty string and fails before mutation if it is missing.

Later runs reuse `/etc/ansible/facts.d/kubernetes.fact`, available as `ansible_facts['ansible_local']['kubernetes']['cluster']['cluster_name']`. Names stored by earlier versions remain valid. Explicit empty/non-string values or a different name are rejected; the stored identity is not overwritten.

Only the name is reused automatically. Keep all other overrides in inventory/playbooks or supply them on every run.

## Immutable identity

Cluster name, Kubernetes minor version, pod CIDR, and service CIDR are recorded on the first run and checked before mutation. Changing them requires a rebuild or a separate upgrade/migration procedure; this role provides neither.

Non-identity control-plane changes regenerate kubeadm manifests and briefly restart the API server. The configuration uses the installed kubeadm version, not a network-resolved version label. See [architecture](../concepts/architecture.md).

## Example

```yaml
kubernetes_cluster_name: my-cluster
kubernetes_advertise_address: 203.0.113.10
kubernetes_kubeconfig_user: ubuntu
```

[Quickstart](../getting-started/quickstart.md) · [Networking](../guides/customize-networking.md)
