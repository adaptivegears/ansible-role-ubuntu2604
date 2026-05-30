"""Production verification for the ubuntu2604 role."""

from __future__ import annotations

import re

import pytest


def grep_literal(value: str) -> str:
    """Escape a literal for the POSIX grep regexes used by File.contains()."""
    return re.sub(r"([][\\.^$*])", r"\\\1", value)


def locale_a_name(locale: str) -> str:
    return re.sub(r"utf-?8$", "utf8", locale.lower())


# -----------------------------------------------------------------------------
# Breadcrumbs
# -----------------------------------------------------------------------------


ROLE_SOURCE_URL = "https://github.com/adaptivegears/ansible-role-ubuntu2604"
EXPECTED_BREADCRUMBED_FILES = (
    "/etc/modules-load.d/99-ubuntu2604-container.conf",
    "/etc/sysctl.d/99-ubuntu2604.conf",
    "/etc/security/limits.d/60-ubuntu2604-container.conf",
    "/etc/systemd/system/transparent-hugepages-madvise.service",
    "/etc/systemd/system.conf.d/60-ubuntu2604-density.conf",
    "/etc/apt/ubuntu-mirrors.txt",
    "/etc/apt/ubuntu-security-mirrors.txt",
    "/etc/apt/sources.list.d/ubuntu.sources",
    "/etc/apt/preferences.d/99-ubuntu2604-nosnap.pref",
    "/etc/apt/apt.conf.d/20auto-upgrades",
    "/etc/apt/apt.conf.d/52ubuntu2604-unattended-upgrades",
    "/etc/needrestart/conf.d/99-ubuntu2604-no-auto-restarts.conf",
    "/etc/systemd/journald.conf.d/60-ubuntu2604-log-pressure.conf",
    "/etc/ssh/sshd_config.d/00-ubuntu2604-hardening.conf",
    "/etc/default/locale",
    "/etc/systemd/resolved.conf.d/60-ubuntu2604-fallback-dns.conf",
)


@pytest.mark.parametrize("path", EXPECTED_BREADCRUMBED_FILES)
def test_role_owned_text_file_has_source_breadcrumb(host, path):
    config = host.file(path)

    assert config.exists
    assert config.contains(grep_literal(ROLE_SOURCE_URL))


# -----------------------------------------------------------------------------
# Kernel
# -----------------------------------------------------------------------------


KERNEL_MODULES_CONFIG = "/etc/modules-load.d/99-ubuntu2604-container.conf"
SYSCTL_CONFIG = "/etc/sysctl.d/99-ubuntu2604.conf"
PAM_LIMITS_CONFIG = "/etc/security/limits.d/60-ubuntu2604-container.conf"
EXPECTED_KERNEL_MODULES = (
    "br_netfilter",
    "nf_conntrack",
    "overlay",
)


@pytest.mark.parametrize("module", EXPECTED_KERNEL_MODULES)
def test_container_kernel_module_is_loaded(host, module):
    assert host.file(f"/sys/module/{module}").is_directory


@pytest.mark.parametrize("module", EXPECTED_KERNEL_MODULES)
def test_container_kernel_module_is_persistent(host, module):
    assert host.file(KERNEL_MODULES_CONFIG).contains(rf"^{module}$")


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


@pytest.mark.parametrize("name, expected", EXPECTED_SYSCTLS.items())
def test_runtime_sysctl_value(host, name, expected):
    assert " ".join(str(host.sysctl(name)).split()) == expected


@pytest.mark.parametrize("name, expected", EXPECTED_SYSCTLS.items())
def test_sysctl_value_is_persistent(host, name, expected):
    pattern = (
        f"^[[:space:]]*{grep_literal(name)}[[:space:]]*="
        f"[[:space:]]*{grep_literal(expected)}[[:space:]]*$"
    )

    assert host.file(SYSCTL_CONFIG).contains(pattern)


EXPECTED_PAM_LIMITS = (
    ("soft", "nofile", "65536"),
    ("hard", "nofile", "65536"),
    ("soft", "nproc", "65536"),
    ("hard", "nproc", "65536"),
)


@pytest.mark.parametrize("limit_type, name, expected", EXPECTED_PAM_LIMITS)
def test_pam_limit_is_configured(host, limit_type, name, expected):
    pattern = (
        rf"^\*[[:space:]][[:space:]]*{limit_type}[[:space:]][[:space:]]*{name}"
        rf"[[:space:]][[:space:]]*{expected}[[:space:]]*$"
    )

    assert host.file(PAM_LIMITS_CONFIG).contains(pattern)


