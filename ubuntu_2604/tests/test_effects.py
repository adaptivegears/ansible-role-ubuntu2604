"""Production verification for the ubuntu_2604 role.

These tests validate externally observable host behavior rather than Ansible task
implementation details. The assertions are grouped to mirror the role's semantic
sections so a failure points back to the relevant contract in tasks/main.yml.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROLE_DIR = Path(__file__).resolve().parents[1]
ROLE_VARS_FILE = ROLE_DIR / "vars" / "main.yml"

EXPECTED_KERNEL_MODULES = (
    "br_netfilter",
    "nf_conntrack",
    "overlay",
)

EXPECTED_SYSCTLS = {
    "net.bridge.bridge-nf-call-arptables": "1",
    "net.bridge.bridge-nf-call-ip6tables": "1",
    "net.bridge.bridge-nf-call-iptables": "1",
    "fs.file-max": "2097152",
    "fs.inotify.max_queued_events": "32768",
    "fs.inotify.max_user_instances": "512",
    "fs.inotify.max_user_watches": "524288",
    "fs.nr_open": "2097152",
    "kernel.panic": "10",
    "kernel.panic_on_oops": "1",
    "kernel.pid_max": "4194304",
    "kernel.task_delayacct": "1",
    "net.core.netdev_max_backlog": "65536",
    "net.core.somaxconn": "65536",
    "net.ipv4.ip_forward": "1",
    "net.ipv4.ip_local_port_range": "1024 65535",
    "net.ipv4.ip_unprivileged_port_start": "0",
    "net.ipv4.neigh.default.gc_thresh1": "2048",
    "net.ipv4.neigh.default.gc_thresh2": "4096",
    "net.ipv4.neigh.default.gc_thresh3": "8192",
    "net.ipv4.tcp_fin_timeout": "15",
    "net.ipv4.tcp_keepalive_intvl": "30",
    "net.ipv4.tcp_keepalive_probes": "5",
    "net.ipv4.tcp_keepalive_time": "600",
    "net.ipv4.tcp_max_syn_backlog": "65536",
    "net.ipv4.tcp_syncookies": "1",
    "net.ipv4.tcp_tw_reuse": "1",
    "net.ipv6.conf.all.accept_ra": "2",
    "net.ipv6.conf.all.forwarding": "1",
    "net.ipv6.conf.default.accept_ra": "2",
    "net.ipv6.conf.default.forwarding": "1",
    "net.netfilter.nf_conntrack_max": "1048576",
    "user.max_user_namespaces": "15000",
    "vm.max_map_count": "262144",
    "vm.min_free_kbytes": "131072",
    "vm.overcommit_memory": "1",
    "vm.panic_on_oom": "0",
    "vm.swappiness": "10",
}

EXPECTED_PAM_LIMITS = (
    ("soft", "nofile", "65536"),
    ("hard", "nofile", "65536"),
    ("soft", "nproc", "65536"),
    ("hard", "nproc", "65536"),
)

FSTAB_SWAP_PATTERN = re.compile(r"^\s*[^#\s]+\s+[^\s]+\s+swap\s+", re.MULTILINE)


def _role_var(name: str) -> str:
    pattern = re.compile(rf"^{re.escape(name)}:\s*(?P<value>.+?)\s*$")
    for line in ROLE_VARS_FILE.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group("value").strip().strip('"\'')
    raise AssertionError(f"{name} is missing from {ROLE_VARS_FILE}")


def _locale_name_for_locale_a(locale: str) -> str:
    return re.sub(r"utf-?8$", "utf8", locale.lower())


def _literal_setting_pattern(name: str, value: str) -> re.Pattern[str]:
    return re.compile(
        rf"^\s*{re.escape(name)}\s*=\s*{re.escape(value)}\s*(?:#.*)?$",
        re.MULTILINE,
    )


# -----------------------------------------------------------------------------
# Kernel
# -----------------------------------------------------------------------------
# The role prepares the host kernel for container networking and dense process
# trees. These checks validate the observable runtime policy and the persistent
# configuration needed for the same behavior after a reboot.
# -----------------------------------------------------------------------------


def test_container_kernel_modules_are_loaded(host):
    missing = [
        module
        for module in EXPECTED_KERNEL_MODULES
        if not host.file(f"/sys/module/{module}").is_directory
    ]

    assert not missing, f"kernel modules are not loaded: {missing}"


def test_runtime_sysctl_values_match_role_contract(host):
    names = json.dumps(list(EXPECTED_SYSCTLS))
    result = host.run(
        f"""python3 - <<'PY'
