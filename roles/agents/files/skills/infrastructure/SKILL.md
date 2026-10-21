---
name: infrastructure
description: >-
  Inspect, change, or troubleshoot infrastructure managed by the andreygubarev.com
  Ansible collection: Ubuntu container hosts, kubeadm Kubernetes, OpenTofu/Terragrunt
  GitOps, Forgejo runners, and K8up backups. Discover actual configuration before
  acting; the presence of this skill does not mean every component is installed.
---

# Infrastructure

## Discover the host before making changes

This is the collection's operating contract, not a generated inventory or proof
of a successful deployment. Roles and workloads have independent lifecycles.

1. Confirm the requested host, account, cluster context, and scope of work.
2. Read available settings in `/etc/ansible/facts.d/ubuntu2604.fact`,
   `/etc/ansible/facts.d/kubernetes.fact`, and `/etc/ansible/facts.d/terraform.fact`.
   These files record desired configuration before application, not runtime health.
   Do not assume missing roles should be installed.
3. Resolve account homes with `getent passwd`. The tooling user, kubeconfig owner,
   GitOps owner, and agent user can differ. Below, `~` means the relevant owner's
   home, not whichever account sudo happens to select.
4. Inspect actual services and binaries. If Kubernetes exists, check the selected
   kubeconfig context, node readiness, workloads, and warning events before mutation.
   Do not assume the default context identifies the requested cluster.
5. For GitOps, inspect `git status`, the selected workload's HCL, ordinary overrides,
   version pins, and backend location. Read only the secret inputs needed for an
   authorized operation, without printing decrypted values.

Use the installed collection's role README/defaults/tasks to resolve details.
`ansible-galaxy collection list andreygubarev.com` locates the installed collection.
Use saved versions and workspace pins rather than guessing current upstream defaults.

## Roles and ownership

All collection playbooks target localhost. Remote provisioning uses an explicit
inventory and the fully qualified role. Applying one role never applies another.

| Role | Contract |
|---|---|
| `andreygubarev.com.ubuntu2604` | Ubuntu 26.04 container-host baseline: kernel modules/sysctls, PAM limits, systemd tuning, swap policy, APT/updates, logs, SSH, DNS, and time synchronization. |
| `andreygubarev.com.kubernetes` | Standalone single-node kubeadm cluster: containerd, kubelet/control plane, kubeconfig, single-node scheduling, Flannel, metrics-server, CoreDNS configuration, and k9s. |
| `andreygubarev.com.terraform` | System direnv, tenv proxies, SOPS, and age; per-user OpenTofu/Terragrunt in `~/.tenv`; Bash direnv hook and an age identity. No HashiCorp Terraform. |
| `andreygubarev.com.gitops` | Git, Helm 3, and the `~/gitops` scaffold, with per-user configuration and durable local backends. Does not initialize or apply workloads. |
| `andreygubarev.com.agents` | This skill only. Does not install AI clients or the infrastructure described here. |

Ubuntu, Kubernetes, and Terraform settings use explicit overrides before saved
local facts before fallback defaults. Exact resolved tooling versions are reused;
routine role reapplication is not an instruction to upgrade them.

Ubuntu first-use operations include destructive Snap removal and SSH host-key
regeneration. Review the role and existing configuration before running a baseline.
Keep verified administrative SSH access when changing ports or authentication.
Never bypass SSH host-key verification to work around a mismatch.

Kubernetes cluster name, Kubernetes minor version, and cluster CIDRs are stored
identity; changing them requires an explicit migration/rebuild, not an override.
Use the configured kubeconfig owner's `~/.kube/config`. Optional CoreDNS rewrites
resolve canonical hostnames internally without changing application URLs or TLS SNI.
Do not replace the whole Corefile to change one managed rewrite.

## Tooling and workspace

- System proxies/binaries live under `/usr/local/bin`; OpenTofu/Terragrunt versions
  live under the selected user's `~/.tenv`.
