# GitOps

Creates `~/gitops` for `gitops_user`, defaulting to the invoking/SSH user. The directory belongs to that user and their primary group, with mode `0700` to protect potentially sensitive OpenTofu state.

Run locally with `ansible-playbook andreygubarev.com.gitops`; use `-e gitops_user=operator` to select another existing user. The playbook does not apply other roles or cluster workloads.

The role copies `files/gitops/` into the workspace on every run, including dotfiles, without deleting host-only files. Matching code files are overwritten, including uncommitted local edits. Each `terraform.tfvars.yaml` is created only if missing and is never overwritten; it contains user overrides, while defaults belong in the HCL variable declarations. Newly added workloads receive their own initial YAML even when the repository already exists.

Git is installed and the workspace is initialized as a repository before copying the scaffold. After copying, the first application creates a baseline commit using the command-local identity `Ansible <ansible@localhost>`; existing Git settings are not changed. An existing `.git` prevents reinitialization, and an existing `HEAD` prevents another automatic commit. Subsequent overlays remain uncommitted for review with `git status` and `git diff`.

The scaffold includes `.envrc`, pinned OpenTofu/Terragrunt versions, and a `.gitignore` excluding local state and runtime caches. The provider lock file is also ignored. The role does not authorize direnv or run OpenTofu/Terragrunt commands.

## Workloads

- `10-gateway-api`: Standard Gateway API CRDs.
- `11-istio-base`: The `istio-system` namespace and Istio base chart.
- `12-istiod`: The Istio control plane, with automatic Gateway Deployment/Service provisioning disabled.

The Istio workloads require Helm at `/usr/local/bin/helm`; neither this role nor the Terraform tooling role installs it yet. Both charts default to Istio `1.31.2`; keep their `istio_version` overrides aligned.

For Terragrunt `run --all`, Istiod declares ordering dependencies on Gateway API and Istio base. Single-workload commands do not apply dependencies automatically: apply Gateway API and base before Istiod, and destroy Istiod before base.
