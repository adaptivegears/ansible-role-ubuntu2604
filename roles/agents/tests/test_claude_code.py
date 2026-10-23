"""Verify system-wide Claude Code without credentials or model calls."""

import json
import re

import pytest


CLAUDE_CODE_PACKAGE = "/usr/local/lib/node_modules/@anthropic-ai/claude-code"


@pytest.fixture
def claude_code_metadata(host):
    return json.loads(host.file(f"{CLAUDE_CODE_PACKAGE}/package.json").content_string)


def test_claude_code_package_is_installed_system_wide(host, claude_code_metadata):
    package = host.file(f"{CLAUDE_CODE_PACKAGE}/package.json")
    assert package.is_file
    assert package.user == "root"
    assert claude_code_metadata["name"] == "@anthropic-ai/claude-code"
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", claude_code_metadata["version"])


def test_claude_code_is_latest_stable(host, claude_code_metadata):
    latest = json.loads(
        host.check_output("/usr/bin/npm view @anthropic-ai/claude-code@latest version --json")
    )
    assert claude_code_metadata["version"] == latest


def test_claude_code_cli_is_available_without_shell_initialization(host, claude_code_metadata):
    cli = host.file("/usr/local/bin/claude")
    assert cli.is_symlink
    assert cli.user == "root"
    assert cli.linked_to.startswith(f"{CLAUDE_CODE_PACKAGE}/")
    result = host.run("sudo -u bb -H env PATH=/usr/local/bin:/usr/bin:/bin claude --version")
    assert result.rc == 0, result.stderr
    assert result.stdout.strip() == f"{claude_code_metadata['version']} (Claude Code)"


def test_claude_code_smoke_checks_do_not_configure_credentials(host):
    assert not host.file("/home/bb/.claude/.credentials.json").exists
