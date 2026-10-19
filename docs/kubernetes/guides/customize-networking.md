# Customize networking

Change the Kubernetes API advertise address or cluster CIDRs before the first successful kubeadm initialization.

## API advertise address

By default, the role uses the host's default IPv4 address:

```yaml
kubernetes_advertise_address: "{{ ansible_facts.get('default_ipv4', {}).get('address', '') }}"
```

Set it explicitly when direct access should use a specific address:

```yaml
kubernetes_advertise_address: "203.0.113.10"
```

The address is used for kubeadm `advertiseAddress`, `controlPlaneEndpoint`, the API server bind address, and the API server certificate SANs.

## Pod and service CIDRs

Defaults:

```yaml
kubernetes_pod_subnet: "10.244.0.0/16"
kubernetes_service_subnet: "10.96.0.0/16"
```

The default pod subnet matches the upstream Flannel manifest. For a custom `kubernetes_pod_subnet`, also set `kubernetes_flannel_manifest_url` to a manifest with a matching `net-conf.json` `Network` value. The role does not rewrite the Flannel manifest.

## Immutable subnet facts

The role stores the first requested Kubernetes version, cluster name, pod subnet, and service subnet in `/etc/ansible/facts.d/kubernetes.fact`:

```ini
[cluster]
cluster_name=kubernetes
kubernetes_version=1.37
pod_subnet=10.244.0.0/16
service_subnet=10.96.0.0/16
```

Ansible loads this file as `ansible_local.kubernetes.cluster`. On later runs, the role validates the requested values against the stored facts before proceeding. This prevents a playbook variable change from silently diverging from the already-initialized kubeadm cluster.

## Reinitialization warning

The role skips `kubeadm init` once `/etc/kubernetes/admin.conf` exists. Changing these variables after initialization does not rewrite the existing cluster. Back up workloads and rebuild the node if you need to change cluster networking after bootstrap.

The role does not migrate an existing Calico cluster to Flannel or remove Calico resources and host CNI configuration. Do not run it against a Calico cluster without a separately planned migration or rebuild. Flannel alone does not enforce Kubernetes NetworkPolicy; policies that depended on Calico will no longer provide isolation.
