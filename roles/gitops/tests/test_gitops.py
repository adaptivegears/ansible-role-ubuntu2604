"""Verification for the GitOps workspace role."""

import re
import shlex

import pytest


@pytest.fixture
def workspace(host):
    variables = host.ansible.get_variables()
    user = host.user(variables.get("gitops_user", variables["ansible_user"]))
    return user, user.home + "/gitops"


def git_command(host, workspace, *arguments):
    user, directory = workspace
    with host.sudo(user.name):
        return host.run(shlex.join([
            "env", f"HOME={user.home}", "/usr/bin/git", "-C", directory, *arguments,
        ]))


def test_git_is_installed(host):
    assert host.package("git").is_installed


def test_helm_is_system_wide_and_usable_by_workspace_owner(host, workspace):
    link = host.file("/usr/local/bin/helm")
    assert link.is_symlink
    version = re.fullmatch(r"/usr/local/lib/helm/(3\.[0-9]+\.[0-9]+)/helm", link.linked_to)
    assert version
    binary = host.file(link.linked_to)
    assert binary.is_file
    assert binary.user == "root" and binary.group == "root"
    assert binary.mode == 0o755
    user, _directory = workspace
    with host.sudo(user.name):
        assert host.check_output("/usr/local/bin/helm version --short").startswith("v" + version.group(1) + "+")


def test_workspace_is_private_and_user_owned(host, workspace):
    user, directory = workspace
    folder = host.file(directory)
    assert folder.is_directory
    assert folder.user == user.name
    assert folder.gid == user.gid
    assert folder.mode == 0o700


@pytest.mark.parametrize("name", (
    "13-istio-gateway", "20-cert-manager", "21-letsencrypt", "30-openebs", "31-cnpg",
    "40-forgejo", "41-forgejo-runner",
))
def test_workload_directory_is_private_and_user_owned(host, workspace, name):
    user, directory = workspace
    folder = host.file(f"{directory}/{name}")
    assert folder.is_directory
    assert folder.user == user.name
    assert folder.gid == user.gid
    assert folder.mode == 0o700


@pytest.mark.parametrize("name", (
    ".envrc", ".gitignore", ".opentofu-version", ".terragrunt-version",
    "20-cert-manager/terraform.tf", "20-cert-manager/terraform.tfvars.yaml",
    "20-cert-manager/terragrunt.hcl",
    "30-openebs/terraform.tf", "30-openebs/terraform.tfvars.yaml",
    "30-openebs/terragrunt.hcl",
    "31-cnpg/terraform.tf", "31-cnpg/terraform.tfvars.yaml", "31-cnpg/terragrunt.hcl",
    "13-istio-gateway/terraform.tf", "13-istio-gateway/terraform.tfvars.yaml", "13-istio-gateway/terragrunt.hcl",
    "21-letsencrypt/terraform.tf", "21-letsencrypt/terraform.tfvars.yaml", "21-letsencrypt/terragrunt.hcl",
    "40-forgejo/terraform.tf", "40-forgejo/terraform.tfvars.yaml", "40-forgejo/terragrunt.hcl",
    "41-forgejo-runner/terraform.tf", "41-forgejo-runner/terraform.tfvars.yaml", "41-forgejo-runner/terragrunt.hcl",
))
def test_scaffold_file_is_user_owned(host, workspace, name):
    user, directory = workspace
    item = host.file(f"{directory}/{name}")
    assert item.is_file
    assert item.user == user.name
    assert item.gid == user.gid
    assert item.mode == 0o644


@pytest.mark.parametrize("name, version", ((".opentofu-version", "1.12.8"), (".terragrunt-version", "1.1.6")))
def test_project_version_is_pinned(host, workspace, name, version):
    _user, directory = workspace
    assert host.file(f"{directory}/{name}").content_string.strip() == version


def test_repository_has_a_baseline_commit(host, workspace):
    user, directory = workspace
    repository = host.file(directory + "/.git")
    assert repository.is_directory
    assert repository.user == user.name
    result = git_command(host, workspace, "rev-parse", "--verify", "HEAD")
    assert result.rc == 0
    assert re.fullmatch(r"[0-9a-f]{40}\n", result.stdout)


IGNORED_PATHS = (
    ".terraform/provider",
    ".terragrunt-cache/module",
    "terraform.tfstate",
    "terraform.tfstate.backup",
    "40-forgejo/terraform.tfvars.yaml",
    "41-forgejo-runner/terraform.tfvars.yaml",
)


def test_runtime_state_and_caches_are_ignored(host, workspace):
    result = git_command(host, workspace, "check-ignore", "--no-index", *IGNORED_PATHS)
    assert result.rc == 0
    assert result.stdout.splitlines() == list(IGNORED_PATHS)


def test_provider_lock_file_is_ignored(host, workspace):
    assert git_command(host, workspace, "check-ignore", "--no-index", ".terraform.lock.hcl").rc == 0