import json
from pathlib import Path

names = {names}
values = {{}}
errors = {{}}

for name in names:
    path = Path("/proc/sys") / Path(name.replace(".", "/"))
    try:
        values[name] = " ".join(path.read_text(encoding="utf-8").split())
    except OSError as exc:
        errors[name] = str(exc)

print(json.dumps({{"errors": errors, "values": values}}, sort_keys=True))
PY"""
    )

    assert result.rc == 0, result.stderr

    payload = json.loads(result.stdout)
    mismatches = {
        name: {"expected": expected, "actual": payload["values"].get(name)}
        for name, expected in EXPECTED_SYSCTLS.items()
        if payload["values"].get(name) != expected
    }

    assert not payload["errors"], f"failed to read sysctls: {payload['errors']}"
    assert not mismatches, f"runtime sysctl mismatches: {mismatches}"


def test_sysctl_values_persist_across_reboot(host):
    content = host.file("/etc/sysctl.d/99-ubuntu-2604.conf").content_string
    missing = [
        f"{name} = {value}"
        for name, value in EXPECTED_SYSCTLS.items()
        if _literal_setting_pattern(name, value).search(content) is None
    ]

    assert not missing, f"persistent sysctl settings are missing: {missing}"


def test_pam_limits_match_role_contract(host):
    content = host.file("/etc/security/limits.conf").content_string
    missing = []

    for limit_type, name, value in EXPECTED_PAM_LIMITS:
        pattern = re.compile(
            rf"^\*\s+{limit_type}\s+{name}\s+{re.escape(value)}\s*(?:#.*)?$",
            re.MULTILINE,
        )
        if pattern.search(content) is None:
            missing.append(f"* {limit_type} {name} {value}")

    assert not missing, f"PAM limits are missing: {missing}"


def test_transparent_hugepages_service_is_active_and_enabled(host):
    service = host.service("transparent-hugepages-madvise.service")

    assert service.is_running, "transparent-hugepages-madvise.service is not active"
    assert service.is_enabled, "transparent-hugepages-madvise.service is not enabled"


def test_transparent_hugepages_mode_is_madvise(host):
    content = host.file("/sys/kernel/mm/transparent_hugepage/enabled").content_string

    assert "[madvise]" in content, f"transparent hugepages mode is {content.strip()}"


# -----------------------------------------------------------------------------
# Swap
# -----------------------------------------------------------------------------
# Container hosts should let cgroups and OOM policy handle memory pressure, so
# swap must be absent both from the live system and from reboot-time mounts.
# -----------------------------------------------------------------------------


def test_no_swap_is_active(host):
    result = host.run("swapon --show=NAME --noheadings")

    assert result.rc == 0, result.stderr
    assert result.stdout.strip() == "", f"active swap devices: {result.stdout!r}"


def test_fstab_has_no_active_swap_entries(host):
    content = host.file("/etc/fstab").content_string

    assert FSTAB_SWAP_PATTERN.search(content) is None, (
        "/etc/fstab contains uncommented swap entries"
    )


# -----------------------------------------------------------------------------
# Locale
# -----------------------------------------------------------------------------
# The role standardizes the host's UTF-8 locale because build tools, editors,
# and container CLIs often inherit the system default environment.
# -----------------------------------------------------------------------------


def test_locales_package_is_installed(host):
    assert host.package("locales").is_installed, "locales package is not installed"


def test_configured_locale_is_generated(host):
    expected_locale = _role_var("ubuntu_2604_locale")
    result = host.run("locale -a")

    assert result.rc == 0, result.stderr

    generated_locales = {
        _locale_name_for_locale_a(line.strip()) for line in result.stdout.splitlines()
    }
    assert _locale_name_for_locale_a(expected_locale) in generated_locales, (
        f"locale {expected_locale} is not generated; observed {sorted(generated_locales)}"
    )


def test_default_locale_is_configured(host):
    expected_locale = _role_var("ubuntu_2604_locale")
    content = host.file("/etc/default/locale").content_string

    assert re.search(rf"^LANG={re.escape(expected_locale)}$", content, re.MULTILINE), (
        f"/etc/default/locale does not contain LANG={expected_locale}"
    )
