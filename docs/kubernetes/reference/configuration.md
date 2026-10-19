# Configuration

Default variables are defined in `roles/kubernetes/defaults/main.yml`.

## Variables

### `kubernetes_version`

- **Default**: `"1.37"`
- Kubernetes minor version used for the upstream APT repository URL.
- Immutable after first role run. The role stores the first value in `/etc/ansible/facts.d/kubernetes.fact` and refuses to proceed if a later run requests a different value.

### `kubernetes_cluster_name`

- **Default**: `"kubernetes"`
- Cluster name passed to kubeadm.
- Immutable after first role run. The role stores the first value in `/etc/ansible/facts.d/kubernetes.fact` and refuses to proceed if a later run requests a different value.

### `kubernetes_advertise_address`

- **Default**: `{{ ansible_facts.get('default_ipv4', {}).get('address', '') }}`
- Address used for kubeadm `advertiseAddress`, `controlPlaneEndpoint`, API server certificate SANs, and API server bind address.
- Set this explicitly when the host has multiple interfaces or when direct access should use a public or specific private address.

### `kubernetes_pod_subnet`

- **Default**: `"10.244.0.0/16"`
- Pod CIDR passed to kubeadm. The default matches the upstream Flannel manifest; a custom CIDR requires a matching Flannel manifest.
- Immutable after first role run. The role stores the first value in `/etc/ansible/facts.d/kubernetes.fact` and refuses to proceed if a later run requests a different value.

### `kubernetes_service_subnet`

- **Default**: `"10.96.0.0/16"`
- Service CIDR passed to kubeadm.
- Immutable after first role run. The role stores the first value in `/etc/ansible/facts.d/kubernetes.fact` and refuses to proceed if a later run requests a different value.

### `kubernetes_kubeconfig_user`

- **Default**: `{{ ansible_user | default(ansible_ssh_user | default('')) }}`
- Existing local user that receives kubeconfig at `<home>/.kube/config`.
- The included local playbook sets `ansible_user` to the invoking account before escalating role tasks, so kubeconfig is not assigned to root merely because sudo is used.
- The role does not create this user.

### `kubernetes_apiserver_gogc`

- **Default**: `"50"`
- `GOGC` for kube-apiserver, rendered into kubeadm `apiServer.extraEnvs` so the setting survives `kubeadm upgrade`. The default halves the Go garbage collector's headroom compared to the upstream `GOGC=100`, trading a little CPU for substantially lower resident memory — on a single-node control plane most of the API server's heap is static CRD schema machinery that the default GC ratio doubles. Set to `""` to keep the upstream default.

### `kubernetes_apiserver_gomemlimit`

- **Default**: `""`
- Optional `GOMEMLIMIT` hard memory ceiling for kube-apiserver, for example `"1536MiB"`, rendered into kubeadm `apiServer.extraEnvs`. Leave empty until the effect of `kubernetes_apiserver_gogc` alone has been measured: a too-tight ceiling makes the Go runtime thrash the garbage collector.

### `kubernetes_flannel_manifest_url`

- **Default**: `https://github.com/flannel-io/flannel/releases/download/v0.28.10/kube-flannel.yml`
- Manifest applied when the Flannel DaemonSet is absent. Existing installations are not upgraded automatically.
- Override with a pinned release URL or a custom manifest whose network matches `kubernetes_pod_subnet`.

### `kubernetes_metrics_server_version`

- **Default**: `"v0.9.0"`
- metrics-server release installed from that tag's `components.yaml`. The role applies the manifest on first run and whenever the deployed image tag differs from this pin, which is also how metrics-server upgrades are rolled out. The `--kubelet-insecure-tls` patch is re-applied after every install.

## Example

```yaml
---
kubernetes_version: "1.37"
kubernetes_advertise_address: "203.0.113.10"
kubernetes_kubeconfig_user: "ubuntu"
```

## Notes

Changing kubeadm identity, Kubernetes minor version, or networking values after the first successful run does not reinitialize the cluster. The Kubernetes version, cluster name, pod subnet, and service subnet are additionally guarded by a persistent local fact in `/etc/ansible/facts.d/kubernetes.fact`; back up and rebuild the cluster, or use a future explicit upgrade workflow, if you need to change them after first bootstrap.

Non-identity control-plane settings — such as the API server GC variables — do converge on an initialized cluster: when `/etc/kubernetes/kubeadm-config.yaml` changes, the role uploads the configuration to the `kubeadm-config` ConfigMap and regenerates the control-plane static pod manifests, which briefly restarts the API server. See [Architecture](../concepts/architecture.md) for the convergence model.
