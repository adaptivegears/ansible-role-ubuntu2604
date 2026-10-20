"""Verification for the terraform tooling role."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest
import yaml
from ansible.plugins.filter.core import FilterModule
from ansible.plugins.loader import filter_loader, init_plugin_loader
from ansible.plugins.test.core import TestModule as AnsibleTestModule
from jinja2 import Environment


# -----------------------------------------------------------------------------
# Configuration and release selection
# -----------------------------------------------------------------------------


SETTINGS_FACT = "/etc/ansible/facts.d/terraform.fact"
ROLE_SOURCE_URL = "https://github.com/andreygubarev/ansible-collection"
INITIAL_SETTINGS = {
    "user": "ubuntu",
    "tenv_version": "latest",
    "opentofu_version": "1.12.x",
    "terragrunt_version": "1.1.x",
    "sops_version": "3.13.3",
    "age_version": "1.3.2",
}


@pytest.fixture(scope="module")
def configuration_contract():
    role = Path(__file__).resolve().parents[1]
    ordered = yaml.safe_load((role / "tasks/01-configuration.yml").read_text())[0]["block"]
    tasks = {task["name"]: task for task in ordered}
    defaults = yaml.safe_load((role / "defaults/main.yml").read_text())
    environment = Environment()
    filters = FilterModule().filters()
    environment.filters.update({
        name: filters[name] for name in ("combine", "to_nice_json", "regex_escape", "regex_replace")
    })
    environment.tests["match"] = AnsibleTestModule().tests()["match"]
    init_plugin_loader()
    environment.filters["community.general.version_sort"] = filter_loader.get(
        "community.general.version_sort"
    ).j2_function

    def evaluate(expression, context):
        return environment.compile_expression(expression.strip()[2:-2].strip())(**context)

    def resolve(saved, overrides):
        context = {"terraform__facts": saved, "ansible_user": "ubuntu", "ansible_facts": {"user_id": "root"}}
        context.update({name: evaluate(value, context) for name, value in defaults.items()})
        context.update(overrides)
        return context

    return ordered, tasks, defaults, environment, evaluate, resolve


def test_configuration_defaults_and_complete_snapshot(configuration_contract):
    ordered, tasks, defaults, environment, evaluate, resolve = configuration_contract
    assert set(defaults) == {"terraform_" + key for key in INITIAL_SETTINGS}
    context = resolve({}, {})
    assert {key: context["terraform_" + key] for key in INITIAL_SETTINGS} == INITIAL_SETTINGS

    saved = {
        "user": "operator",
        "tenv_version": "4.15.1",
        "opentofu_version": "1.12.8",
        "terragrunt_version": "1.1.6",
        "other_setting": "keep",
    }
    context = resolve(saved, {"terraform_opentofu_version": "1.12.9"})
    exact = tasks["Configuration | Resolve exact versions"]["ansible.builtin.set_fact"]
    context.update({name: evaluate(value, context) for name, value in exact.items()})
    expression = tasks["Configuration | Prepare complete settings snapshot"]["ansible.builtin.set_fact"]["terraform__vars"]
    actual = evaluate(expression, context)
    expected = {
        **saved, "opentofu_version": "1.12.9", "sops_version": "3.13.3",
        "age_version": "1.3.2", "_source": ROLE_SOURCE_URL,
    }
    assert actual == expected
    copy = tasks["Configuration | Save complete desired settings"]["ansible.builtin.copy"]
    assert copy["dest"] == SETTINGS_FACT
    assert json.loads(environment.from_string(copy["content"]).render(terraform__vars=actual)) == expected
    names = [task["name"] for task in ordered]
    for name in (
        "Configuration | Validate required string settings",
        "Configuration | Validate encryption tool versions",
        "Configuration | Read tool owner account",
        "Configuration | Assert stable exact versions were found",
    ):
        assert names.index(name) < names.index("Configuration | Ensure local facts directory exists")


@pytest.mark.parametrize("overrides, expected", (
    ({}, ("3.12.2", "1.3.1")),
    ({"terraform_age_version": "1.3.2"}, ("3.12.2", "1.3.2")),
))
def test_saved_encryption_versions_are_reused(configuration_contract, overrides, expected):
    _ordered, _tasks, _defaults, _environment, _evaluate, resolve = configuration_contract
    context = resolve({"sops_version": "3.12.2", "age_version": "1.3.1"}, overrides)
    assert (context["terraform_sops_version"], context["terraform_age_version"]) == expected


def test_release_selection_stays_in_minor_series_and_excludes_prereleases(configuration_contract):
    _ordered, tasks, _defaults, _environment, evaluate, resolve = configuration_contract
    context = resolve({}, {})
    context.update({
        "terraform__tenv_release": {"json": {"tag_name": "v4.15.1"}},
        "terraform__opentofu_tags": {"json": [
            {"ref": "refs/tags/" + tag} for tag in ("v1.12.9", "v1.12.10", "v1.12.11-rc1", "v1.13.1")
        ]},
        "terraform__terragrunt_tags": {"json": [
            {"ref": "refs/tags/" + tag} for tag in ("v1.1.9", "v1.1.10", "v1.1.11-beta1", "v1.2.0")
        ]},
    })
    expressions = tasks["Configuration | Resolve exact versions"]["ansible.builtin.set_fact"]
    actual = {name: evaluate(value, context) for name, value in expressions.items()}
    assert actual == {
        "terraform__tenv_version": "4.15.1",
        "terraform__opentofu_version": "1.12.10",
        "terraform__terragrunt_version": "1.1.10",
    }
    context["terraform__opentofu_tags"] = {"json": [{"ref": "refs/tags/v1.12.0-rc1"}]}
    assert evaluate(expressions["terraform__opentofu_version"], context) == ""


@pytest.mark.parametrize(
    "task, name, value, valid",
    (
        ("Validate required string settings", "user", "ubuntu", True),
        ("Validate required string settings", "user", "", False),
        ("Validate required string settings", "user", False, False),
        ("Validate encryption tool versions", "sops_version", "3.13.3", True),
        ("Validate encryption tool versions", "sops_version", "latest", False),
        ("Validate encryption tool versions", "sops_version", "v3.13.3", False),
        ("Validate encryption tool versions", "age_version", "1.3.2", True),
        ("Validate encryption tool versions", "age_version", "1.3.x", False),
        ("Validate encryption tool versions", "age_version", "1.3.2-rc1", False),
        ("Validate tenv version", "tenv_version", "latest", True),
        ("Validate tenv version", "tenv_version", "4.15.1", True),
        ("Validate tenv version", "tenv_version", "v4.15.1", False),
        ("Validate tenv version", "tenv_version", "4.15.x", False),
        ("Validate tool version selectors", "opentofu_version", "1.12.x", True),
        ("Validate tool version selectors", "opentofu_version", "1.12.8", True),
        ("Validate tool version selectors", "opentofu_version", "1.12.8-rc1", False),
        ("Validate tool version selectors", "terragrunt_version", "1.1.x", True),
        ("Validate tool version selectors", "terragrunt_version", "latest", False),
        ("Validate tool version selectors", "terragrunt_version", "1.1", False),
    ),
)
def test_configuration_validation(configuration_contract, task, name, value, valid):
    _ordered, tasks, _defaults, environment, _evaluate, _resolve = configuration_contract
    public_name = "terraform_" + name
    context = {public_name: value, "item": public_name}
    context["lookup"] = lambda _plugin, key: context[key]
    conditions = tasks["Configuration | " + task]["ansible.builtin.assert"]["that"]
    assert all(environment.compile_expression(condition)(**context) for condition in conditions) is valid


@pytest.fixture
def saved_settings(host):
    fact = host.file(SETTINGS_FACT)
    assert fact.is_file
    assert fact.user == "root" and fact.group == "root"
    assert fact.mode == 0o644
    settings = json.loads(fact.content_string)
    assert settings["user"]
    assert settings["_source"] == ROLE_SOURCE_URL
    for name in ("tenv_version", "opentofu_version", "terragrunt_version", "sops_version", "age_version"):
        assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", settings[name])
    return settings


# -----------------------------------------------------------------------------
# System packages and tenv proxies
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("package", ("bash", "ca-certificates", "direnv", "gzip", "tar"))
def test_prerequisite_package_is_installed(host, package):
    assert host.package(package).is_installed


@pytest.mark.parametrize("binary", ("tenv", "tofu", "terragrunt"))
def test_tenv_proxy_is_system_wide_and_versioned(host, saved_settings, binary):
    target = f"/usr/local/lib/tenv/{saved_settings['tenv_version']}/{binary}"
    link = host.file(f"/usr/local/bin/{binary}")
    assert link.is_symlink
    assert link.linked_to == target
    executable = host.file(target)
    assert executable.is_file
    assert executable.user == "root" and executable.group == "root"
    assert executable.mode == 0o755


# -----------------------------------------------------------------------------
# User-managed versions and executable smoke checks
# -----------------------------------------------------------------------------


def user_command(host, settings, *arguments):
    home = host.user(settings["user"]).home
    command = shlex.join([
        "env", f"HOME={home}", f"TENV_ROOT={home}/.tenv", "TENV_LOG=off", "TENV_SKIP_LAST_USE=true",
        *arguments,
    ])
    with host.sudo(settings["user"]):
        return host.check_output(command)


@pytest.mark.parametrize(
    "tool, binary, setting",
    (("OpenTofu", "tofu", "opentofu_version"), ("Terragrunt", "terragrunt", "terragrunt_version")),
)
def test_tool_is_installed_and_selected_for_user(host, saved_settings, tool, binary, setting):
    user = host.user(saved_settings["user"])
    root = f"{user.home}/.tenv"
    assert host.file(root).user == saved_settings["user"]
    version = saved_settings[setting]
    executable = host.file(f"{root}/{tool}/{version}/{binary}")
    assert executable.is_file
    assert executable.user == saved_settings["user"]
    assert executable.gid == user.gid
    assert executable.mode & 0o111
    default = host.file(f"{root}/{tool}/version")
    assert default.user == saved_settings["user"]
    assert default.content_string.strip() == version


def test_tenv_version(host, saved_settings):
    assert saved_settings["tenv_version"] in user_command(host, saved_settings, "/usr/local/bin/tenv", "version")


def test_opentofu_version(host, saved_settings):
    version = json.loads(user_command(host, saved_settings, "/usr/local/bin/tofu", "version", "-json"))
    assert version["terraform_version"] == saved_settings["opentofu_version"]


def test_terragrunt_version(host, saved_settings):
    assert saved_settings["terragrunt_version"] in user_command(host, saved_settings, "/usr/local/bin/terragrunt", "--version")


def test_terragrunt_can_run_opentofu(host, saved_settings):
    directory = user_command(host, saved_settings, "mktemp", "-d")
    try:
        user_command(host, saved_settings, "touch", f"{directory}/terragrunt.hcl")
        output = user_command(
            host, saved_settings, "/usr/local/bin/terragrunt", "--working-dir", directory, "run", "--", "version",
        )
        assert "OpenTofu v" + saved_settings["opentofu_version"] in output
    finally:
        user_command(host, saved_settings, "rm", "-rf", directory)


# -----------------------------------------------------------------------------
# SOPS and age
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("binary, tool", (("sops", "sops"), ("age", "age"), ("age-keygen", "age")))
def test_encryption_binary_is_system_wide_and_versioned(host, saved_settings, binary, tool):
    target = f"/usr/local/lib/{tool}/{saved_settings[tool + '_version']}/{binary}"
    link = host.file(f"/usr/local/bin/{binary}")
    assert link.is_symlink and link.linked_to == target
    executable = host.file(target)
    assert executable.is_file
    assert executable.user == "root" and executable.group == "root"
    assert executable.mode == 0o755
    arguments = ["/usr/local/bin/" + binary, "--version"]
    if binary == "sops":
        arguments.append("--disable-version-check")
    assert saved_settings[tool + "_version"] in user_command(host, saved_settings, *arguments)


def test_age_identity_is_private_and_usable_by_selected_user(host, saved_settings):
    user = host.user(saved_settings["user"])
    for name in ("sops", "sops/age", "sops/age/keys.txt"):
        item = host.file(f"{user.home}/.config/{name}")
        assert item.user == user.name and item.gid == user.gid
        assert item.mode == (0o600 if name.endswith("keys.txt") else 0o700)
    recipient = user_command(
        host, saved_settings, "/usr/local/bin/age-keygen", "-y", f"{user.home}/.config/sops/age/keys.txt",
    )
    assert recipient
    assert all(line.startswith("age1") for line in recipient.splitlines())


def test_age_generation_never_replaces_existing_key():
    role = Path(__file__).resolve().parents[1]
    tasks = yaml.safe_load((role / "tasks/41-age.yml").read_text())[0]["block"]
    generation = next(task for task in tasks if task["name"] == "Age | Generate identity only when absent")
    assert generation["ansible.builtin.command"]["creates"] == "{{ terraform__home }}/.config/sops/age/keys.txt"
    assert generation["no_log"] is True
    assert generation["become_user"] == "{{ terraform__vars.user }}"


# -----------------------------------------------------------------------------
# Bash integration
# -----------------------------------------------------------------------------


def test_direnv_bash_hook_is_managed_once(host, saved_settings):
    bashrc = host.file(host.user(saved_settings["user"]).home + "/.bashrc")
    assert bashrc.user == saved_settings["user"]
    assert bashrc.content_string.count("# BEGIN ANSIBLE terraform direnv") == 1
    assert 'eval "$(direnv hook bash)"' in bashrc.content_string
    assert ROLE_SOURCE_URL in bashrc.content_string


def test_direnv_hook_is_loaded_by_interactive_bash(host, saved_settings):
    assert user_command(host, saved_settings, "bash", "--noprofile", "-ic", "declare -F _direnv_hook") == "_direnv_hook"