def test_transparent_hugepages_service_is_active_and_enabled(host):
    service = host.service("transparent-hugepages-madvise.service")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_transparent_hugepages_mode_is_madvise(host):
    assert host.file("/sys/kernel/mm/transparent_hugepage/enabled").contains(
        r"\[madvise\]"
    )


# -----------------------------------------------------------------------------
# Systemd
# -----------------------------------------------------------------------------


SYSTEMD_DENSITY_CONFIG = "/etc/systemd/system.conf.d/60-ubuntu2604-density.conf"
EXPECTED_SYSTEMD_MANAGER_SETTINGS = {
    "DefaultLimitNOFILE": "65536",
    "DefaultLimitNPROC": "65536",
    "DefaultTasksMax": "65536",
    "DefaultMemoryAccounting": "yes",
    "DefaultTasksAccounting": "yes",
}


@pytest.mark.parametrize("name, expected", EXPECTED_SYSTEMD_MANAGER_SETTINGS.items())
def test_systemd_manager_density_setting_is_persistent(host, name, expected):
    pattern = (
        f"^{grep_literal(name)}[[:space:]]*="
        f"[[:space:]]*{grep_literal(expected)}[[:space:]]*$"
    )

    assert host.file(SYSTEMD_DENSITY_CONFIG).contains(pattern)


@pytest.mark.parametrize("name, expected", EXPECTED_SYSTEMD_MANAGER_SETTINGS.items())
def test_systemd_manager_density_setting_is_effective(host, name, expected):
    assert host.check_output(f"systemctl show --property={name} --value") == expected


def test_systemd_density_config_avoids_deprecated_cpu_accounting_default(host):
    assert not host.file(SYSTEMD_DENSITY_CONFIG).contains(
        r"^[[:space:]]*DefaultCPUAccounting[[:space:]]="
    )


# -----------------------------------------------------------------------------
# Swap
# -----------------------------------------------------------------------------


def test_no_swap_is_active(host):
    assert host.file("/proc/swaps").content_string.splitlines()[1:] == []


def test_fstab_has_no_active_swap_entries(host):
    swap_entry = (
        r"^[[:space:]]*[^#[:space:]][^[:space:]]*[[:space:]][[:space:]]*"
        r"[^[:space:]][^[:space:]]*[[:space:]][[:space:]]*swap[[:space:]][[:space:]]*"
    )

    assert not host.file("/etc/fstab").contains(swap_entry)


# -----------------------------------------------------------------------------
# APT
# -----------------------------------------------------------------------------


APT_MIRRORS = "/etc/apt/ubuntu-mirrors.txt"
APT_SECURITY_MIRRORS = "/etc/apt/ubuntu-security-mirrors.txt"
APT_SOURCES = "/etc/apt/sources.list.d/ubuntu.sources"
APT_NOSNAP_PREF = "/etc/apt/preferences.d/99-ubuntu2604-nosnap.pref"
APT_VPS_REMOVED_PACKAGES = (
    "modemmanager",
    "fwupd",
    "udisks2",
    "bolt",
    "multipath-tools",
    "open-iscsi",
    "open-vm-tools",
    "software-properties-common",
    "packagekit",
    "polkitd",
)


def test_apt_sources_use_managed_mirror_lists(host):
    sources = host.file(APT_SOURCES)

    assert sources.exists
    assert sources.contains(r"^Types: deb$")
    assert sources.contains(
        rf"^URIs: mirror+file:{grep_literal(APT_MIRRORS)}$"
    )
    assert sources.contains(
        rf"^URIs: mirror+file:{grep_literal(APT_SECURITY_MIRRORS)}$"
    )
    assert sources.contains(r"^Components: main restricted universe multiverse$")
    assert sources.contains(
        r"^Signed-By: /usr/share/keyrings/ubuntu-archive-keyring\.gpg$"
    )


def test_apt_mirrors_prefer_official_archive(host):
    mirrors = host.file(APT_MIRRORS)

    assert mirrors.exists
    assert mirrors.contains(
        r"^http://archive\.ubuntu\.com/ubuntu/[[:space:]][[:space:]]*priority:1$"
    )


def test_apt_security_mirrors_prefer_official_security_endpoint(host):
    mirrors = host.file(APT_SECURITY_MIRRORS)

    assert mirrors.exists
    assert mirrors.contains(
        r"^http://security\.ubuntu\.com/ubuntu/[[:space:]][[:space:]]*priority:1$"
    )
    assert mirrors.contains(
        r"^http://archive\.ubuntu\.com/ubuntu/[[:space:]][[:space:]]*priority:[0-9][0-9]*$"
    )


