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
- Kubernetes requires `kubernetes_cluster_name` once and remembers the complete configuration, including the initial API address and kubeconfig owner. Cluster name, Kubernetes minor version, and cluster CIDRs remain immutable.

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

Obtain a [Galaxy API token](https://galaxy.ansible.com/ui/token/) with access to the `andreygubarev` namespace.

### GitHub Actions

Add the token as the repository Actions secret `GALAXY_API_KEY`. The workflow in `.github/workflows/ci.yml` publishes to Galaxy when a numeric version tag is pushed, without a `v` prefix.

Update `version` in `galaxy.yml` and `CHANGELOG.md`, commit the release, then tag that commit and push:

```bash
git tag 2026.10.6
git push origin HEAD
git push origin 2026.10.6
```

The tag must exactly match `version` in `galaxy.yml`. The workflow runs `make publish`, which checks the collection, builds a fresh artifact, and waits for Galaxy import validation. Published versions are immutable; rerunning a successful publication does not overwrite them.

### Local publishing

Store the token outside the repository in `~/.ansible/galaxy_token` with permissions `0600`:

```yaml
token: <your-galaxy-api-token>
```

Increment `version` in `galaxy.yml`, then run `make publish`.

## Project

[Documentation](docs/index.md) · [Changelog](CHANGELOG.md) · [Source](https://github.com/andreygubarev/ansible-collection) · [Apache-2.0](LICENSE) · [NOTICE](NOTICE)
