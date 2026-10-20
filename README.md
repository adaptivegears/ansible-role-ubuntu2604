# andreygubarev.com

Ansible roles and local playbooks for Ubuntu 26.04 infrastructure.

## Requirements

Ubuntu 26.04 on amd64 or arm64, ansible-core ≥ 2.20, and root or sudo access.

## Install or update

```bash
ansible-galaxy collection install andreygubarev.com --upgrade
```

## Run

Run on the machine to configure. No inventory or SSH connection is required; add `-K` if sudo requires a password.

```bash
ansible-playbook andreygubarev.com.ubuntu2604 -e ubuntu2604_hostname=worker-1
ansible-playbook andreygubarev.com.kubernetes -e kubernetes_cluster_name=my-cluster
```

| Role / playbook | Purpose | Documentation |
|---|---|---|
| `andreygubarev.com.ubuntu2604` | Container-host baseline | [Quickstart](docs/getting-started/quickstart.md) · [Configuration](docs/reference/configuration.md) |
| `andreygubarev.com.kubernetes` | Single-node kubeadm cluster | [Quickstart](docs/kubernetes/getting-started/quickstart.md) · [Configuration](docs/kubernetes/reference/configuration.md) |

The playbooks are independent. Kubernetes does not automatically apply the Ubuntu role.

- Ubuntu requires `ubuntu2604_hostname` once and remembers the complete validated configuration, including defaults. Future runs need no repeated overrides; supply a new value once to change a setting.
- Kubernetes requires `kubernetes_cluster_name` once, then reuses it from local facts. Renaming is rejected; other Kubernetes overrides still need to be supplied on each run or kept in inventory/playbooks.

**Ubuntu baseline:** requires SSH authorized keys, disables password authentication, removes all snap data, and regenerates SSH host keys on first configuration. Review the quickstart before use.

## Development

```bash
make deps     # Install the local collection and dependencies
make check    # Lint and syntax-check both playbooks
make build    # Build the collection artifact in dist/
make publish  # Check, build, and publish to Galaxy
make test     # Verify Ubuntu hosts from inventory.ini
```

For local Kubernetes verification:

```bash
make test ANSIBLE_ROLE_DIR=roles/kubernetes TESTINFRA_HOSTS=local://
```

## Publish

Obtain a [Galaxy API token](https://galaxy.ansible.com/ui/token/) with access to the `andreygubarev` namespace. Store it outside the repository in `~/.ansible/galaxy_token` with permissions `0600`:

```yaml
token: <your-galaxy-api-token>
```

Increment `version` in `galaxy.yml`, then run `make publish`. It publishes a fresh artifact for that version and waits for import validation. Published versions are immutable.

## Project

[Documentation](docs/index.md) · [Changelog](CHANGELOG.md) · [Source](https://github.com/andreygubarev/ansible-collection) · [Apache-2.0](LICENSE) · [NOTICE](NOTICE)
