# Terraform tooling configuration

## Public settings

All settings are in `roles/terraform/defaults/main.yml`. Explicit inventory, playbook, and CLI values override saved local facts, which override the initial defaults.

| Variable | Initial default | Purpose |
|---|---|---|
| `terraform_user` | Invoking/SSH user | Existing account owning OpenTofu/Terragrunt installations and the Bash hook |
| `terraform_tenv_version` | `latest` | Latest stable tenv release or an exact version such as `4.15.1` |
| `terraform_opentofu_version` | `1.12.x` | Highest stable patch in that minor series, or an exact version |
| `terraform_terragrunt_version` | `1.1.x` | Highest stable patch in that minor series, or an exact version |

Use quoted version strings without a leading `v`. Prerelease selectors are not accepted. Minor-series resolution considers numeric stable tags only; tenv's `latest` uses GitHub's latest stable release endpoint.

## Persistence and updates

The complete desired configuration is validated and saved in `/etc/ansible/facts.d/terraform.fact` before packages or binaries are installed. Version selectors are resolved to exact versions before saving. Invalid inputs, missing users, and unresolved selectors fail before overwriting local facts. Installation failures retain the desired configuration for retry.

A later run without overrides reuses the selected user and exact versions. It does not silently upgrade because new releases or collection defaults appeared.

To deliberately refresh within the initial tracks:

```bash
ansible-playbook andreygubarev.com.terraform \
  -e terraform_tenv_version=latest \
  -e terraform_opentofu_version=1.12.x \
  -e terraform_terragrunt_version=1.1.x
```

To select exact versions, override the same variables. Existing installed versions are retained; the role does not delete another user's tools or migrate project version files. Switching `terraform_user` configures the new existing account without cleaning the old one.

## Installation layout and verification

- direnv, Bash, and CA certificates come from Ubuntu APT.
- tenv archives are checked against the release's SHA256 checksum file over HTTPS and extracted under `/usr/local/lib/tenv/<version>/`.
- Only `tenv`, `tofu`, and `terragrunt` are exposed through root-owned links in `/usr/local/bin`. The Terraform proxy and HashiCorp Terraform are not installed.
- OpenTofu and Terragrunt are installed by tenv as the selected user, with `HOME` and `TENV_ROOT` explicitly set to that user's home and `~/.tenv`.
- tenv's normal download verification remains enabled: OpenTofu uses its default signature policy, and Terragrunt uses upstream checksums. No skip-verification flags are set.
- User defaults are selected through `tenv tofu use` and `tenv tg use`; per-project overrides still work.
- The only shell modification is a managed direnv hook block in the selected user's `.bashrc`. Restart interactive Bash to load it.

## Tags

| Tag | Scope |
|---|---|
| `packages` | Install direnv, Bash, and CA certificates |
| `tenv` | Install the manager and requested proxies |
| `opentofu` | Install tenv prerequisites, OpenTofu, and its user default |
| `terragrunt` | Install tenv prerequisites, Terragrunt, and its user default |
| `direnv` | Install prerequisites and configure the Bash hook |

OS/architecture checks, the cloud-init barrier, and full configuration validation/persistence use `always`; do not skip them. Selecting a tag still validates and saves the complete desired configuration.
