"""Verification for the agents role in the disposable test VM."""

import pytest
import yaml


@pytest.fixture
def skill_owner(host):
    variables = host.ansible.get_variables()
    return host.user(variables.get("agents_user", variables["ansible_user"]))


# -----------------------------------------------------------------------------
# Skill ownership and discovery
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("relative", (
    ".agents", ".agents/skills", ".agents/skills/infrastructure",
))
def test_skill_directories_are_private_and_user_owned(host, skill_owner, relative):
    directory = host.file(f"{skill_owner.home}/{relative}")
    assert directory.is_directory
    assert directory.user == skill_owner.name
    assert directory.gid == skill_owner.gid
    assert directory.mode == 0o700


def test_infrastructure_skill_is_discoverable_and_user_owned(host, skill_owner):
    skill = host.file(f"{skill_owner.home}/.agents/skills/infrastructure/SKILL.md")
    assert skill.is_file
    assert skill.user == skill_owner.name
    assert skill.gid == skill_owner.gid
    assert skill.mode == 0o644
    opening, frontmatter, body = skill.content_string.split("---\n", 2)
    assert opening == ""
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == "infrastructure"
    assert "OpenTofu/Terragrunt" in metadata["description"]
    assert "does not mean every component is installed" in metadata["description"]
    for section in (
        "Discover the host before making changes", "Roles and ownership",
        "Tooling and workspace", "Inputs, secrets, and state", "Workload map",
        "Forgejo Actions", "Storage and backups", "Change workflow",
    ):
        assert section in body


# -----------------------------------------------------------------------------
# Infrastructure operating contract
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("role", ("ubuntu2604", "kubernetes", "terraform", "gitops", "agents"))
def test_skill_explains_each_independent_role(host, skill_owner, role):
    skill = host.file(f"{skill_owner.home}/.agents/skills/infrastructure/SKILL.md")
    assert f"`andreygubarev.com.{role}`" in skill.content_string


@pytest.mark.parametrize("workload", (
    "10-gateway-api", "11-istio-base", "12-istiod", "13-istio-gateway",
    "20-cert-manager", "21-letsencrypt", "30-openebs", "31-cnpg", "32-k8up",
    "40-forgejo", "41-forgejo-runner", "42-forgejo-backup",
))
def test_skill_explains_the_bundled_workloads(host, skill_owner, workload):
    skill = host.file(f"{skill_owner.home}/.agents/skills/infrastructure/SKILL.md")
    assert f"`{workload}`" in skill.content_string


# -----------------------------------------------------------------------------
# Unmanaged files
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("relative", ("unmanaged/SKILL.md", "infrastructure/notes.txt"))
def test_existing_skills_and_extra_files_are_preserved(host, skill_owner, relative):
    item = host.file(f"{skill_owner.home}/.agents/skills/{relative}")
    assert item.is_file
    assert item.user == skill_owner.name
    assert item.gid == skill_owner.gid
    assert item.mode == 0o644
    assert item.content_string == "Unmanaged test fixture.\n"