@pytest.mark.parametrize("package", APT_VPS_REMOVED_PACKAGES)
def test_vps_irrelevant_hardware_package_is_removed(host, package):
    assert not host.package(package).is_installed


# -----------------------------------------------------------------------------
# Snap
# -----------------------------------------------------------------------------


def test_snapd_package_is_removed(host):
    assert not host.package("snapd").is_installed


def test_snap_command_is_absent(host):
    assert host.run("command -v snap").rc != 0


def test_snapd_reinstallation_is_pinned(host):
    policy = host.file(APT_NOSNAP_PREF)

    assert policy.exists
    assert policy.contains(r"^Package:[[:space:]][[:space:]]*snapd$")
    assert policy.contains(r"^Pin:[[:space:]][[:space:]]*release \*$")
    assert policy.contains(r"^Pin-Priority:[[:space:]][[:space:]]*-1$")


# -----------------------------------------------------------------------------
# Unattended upgrades
# -----------------------------------------------------------------------------


UNATTENDED_AUTO_UPGRADES = "/etc/apt/apt.conf.d/20auto-upgrades"
UNATTENDED_REBOOT_POLICY = "/etc/apt/apt.conf.d/52ubuntu2604-unattended-upgrades"
NEEDRESTART_POLICY = "/etc/needrestart/conf.d/99-ubuntu2604-no-auto-restarts.conf"
EXPECTED_UNATTENDED_AUTO_UPGRADES = {
    "APT::Periodic::Update-Package-Lists": "1",
    "APT::Periodic::Unattended-Upgrade": "1",
    "APT::Periodic::Download-Upgradeable-Packages": "1",
    "APT::Periodic::AutocleanInterval": "7",
}
EXPECTED_UNATTENDED_REBOOT_POLICY = {
    "Unattended-Upgrade::Automatic-Reboot": "false",
    "Unattended-Upgrade::Automatic-Reboot-WithUsers": "false",
    "Unattended-Upgrade::InstallOnShutdown": "false",
}
EXPECTED_UNATTENDED_TIMERS = (
    "apt-daily.timer",
    "apt-daily-upgrade.timer",
)


def test_unattended_upgrades_package_is_installed(host):
    assert host.package("unattended-upgrades").is_installed


@pytest.mark.parametrize("name, expected", EXPECTED_UNATTENDED_AUTO_UPGRADES.items())
def test_periodic_unattended_upgrade_setting_is_enabled(host, name, expected):
    pattern = (
        f"^{grep_literal(name)}[[:space:]][[:space:]]*"
        f'"{grep_literal(expected)}";[[:space:]]*$'
    )

    assert host.file(UNATTENDED_AUTO_UPGRADES).contains(pattern)


@pytest.mark.parametrize("name, expected", EXPECTED_UNATTENDED_REBOOT_POLICY.items())
def test_unattended_reboot_behavior_is_disabled(host, name, expected):
    pattern = (
        f"^{grep_literal(name)}[[:space:]][[:space:]]*"
        f'"{grep_literal(expected)}";[[:space:]]*$'
    )

    assert host.file(UNATTENDED_REBOOT_POLICY).contains(pattern)


def test_needrestart_is_configured_for_list_only_mode(host):
    assert host.file(NEEDRESTART_POLICY).contains(
        r"^\$nrconf{restart}[[:space:]]*=[[:space:]]*'l';$"
    )


@pytest.mark.parametrize("timer", EXPECTED_UNATTENDED_TIMERS)
def test_apt_maintenance_timer_is_enabled(host, timer):
    service = host.service(timer)

    assert service.exists
    assert service.is_enabled


# -----------------------------------------------------------------------------
# Logs
# -----------------------------------------------------------------------------


JOURNALD_CONFIG = "/etc/systemd/journald.conf.d/60-ubuntu2604-log-pressure.conf"
EXPECTED_JOURNALD_SETTINGS = {
    "Storage": "persistent",
    "Compress": "yes",
    "SystemMaxUse": "1G",
    "SystemMaxFileSize": "128M",
    "MaxRetentionSec": "30day",
    "MaxFileSec": "1week",
    "SystemKeepFree": "2G",
    "RuntimeMaxUse": "256M",
    "RuntimeKeepFree": "512M",
}


@pytest.mark.parametrize("name, expected", EXPECTED_JOURNALD_SETTINGS.items())
def test_journald_pressure_setting_is_persistent(host, name, expected):
    pattern = (
        f"^{grep_literal(name)}[[:space:]]*="
        f"[[:space:]]*{grep_literal(expected)}[[:space:]]*$"
    )

    assert host.file(JOURNALD_CONFIG).contains(pattern)


