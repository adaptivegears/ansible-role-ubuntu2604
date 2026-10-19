# Quickstart

Provision a single-node Kubernetes cluster on the Ubuntu 26.04 machine running Ansible.

## Prerequisites

- Ubuntu 26.04 on amd64 or arm64
- ansible-core 2.20 or newer installed on that host
- Root or sudo access; add `-K` if sudo requires a password
- A stable address for the Kubernetes API

The role works independently or on hosts already prepared by `andreygubarev.com.ubuntu2604`. It does not automatically apply the Ubuntu role.

## Install the collection

After the collection release containing Kubernetes is published:

```bash
ansible-galaxy collection install andreygubarev.com --upgrade
```

For development from a repository checkout, use `make deps` instead. It installs the local collection and its dependencies.

## Run the local playbook

No inventory or SSH connection is needed:

```bash
ansible-playbook andreygubarev.com.kubernetes
```

The API server advertises the host's default IPv4 address, and kubeconfig is copied to the invoking user's home directory. If either default is wrong, override it explicitly:

```bash
ansible-playbook andreygubarev.com.kubernetes \
  -e kubernetes_advertise_address=203.0.113.10 \
  -e kubernetes_kubeconfig_user=ubuntu
```

Review the [configuration reference](../reference/configuration.md) before changing cluster identity or networking. The Kubernetes version, cluster name, pod subnet, and service subnet are immutable after the first role run.

## Verify the cluster

On that host, run:

```bash
kubectl get nodes
kubectl get pods -A
```

If the node is `Ready` and the `kube-system` pods are running, the installation succeeded.

From a repository checkout, run production verification locally:

```bash
make test ANSIBLE_ROLE_DIR=roles/kubernetes TESTINFRA_HOSTS=local://
```

## Remote provisioning

To provision over SSH, use the role in your own playbook, for example `kubernetes.yml`:

```yaml
- name: Provision a single-node Kubernetes cluster
  hosts: kubernetes
  become: true
  roles:
    - andreygubarev.com.kubernetes
```

Provide an inventory with the SSH login user:

```ini
[kubernetes]
node1.example.com ansible_user=ubuntu
```

```bash
ansible-playbook -i inventory.ini kubernetes.yml
make test ANSIBLE_ROLE_DIR=roles/kubernetes
```
