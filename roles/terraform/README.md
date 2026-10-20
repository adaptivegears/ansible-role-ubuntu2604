# andreygubarev.com.terraform

OpenTofu and Terragrunt tooling for Ubuntu 26.04, included in the `andreygubarev.com` collection. The role installs direnv and tenv system-wide, then installs OpenTofu and Terragrunt through tenv for an existing user. HashiCorp Terraform is not installed.

[Quickstart](../../docs/terraform/getting-started/quickstart.md) · [Configuration](../../docs/terraform/reference/configuration.md) · [Task index](tasks/main.yml)

Initial defaults select the latest stable tenv, OpenTofu 1.12.x, and Terragrunt 1.1.x. Exact resolved versions and the selected user are validated and saved in local facts before installation. Later runs reuse them unless explicitly overridden.

All public settings are in `defaults/main.yml`. Numbered task files use explicit static imports. The role is independent of the Ubuntu and Kubernetes roles.

## License

[Apache-2.0](../../LICENSE).
