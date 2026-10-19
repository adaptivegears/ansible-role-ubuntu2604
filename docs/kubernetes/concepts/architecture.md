# Architecture

`andreygubarev.com.kubernetes` builds a single-node kubeadm cluster on Ubuntu 26.04.

## Single-node control plane

The host runs the Kubernetes control plane and user workloads on the same node:

- kube-apiserver
- kube-controller-manager
- kube-scheduler
- etcd
- kubelet
- containerd

The role removes the standard control-plane taint because there are no worker nodes in this design.

## Declarative control-plane configuration

`/etc/kubernetes/kubeadm-config.yaml` is written on every run and is the source of truth for control-plane configuration. The first run feeds it to `kubeadm init` exactly once; the admin kubeconfig is the initialization marker because re-running `kubeadm init` over an existing control plane can destroy cluster state.

When the file changes on an initialized cluster, the role converges the running control plane through kubeadm's reconfigure flow: it uploads the configuration to the `kubeadm-config` ConfigMap — so `kubeadm upgrade` preserves the settings — and regenerates the control-plane static pod manifests with `kubeadm init phase control-plane all`, then waits until the API server answers `/readyz` again. Regeneration briefly restarts the API server; on a single node that is a short API outage while workloads keep running. Static pod manifests are never edited by hand.

`kubernetesVersion` in the file is pinned to the installed kubeadm binary so config uploads and manifest regeneration never resolve a release label over the network and never generate manifests at a version other than the cluster's.

kube-apiserver runs with `GOGC=50` (`kubernetes_apiserver_gogc`) by default. On a small cluster the dominant, structural part of the API server's heap is CRD schema machinery, and the upstream `GOGC=100` keeps roughly as much reclaimable GC headroom on top of it as the live heap itself. Halving the GC ratio trades a little CPU for substantially lower resident memory. `kubernetes_apiserver_gomemlimit` can add a hard memory ceiling once the GOGC effect has been measured.

## Direct API access

The API server advertises `kubernetes_advertise_address`. By default this is the host's default IPv4 address from Ansible facts. Set it explicitly when the host has multiple interfaces or when the API should bind to a specific public or private address.

The role does not configure a firewall. If the address is publicly reachable, protect TCP/6443 with network policy, host firewall policy, or upstream security groups.

## Existing operator user

The role does not create an `admin` user. It copies kubeconfig to `kubernetes_kubeconfig_user`, which defaults to the Ansible user (the invoking account with the included local playbook). This keeps the role usable on hosts prepared by other base roles without coupling Kubernetes to one account name.

## Container runtime

Containerd is configured with:

- runtime `io.containerd.runc.v2`
- systemd cgroups
- pause image `registry.k8s.io/pause:3.10.2`

Systemd cgroups keep kubelet and containerd aligned with Ubuntu's cgroup hierarchy.

## CNI and metrics

The role installs Flannel from `kubernetes_flannel_manifest_url` when the `kube-flannel-ds` DaemonSet is absent. The default URL is pinned to Flannel `v0.28.10`; existing installations are not automatically upgraded. The upstream manifest uses VXLAN and the role's default pod subnet, `10.244.0.0/16`. A custom pod subnet requires a matching Flannel manifest. kube-proxy is unchanged.

Flannel alone does not enforce Kubernetes NetworkPolicy. Calico-specific policies and observability are no longer managed by the role. Existing Calico clusters require a separately planned migration or rebuild before using this role; it does not remove the old CNI or migrate workloads automatically. See [Customize networking](../guides/customize-networking.md).

metrics-server is installed from the release manifest pinned by `kubernetes_metrics_server_version` and re-applied on version drift. The deployment is patched with `--kubelet-insecure-tls` because a simple kubeadm single-node cluster uses self-signed kubelet serving certificates. This is convenient for private/small clusters, but production clusters with proper kubelet serving certificates should remove that trade-off.