- `~/gitops/.opentofu-version` and `.terragrunt-version` pin workspace tools.
  `.envrc` sets tool selection and cache paths. Never authorize direnv automatically;
  inspect the file and obtain approval before `direnv allow`.
- Helm 3 is required by the Kustomize library embedded in `kbst/kustomization`.
  Helm renders manifests; these workloads are not Helm releases. Do not manage
  them with `helm upgrade/uninstall` or assume Helm hook lifecycle is executed.
- GitOps uses the current kubeconfig context; there is no hardcoded cluster context.
- The GitOps role overlays matching bundled code, including uncommitted edits,
  but preserves host-only files. Review local changes before reapplying it.
- Ordinary inputs, SOPS policy, and encrypted maps are seeded only when absent.
  Later overlays do not commit changes; the automatic Git baseline is first-use only.
  Repository identity is local to `.git/config`; never change global Git identity.

## Inputs, secrets, and state

Each workload has `terraform.tf`, `terragrunt.hcl`, and two input files:

- `terraform.tfvars.yaml`: tracked, non-secret overrides. Omitted values use HCL defaults.
- `terraform.tfvars.sops.yaml`: encrypted secret overrides; merged last, so they win.

Passwords, runner UUID/token, B2 access keys, and the Restic password belong only
in SOPS. Hostnames, ordinary usernames/email, storage sizes, runner labels, and
repository bucket/prefix belong in ordinary YAML. Preserve unrelated overrides.

The age identity is `~/.config/sops/age/keys.txt` (`0600`, private parent). Never
replace it, put it in Git/facts, display it, or treat encrypted inputs as an age-key
backup. Recipient policy is in `~/gitops/.sops.yaml`; do not rewrite it implicitly.

**SOPS does not encrypt state or plans.** Run workload commands as the workspace
owner with the correct `HOME`; changing the account/HOME changes both age discovery
and the backend path. Use `umask 077`, private plan directories, and state mode `0600`.
Never dump decrypted input maps, Secret manifests, container environments, state,
or unfiltered logs to explain an error. Capture and redact diagnostics instead.

Shared `root.hcl` generates these absolute local backend paths:

```text
~/.local/state/gitops/<workload>/terraform.tfstate
~/.local/state/gitops/<workload>/workspaces/<workspace>/terraform.tfstate
```

State directories are `0700`. Workload relative paths are state identities: directory
renames require explicit migration. Do not delete, edit, or recreate state to make
an unexpected plan disappear. Verify the backend before initializing a workload
that is already deployed; an empty state can misleadingly plan a fresh deployment.

Disposable caches normally include `~/gitops/.terragrunt-cache` and
`~/.cache/opentofu/plugin-cache`. Older deployments may still have authoritative
state inside the Terragrunt cache. The role blocks such overlays: **do not delete
the cache to bypass that guard**. Migrate explicitly and verify state before cleanup.
Generated backend files, provider locks, plans, caches, state, and private keys stay
out of Git. Back up state and the age identity separately through approved storage.

## Workload map

Read `terragrunt.hcl` for ordering. A single-workload command does not apply its
dependencies. Do not turn a scoped change into `run --all` automatically.

| Workload | Installs or manages |
|---|---|
| `10-gateway-api` | Standard Gateway API CRDs. |
| `11-istio-base` | Istio namespace and base chart. |
| `12-istiod` | Istio control plane; automatic Gateway provisioning is disabled. |
| `13-istio-gateway` | Manually managed gateway with host HTTP/HTTPS/SSH ports and Gateway API listeners. |
| `20-cert-manager` | Certificate controller/CRDs with Gateway API support, not issuers. |
| `21-letsencrypt` | ACME ClusterIssuer using Gateway API HTTP-01. |
| `30-openebs` | LocalPV Hostpath storage and Delete/Retain classes, not replicated storage or backups. |
| `31-cnpg` | CloudNativePG operator/CRDs, not application PostgreSQL clusters. |
| `32-k8up` | K8up operator/CRDs and global B2/Restic settings, not backup schedules. |
| `40-forgejo` | Forgejo in namespace `forgejo`, its CNPG database, PVCs, HTTPS/SSH routes, and Actions. |
| `41-forgejo-runner` | Runner and privileged native-init DinD sidecar in namespace `forgejo-runners`. |
| `42-forgejo-backup` | Online backup Schedule for only the `forgejo-data` PVC. |

