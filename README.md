# andreygubarev.com

Personal Ansible collection of public infrastructure roles and playbooks.

## Requirements

- ansible-core **2.20** or newer
- Target requirements are documented for each role

## Install from Git

```bash
ansible-galaxy collection install git+https://github.com/adaptivegears/ansible-role-ubuntu2604.git
```

The Git repository name does not affect the collection name. No Galaxy publication is required. To pin a revision, append `,<tag-or-commit>` to the Git URL.

## Roles and playbooks

| Role / playbook | Purpose |
|-----------------|---------|
| `andreygubarev.com.ubuntu2604` | Provision Ubuntu 26.04 VMs as container-worker hosts |

Run the included playbook:

```bash
ansible-playbook andreygubarev.com.ubuntu2604 -i inventory.ini
```

Or use the role in your own playbook:

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
make check  # Lint the collection and syntax-check the installed playbook
make build  # Build dist/andreygubarev-com-2026.10.0.tar.gz
make test   # Verify deployed hosts using inventory.ini
```

Roles live in `roles/`, and collection playbooks live in `playbooks/`.