def test_persistent_journal_directory_is_configured(host):
    journal_dir = host.file("/var/log/journal")

    assert journal_dir.is_directory
    assert journal_dir.user == "root"
    assert journal_dir.group == "systemd-journal"
    assert journal_dir.mode == 0o2755


def test_systemd_journald_service_is_running(host):
    service = host.service("systemd-journald")

    assert service.exists
    assert service.is_running


# -----------------------------------------------------------------------------
# Firewall
# -----------------------------------------------------------------------------


EXPECTED_FIREWALL_PACKAGES = (
    "conntrack",
    "iptables",
    "nftables",
)
EXPECTED_NFT_COMPAT_COMMANDS = (
    ("iptables", "nf_tables"),
    ("ip6tables", "nf_tables"),
    ("arptables", "nf_tables"),
    ("ebtables", "nf_tables"),
)


@pytest.mark.parametrize("package", EXPECTED_FIREWALL_PACKAGES)
def test_firewall_package_is_installed(host, package):
    assert host.package(package).is_installed


def test_nftables_service_is_active_and_enabled(host):
    service = host.service("nftables")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_ufw_service_is_masked(host):
    link = host.file("/etc/systemd/system/ufw.service")

    assert link.is_symlink
    assert link.linked_to == "/dev/null"


@pytest.mark.parametrize("command, expected_backend", EXPECTED_NFT_COMPAT_COMMANDS)
def test_iptables_compatibility_command_uses_nft_backend(host, command, expected_backend):
    assert expected_backend in host.check_output(f"{command} --version")


# -----------------------------------------------------------------------------
# Packages
# -----------------------------------------------------------------------------


EXPECTED_OPERATION_PACKAGES = (
    "bind9-dnsutils",
    "curl",
    "exip",
    "htop",
    "iotop",
    "jq",
    "less",
    "lsof",
    "tcpdump",
    "tmux",
    "traceroute",
    "tree",
    "unzip",
    "wget",
)


@pytest.mark.parametrize("package", EXPECTED_OPERATION_PACKAGES)
def test_operation_package_is_installed(host, package):
    assert host.package(package).is_installed


# -----------------------------------------------------------------------------
# SSH
# -----------------------------------------------------------------------------


SSHD_CONFIG = "/etc/ssh/sshd_config"
SSHD_HARDENING_CONFIG = "/etc/ssh/sshd_config.d/00-ubuntu2604-hardening.conf"
EXPECTED_SSHD_HARDENING_SETTINGS = (
    ("LogLevel", "loglevel", "VERBOSE"),
    ("X11Forwarding", "x11forwarding", "no"),
    ("MaxAuthTries", "maxauthtries", "3"),
    ("IgnoreRhosts", "ignorerhosts", "yes"),
    ("HostbasedAuthentication", "hostbasedauthentication", "no"),
    ("PermitEmptyPasswords", "permitemptypasswords", "no"),
    ("PermitUserEnvironment", "permituserenvironment", "no"),
    ("Ciphers", "ciphers", "aes256-ctr,aes192-ctr,aes128-ctr"),
    ("MACs", "macs", "hmac-sha2-512,hmac-sha2-256"),
    (
        "KexAlgorithms",
        "kexalgorithms",
        "ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256",
    ),
    ("ClientAliveInterval", "clientaliveinterval", "300"),
    ("ClientAliveCountMax", "clientalivecountmax", "0"),
    ("LoginGraceTime", "logingracetime", "60"),
    ("Banner", "banner", "none"),
    ("UsePAM", "usepam", "yes"),
    ("AllowTcpForwarding", "allowtcpforwarding", "no"),
    ("MaxStartups", "maxstartups", "10:30:60"),
    ("MaxSessions", "maxsessions", "3"),
    ("PubkeyAuthentication", "pubkeyauthentication", "yes"),
    ("PasswordAuthentication", "passwordauthentication", "no"),
    (
        "HostKeyAlgorithms",
        "hostkeyalgorithms",
        "ecdsa-sha2-nistp521,ecdsa-sha2-nistp384,ecdsa-sha2-nistp256",
    ),
)


def sshd_effective_config(host):
    return {
        line.split(None, 1)[0]: line.split(None, 1)[1]
        for line in host.check_output("sshd -T").splitlines()
        if line.strip()
    }


def test_openssh_server_package_is_installed(host):
    assert host.package("openssh-server").is_installed


def test_ssh_service_is_active_and_enabled(host):
    service = host.service("ssh")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_sshd_config_permissions(host):
    config = host.file(SSHD_CONFIG)

    assert config.exists
    assert config.user == "root"
    assert config.group == "root"
    assert config.mode == 0o600


