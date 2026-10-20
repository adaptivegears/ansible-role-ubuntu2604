# Kubernetes architecture

## Topology

One Ubuntu 26.04 node runs the control plane, etcd, kubelet, containerd, and workloads. The control-plane taint is removed to allow workload scheduling.

Containerd uses systemd cgroups, `io.containerd.runc.v2`, and pause image `registry.k8s.io/pause:3.10.2`. Kubeconfig is copied to an existing operator account; no account is created.

k9s is installed system-wide from the official, SHA256-verified Debian package for the host architecture. It uses the operator's existing kubeconfig; no additional credentials or cluster resources are created.

The node name defaults to the OS hostname at initialization. Set it beforehand; changing a running node's hostname is not a supported rename procedure.

## Configuration lifecycle

- `/etc/kubernetes/admin.conf` marks initialization; full `kubeadm init` bootstrap is skipped when it exists.
- `/etc/kubernetes/kubeadm-config.yaml` is rendered on every run using the installed kubeadm version.
- Non-identity changes are uploaded to the `kubeadm-config` ConfigMap, followed by static-manifest regeneration and a readiness check. Expect a brief API outage.
- All public settings are validated and saved before application. Subsequent runs reuse the full snapshot, including defaults, API address, and kubeconfig owner.
- Cluster name, Kubernetes minor version, and cluster CIDRs are immutable; conflicting overrides are rejected before facts are written. Legacy INI facts retain the same `cluster` namespace when converted to JSON.
- API server `GOGC=50` reduces GC headroom; optional `GOMEMLIMIT` requires workload-specific tuning.

## Security and networking

- The API binds to `kubernetes_advertise_address`. Restrict TCP/6443 with external or host firewall policy.
- New clusters set kube-proxy `conntrack.maxPerCore=0`, preserving the host's `nf_conntrack_max` rather than overwriting the Ubuntu baseline. Existing clusters' kube-proxy configuration is not migrated automatically.
- Flannel provides VXLAN networking, not NetworkPolicy enforcement. It is installed only when absent; existing Flannel is not upgraded automatically.
- Existing Calico clusters are not migrated or cleaned up. Plan a separate migration or rebuild.
- metrics-server is pinned and reconciled on image-version drift. It uses `--kubelet-insecure-tls` for self-signed kubelet certificates; use a separate TLS hardening procedure where verified serving certificates are required.

[Configuration](../reference/configuration.md) · [Networking](../guides/customize-networking.md)
