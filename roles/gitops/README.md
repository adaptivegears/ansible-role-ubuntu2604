# GitOps

Creates `~/gitops` for `gitops_user`, defaulting to the invoking/SSH user. The directory belongs to that user and their primary group, with mode `0700` to protect potentially sensitive OpenTofu state.

The role copies `files/gitops/` into the workspace on every run, including dotfiles, without deleting host-only files. Matching files are overwritten, including uncommitted local edits.

Git is installed and the workspace is initialized as a repository before copying the scaffold. After copying, the first application creates a baseline commit using the command-local identity `Ansible <ansible@localhost>`; existing Git settings are not changed. An existing `.git` prevents reinitialization, and an existing `HEAD` prevents another automatic commit. Subsequent overlays remain uncommitted for review with `git status` and `git diff`.

The scaffold includes `.envrc`, pinned OpenTofu/Terragrunt versions, and a `.gitignore` excluding local state and runtime caches. The provider lock file is not ignored. The role does not authorize direnv or run OpenTofu/Terragrunt commands.