def test_sshd_config_loads_dropins(host):
    assert host.file(SSHD_CONFIG).contains(
        r"^Include /etc/ssh/sshd_config\.d/\*\.conf$"
    )


def test_sshd_hardening_dropin_permissions(host):
    config = host.file(SSHD_HARDENING_CONFIG)

    assert config.exists
    assert config.user == "root"
    assert config.group == "root"
    assert config.mode == 0o644


def test_sshd_hardening_dropin_has_no_obsolete_protocol_directive(host):
    assert not host.file(SSHD_HARDENING_CONFIG).contains(
        r"^[[:space:]]*Protocol[[:space:]]"
    )


@pytest.mark.parametrize(
    "directive, _effective_key, expected", EXPECTED_SSHD_HARDENING_SETTINGS
)
def test_sshd_hardening_setting_is_persistent(host, directive, _effective_key, expected):
    pattern = rf"^{directive}[[:space:]][[:space:]]*{grep_literal(expected)}$"

    assert host.file(SSHD_HARDENING_CONFIG).contains(pattern)


@pytest.mark.parametrize(
    "_directive, effective_key, expected", EXPECTED_SSHD_HARDENING_SETTINGS
)
def test_sshd_hardening_setting_is_effective(host, _directive, effective_key, expected):
    assert sshd_effective_config(host)[effective_key] == expected


def test_ssh_private_host_key_permissions(host):
    paths = host.check_output(
        "find /etc/ssh -maxdepth 1 -type f -name 'ssh_host_*_key' ! -name '*.pub' "
        "-print"
    ).splitlines()

    assert paths
    for path in paths:
        key = host.file(path)
        assert key.user == "root"
        assert key.group == "root"
        assert key.mode == 0o600


def test_ssh_public_host_key_permissions(host):
    paths = host.check_output(
        "find /etc/ssh -maxdepth 1 -type f -name 'ssh_host_*.pub' -print"
    ).splitlines()

    assert paths
    for path in paths:
        key = host.file(path)
        assert key.user == "root"
        assert key.group == "root"
        assert key.mode == 0o644


# -----------------------------------------------------------------------------
# Locale
# -----------------------------------------------------------------------------


EXPECTED_LOCALE = "en_US.UTF-8"


def test_locales_package_is_installed(host):
    assert host.package("locales").is_installed


def test_configured_locale_is_generated(host):
    generated_locales = {
        locale_a_name(line) for line in host.check_output("locale -a").splitlines()
    }

    assert locale_a_name(EXPECTED_LOCALE) in generated_locales


def test_default_locale_is_configured(host):
    assert host.file("/etc/default/locale").contains(
        f"^LANG={grep_literal(EXPECTED_LOCALE)}$"
    )


# -----------------------------------------------------------------------------
# Time
# -----------------------------------------------------------------------------

EXPECTED_TIMEZONE = "UTC"


def test_timezone_is_utc(host):
    assert host.check_output("timedatectl show --property=Timezone --value").strip() == EXPECTED_TIMEZONE


def test_chrony_package_is_installed(host):
    assert host.package("chrony").is_installed


def test_chrony_service_is_active_and_enabled(host):
    service = host.service("chrony")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


# -----------------------------------------------------------------------------
# DNS
# -----------------------------------------------------------------------------

EXPECTED_FALLBACK_DNS = (
    "1.1.1.1",
    "1.0.0.1",
)


def test_systemd_resolved_is_active_and_enabled(host):
    service = host.service("systemd-resolved")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_resolv_conf_uses_systemd_stub(host):
    resolv = host.file("/etc/resolv.conf")

    assert resolv.is_symlink
    assert resolv.linked_to == "/run/systemd/resolve/stub-resolv.conf"


@pytest.mark.parametrize("address", EXPECTED_FALLBACK_DNS)
def test_fallback_dns_is_configured(host, address):
    dropin = host.file(
        "/etc/systemd/resolved.conf.d/60-ubuntu2604-fallback-dns.conf"
    )

    assert dropin.exists
    assert dropin.contains(
        rf"^FallbackDNS=.*\b{re.escape(address)}\b.*$"
    )


# -----------------------------------------------------------------------------
# MOTD
# -----------------------------------------------------------------------------

def test_update_motd_d_is_empty(host):
    d = host.file("/etc/update-motd.d")
    assert d.is_directory
    assert d.listdir() == []


def test_motd_is_empty(host):
    motd = host.file("/etc/motd")
    assert motd.exists
    assert motd.content_string == ""


def test_motd_news_timer_is_masked(host):
    link = host.file("/etc/systemd/system/motd-news.timer")
    assert link.is_symlink
    assert link.linked_to == "/dev/null"
