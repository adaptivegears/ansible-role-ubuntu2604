# andreygubarev.com

Personal Ansible collection of public infrastructure roles and playbooks.

## Requirements

- ansible-core **2.20** or newer
- Target requirements are documented for each role

## Install from Ansible Galaxy

After the first release is published:

```bash
ansible-galaxy collection install andreygubarev.com
```

Source repository: [andreygubarev/ansible-collection](https://github.com/andreygubarev/ansible-collection).

## Roles and playbooks

| Role / playbook | Purpose |
|-----------------|---------|
| `andreygubarev.com.ubuntu2604` | Provision Ubuntu 26.04 VMs as container-worker hosts |
| `andreygubarev.com.kubernetes` | Provision a single-node kubeadm cluster with containerd, Flannel, and metrics-server |

Run either included playbook on the Ubuntu 26.04 machine you want to configure. Both use a local connection; no inventory or SSH connection is needed:

```bash
ansible-playbook andreygubarev.com.ubuntu2604
ansible-playbook andreygubarev.com.kubernetes
```

The playbooks are independent: Kubernetes does not automatically apply the Ubuntu role. Its kubeconfig defaults to the invoking user's home directory. See the [Kubernetes quickstart](docs/kubernetes/getting-started/quickstart.md).

Use root or a user with sudo privileges; add `-K` if sudo requires a password. The Ubuntu role additionally requires SSH authorized keys and explicit `-e ubuntu2604_ssh_allow_root_login=true` when running as root, because it hardens SSH.

For remote provisioning over SSH, use the role in your own playbook:

```yaml
- name: Provision container workers
  hosts: workers
  roles:
    - andreygubarev.com.ubuntu2604
```

Documentation starts at [`docs/index.md`](docs/index.md).

## Development

From a checkout of this repository:

```bash
make deps   # Install this collection and its dependencies locally
make check  # Lint the collection and syntax-check both installed playbooks
make build  # Build dist/andreygubarev-com-2026.10.2.tar.gz
make publish # Check, build, and publish the current version to Ansible Galaxy
make test   # Verify deployed hosts using inventory.ini
```

Roles live in `roles/`, and collection playbooks live in `playbooks/`. `make test` verifies the Ubuntu role by default; use `make test ANSIBLE_ROLE_DIR=roles/kubernetes` for Kubernetes, and add `TESTINFRA_HOSTS=local://` to verify the local machine.

## Publish to Ansible Galaxy

1. Sign in to [Ansible Galaxy](https://galaxy.ansible.com/) and ensure your account has permission to publish under the `andreygubarev` namespace. A GitHub repository alone does not grant Galaxy namespace access.
2. Obtain an API token from [Galaxy API token management](https://galaxy.ansible.com/ui/token/). Store it outside the repository in `~/.ansible/galaxy_token` with permissions `0600`:

   ```yaml
   token: <your-galaxy-api-token>
   ```

3. Check `version` in `galaxy.yml` before publishing. Every published version is immutable; increment it for subsequent releases, then run:

   ```bash
   make publish
   ```

   This runs `make check`, builds a fresh tarball, and publishes the artifact for the version read from `galaxy.yml`. Existing artifacts for other versions are not selected. Authentication uses the configured Galaxy token, and publishing waits for Galaxy's import validation to finish.

4. After the import succeeds, install with `ansible-galaxy collection install andreygubarev.com` and run either included playbook on the target machine.

## License

The collection and both roles are licensed under [Apache-2.0](LICENSE). See [NOTICE](NOTICE) for the copyright notice.
