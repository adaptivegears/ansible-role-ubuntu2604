# Keep durable state outside both the checkout and disposable Terragrunt caches.
# Workload paths relative to this file are state identities; rename with migration.
remote_state {
  backend = "local"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    path          = "${get_env("HOME")}/.local/state/gitops/${path_relative_to_include()}/terraform.tfstate"
    workspace_dir = "${get_env("HOME")}/.local/state/gitops/${path_relative_to_include()}/workspaces"
  }
}
