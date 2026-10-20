# Kubernetes networking

Choose API and cluster network addresses before initialization:

```yaml
kubernetes_cluster_name: my-cluster
kubernetes_advertise_address: 203.0.113.10
kubernetes_pod_subnet: 10.244.0.0/16
kubernetes_service_subnet: 10.96.0.0/16
```

The API address defaults to the host's default IPv4 address. It controls the advertise address, endpoint, bind address, and certificate SAN; restrict access to TCP/6443.

The default pod CIDR matches Flannel v0.28.10. For another CIDR, set `kubernetes_flannel_manifest_url` to a manifest with a matching `net-conf.json` `Network`. The role does not rewrite the manifest or upgrade an existing Flannel installation.

## Constraints

- Cluster name, Kubernetes minor version, and both CIDRs are immutable and stored in `/etc/ansible/facts.d/kubernetes.fact`.
- Only the cluster name is reused automatically. Repeat custom version/CIDR overrides or retain them in inventory/playbooks.
- Existing clusters are not reinitialized. Back up and rebuild, or use a separate migration procedure, to change identity or CIDRs.
- Calico-to-Flannel migration is not automated. Flannel does not enforce NetworkPolicy.

[Configuration](../reference/configuration.md) · [Architecture](../concepts/architecture.md)