Free and verify administrative SSH on an alternate port before the gateway takes
host port 22. Initial application bootstrap is sequential: networking/issuer,
Forgejo/database, then runner registration and runner. Read the actual workload
inputs for application hostnames; never infer them from examples.

### Forgejo Actions

Runner registration scope matters: instance, organization, user, or repository.
An online runner with matching labels can still be ineligible for a repository.
Our shared runner is intended to be registered at instance scope. UUID/token are
provided after registration and stored in the runner workload's SOPS inputs.

`ubuntu-latest` is a configurable label, not a GitHub-hosted Ubuntu VM. Inspect
`runner_labels` to determine the job image. A working DinD daemon does not put a
Docker CLI in the job image. For Docker CI, an example suitable mapping is:

```yaml
runner_labels:
  - ubuntu-latest:docker://ghcr.io/catthehacker/ubuntu:act-24.04
```

Jobs are trusted-only: DinD is privileged, uses its own Pod-local Docker socket,
and is not the Kubernetes node's containerd socket. No Kubernetes API token is
mounted automatically. Runner/cache/Docker data are ephemeral. Config checksum
changes recreate the runner/DinD Pod; confirm no active job before applying them.
Inspect job/task status and the failing step, not just runner Pod readiness.

### Storage and backups

Retain preserves a volume after PVC deletion; it is not a backup. Hostpath PVC
sizes are not disk quotas, and storage remains tied to the node.

K8up selects opted-in PVCs. PVC annotation/selection labels belong to the workload
that owns the PVC, never to a second Terraform state. The Forgejo backup Schedule
uses a dedicated stable `b2_bucket` repository bucket/prefix with shared global
endpoint/credentials. Each run creates a new Restic snapshot in that repository;
do not create dated prefixes. Separate application repositories isolate retention.

`42-forgejo-backup` backs up only the live Forgejo data disk with a read-only mount.
It does not stop the application, back up PostgreSQL, or configure snapshot pruning.
Do not extend that scope implicitly. K8up's PreBackupPod is a data-source mechanism,
not a paired stop/start hook; there is no PostBackupPod in the bundled operator.
A successful backup is not a restore test. Preserve the Restic password independently.

## Change workflow

1. Establish the actual installation and requested change using read-only checks.
2. Edit the owning role/workload or its inputs; preserve unrelated settings and secrets.
3. For an authorized deployment, use the workspace owner's pinned tools and selected
   kubeconfig context. From the chosen workload, `terragrunt run -- plan` reviews
   the scope. Do not print secret-bearing plan JSON to the conversation.
4. Stop if the plan includes unexpected deletion, recreation, identity changes, or
   unrelated resources. Apply only the reviewed, authorized change. Saved plans
   require private storage and cleanup after use.
5. Check runtime readiness and a no-change follow-up plan. For runners, distinguish
   daemon readiness from successful workflow execution; for backups, distinguish
   snapshot creation from verified recovery.
6. Review Git changes without exposing secrets. Commits, pushes, releases, workload
   applies, key rotation, and history rewrites are separate actions requiring scope
   from the user; none is an implicit consequence of updating the scaffold.

Do not reboot, stop applications, rotate credentials, prune snapshots, or destroy
resources as a diagnostic shortcut. Collection integration tests use a fresh,
disposable Incus VM, never an existing host; run them only when requested.
