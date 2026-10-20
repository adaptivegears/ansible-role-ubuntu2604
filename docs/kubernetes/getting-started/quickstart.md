# Kubernetes quickstart

## Requirements

Ubuntu 26.04 on amd64 or arm64, ansible-core ≥ 2.20, root or sudo access, and a stable API address. See [network requirements](../reference/requirements.md).

## Run locally

```bash
ansible-galaxy collection install andreygubarev.com --upgrade
ansible-playbook andreygubarev.com.kubernetes -e kubernetes_cluster_name=my-cluster
```

No inventory or SSH transport is required. Add `-K` if sudo requires a password. The Ubuntu baseline role is not applied automatically.

A non-empty cluster name is required on the first run; there is no prompt. Later runs reuse the saved name:

```bash
ansible-playbook andreygubarev.com.kubernetes
```

Renaming is rejected before changes. Other overrides, including custom Kubernetes versions and CIDRs, must still be supplied on each run or stored in inventory/playbooks.

The API uses the default IPv4 address; kubeconfig is copied to the invoking user's home directory. Override either explicitly if needed:

```bash
ansible-playbook andreygubarev.com.kubernetes \
  -e kubernetes_cluster_name=my-cluster \
  -e kubernetes_advertise_address=203.0.113.10 \
  -e kubernetes_kubeconfig_user=ubuntu
```

Choose the node hostname before initialization. Cluster name, Kubernetes minor version, and cluster CIDRs are immutable. Flannel does not enforce NetworkPolicy; metrics-server accepts self-signed kubelet certificates. Review [configuration](../reference/configuration.md) and [architecture](../concepts/architecture.md) before deployment.

## Verify

```bash
kubectl get nodes
kubectl get pods -A
```

From a repository checkout on the configured host:

```bash
make test ANSIBLE_ROLE_DIR=roles/kubernetes TESTINFRA_HOSTS=local://
```

## Remote provisioning

Use the role in your own `kubernetes.yml`:

```yaml
- name: Configure a single-node cluster
  hosts: kubernetes
  become: true
  roles:
    - andreygubarev.com.kubernetes
```

Set the SSH login user in inventory, for example `node1 ansible_user=ubuntu`, then run:

```bash
ansible-playbook -i inventory.ini kubernetes.yml -e kubernetes_cluster_name=my-cluster
```
