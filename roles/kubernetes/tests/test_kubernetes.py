"""Production verification for the kubernetes role."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from ansible.plugins.filter.core import FilterModule
from jinja2 import Environment


def grep_literal(value: str) -> str:
    """Escape a literal for the POSIX grep regexes used by File.contains()."""
    return re.sub(r"([][\\.^$*])", r"\\\1", value)


# -----------------------------------------------------------------------------
# Configuration and local facts
# -----------------------------------------------------------------------------


SETTINGS_FACT = "/etc/ansible/facts.d/kubernetes.fact"
DEFAULT_CLUSTER_SETTINGS = {
    "cluster_name": "my-cluster",
    "kubernetes_version": "1.37",
    "advertise_address": "10.0.0.10",
    "pod_subnet": "10.244.0.0/16",
    "service_subnet": "10.96.0.0/16",
    "kubeconfig_user": "ubuntu",
    "apiserver_gogc": "50",
    "apiserver_gomemlimit": "",
    "flannel_manifest_url": "https://github.com/flannel-io/flannel/releases/download/v0.28.10/kube-flannel.yml",
    "metrics_server_version": "v0.9.0",
}


@pytest.fixture
def configuration_contract():
    role = Path(__file__).resolve().parents[1]
    tasks = yaml.safe_load((role / "tasks/01-configuration.yml").read_text())[0]["block"]
    defaults = yaml.safe_load((role / "defaults/main.yml").read_text())
    environment = Environment()
    filters = FilterModule().filters()
    environment.filters.update({name: filters[name] for name in ("combine", "to_nice_json")})

    def resolve(saved, overrides):
        context = {
            "kubernetes__facts": saved,
            "ansible_facts": {"default_ipv4": {"address": "10.0.0.10"}},
            "ansible_user": "ubuntu",
        }
        context.update({
            name: environment.compile_expression(value.strip()[2:-2].strip())(**context)
            for name, value in defaults.items()
        })
        context.update(overrides)
        return context

    return role, tasks, {task["name"]: task for task in tasks}, environment, resolve


@pytest.mark.parametrize(
    "saved_name, overrides, expected, accepted",
    (
        (None, {}, "", False),
        (None, {"kubernetes_cluster_name": "my-cluster"}, "my-cluster", True),
        ("my-cluster", {}, "my-cluster", True),
        ("kubernetes", {}, "kubernetes", True),
        ("my-cluster", {"kubernetes_cluster_name": "my-cluster"}, "my-cluster", True),
        ("my-cluster", {"kubernetes_cluster_name": "other-cluster"}, "other-cluster", False),
        ("my-cluster", {"kubernetes_cluster_name": ""}, "", False),
        (None, {"kubernetes_cluster_name": "   "}, "   ", False),
        (None, {"kubernetes_cluster_name": False}, False, False),
        (None, {"kubernetes_cluster_name": 0}, 0, False),
        (None, {"kubernetes_cluster_name": None}, None, False),
    ),
)
def test_cluster_name_required_and_immutable_policy(
    configuration_contract, saved_name, overrides, expected, accepted
):
    _role, _ordered, tasks, environment, resolve = configuration_contract
    saved = {} if saved_name is None else {
        "cluster_name": saved_name,
        "kubernetes_version": "1.37",
        "pod_subnet": "10.244.0.0/16",
        "service_subnet": "10.96.0.0/16",
    }
    context = resolve(saved, overrides)
    assert context["kubernetes_cluster_name"] == expected
    assert type(context["kubernetes_cluster_name"]) is type(expected)
    conditions = tasks["Configuration | Validate required cluster name"]["ansible.builtin.assert"]["that"]
    valid = all(environment.compile_expression(condition)(**context) for condition in conditions)
    if valid and saved:
        conditions = tasks["Configuration | Assert immutable cluster identity matches stored facts"]["ansible.builtin.assert"]["that"]
        valid = all(environment.compile_expression(condition)(**context) for condition in conditions)
    assert valid is accepted


def test_complete_settings_snapshot_and_validation_order(configuration_contract):
    role, ordered, tasks, environment, resolve = configuration_contract
    saved = {"cluster_name": "my-cluster", "kubernetes_version": "1.36", "other_setting": "keep"}
    context = resolve(saved, {"kubernetes_apiserver_gogc": ""})
    expected = {**DEFAULT_CLUSTER_SETTINGS, **saved, "apiserver_gogc": ""}
    expression = tasks["Configuration | Prepare complete settings snapshot"]["ansible.builtin.set_fact"]["kubernetes__vars"]
    actual = environment.compile_expression(expression.strip()[2:-2].strip())(**context)
    assert actual == expected
    names = [task["name"] for task in ordered]
    for check in (
        "Configuration | Validate required cluster name",
        "Configuration | Assert immutable cluster identity matches stored facts",
        "Configuration | Validate IPv4 cluster networking",
        "Configuration | Read kubeconfig owner account",
    ):
        assert names.index(check) < names.index("Configuration | Ensure local facts directory exists")
    copy = tasks["Configuration | Save complete desired settings"]["ansible.builtin.copy"]
    assert copy["dest"] == SETTINGS_FACT
    content = environment.from_string(copy["content"]).render(
        ansible_facts={"ansible_local": {"kubernetes": {"other_section": {"keep": True}}}},
        kubernetes__vars=actual,
    )
    assert json.loads(content) == {
        "cluster": expected,
        "_source": "https://github.com/andreygubarev/ansible-collection",
        "other_section": {"keep": True},
    }
    defaults = yaml.safe_load((role / "defaults/main.yml").read_text())
    assert len(defaults) == 10 and "kubernetes_cluster_name" in defaults


@pytest.mark.parametrize("gogc, limit", (("50", ""), ("", ""), ("", "1536MiB"), ("0", "off")))
def test_optional_gc_settings_are_preserved(configuration_contract, gogc, limit):
    role, _ordered, _tasks, environment, resolve = configuration_contract
    context = resolve(
        {**DEFAULT_CLUSTER_SETTINGS, "apiserver_gogc": gogc, "apiserver_gomemlimit": limit}, {}
    )
    context["kubernetes__kubeadm_version"] = {"stdout": "v1.37.1"}
    tasks = yaml.safe_load((role / "tasks/50-kubeadm-config.yml").read_text())
    template = next(task["ansible.builtin.copy"]["content"] for task in tasks if "ansible.builtin.copy" in task)
    documents = yaml.safe_load_all(environment.from_string(template).render(**context))
    cluster = next(document for document in documents if document["kind"] == "ClusterConfiguration")
    expected = {name: value for name, value in (("GOGC", gogc), ("GOMEMLIMIT", limit)) if value != ""}
    actual = {item["name"]: item["value"] for item in cluster["apiServer"].get("extraEnvs", [])}
    assert actual == expected
    assert cluster["clusterName"] == "my-cluster"


@pytest.fixture
def saved_settings(host):
    fact = host.file(SETTINGS_FACT)
    assert fact.exists
    assert fact.user == "root" and fact.group == "root"
    assert fact.mode == 0o644
    settings = json.loads(fact.content_string)["cluster"]
    for key in DEFAULT_CLUSTER_SETTINGS:
        assert isinstance(settings[key], str)
        if key not in ("apiserver_gogc", "apiserver_gomemlimit"):
            assert settings[key]
    return settings


# -----------------------------------------------------------------------------
# Breadcrumbs
# -----------------------------------------------------------------------------


ROLE_SOURCE_URL = "https://github.com/andreygubarev/ansible-collection"
EXPECTED_BREADCRUMBED_FILES = (
    "/etc/ansible/facts.d/kubernetes.fact",
    "/etc/modules-load.d/99-kubernetes.conf",
    "/etc/sysctl.d/99-kubernetes.conf",
    "/etc/containerd/config.toml",
    "/etc/containerd/conf.d/99-kubernetes.toml",
    "/etc/apt/sources.list.d/kubernetes.sources",
    "/etc/kubernetes/kubeadm-config.yaml",
)


@pytest.mark.parametrize("path", EXPECTED_BREADCRUMBED_FILES)
def test_role_owned_text_file_has_source_breadcrumb(host, path):
    config = host.file(path)

    assert config.exists
    assert config.contains(grep_literal(ROLE_SOURCE_URL))


# -----------------------------------------------------------------------------
# Kernel and swap
# -----------------------------------------------------------------------------


KERNEL_MODULES_CONFIG = "/etc/modules-load.d/99-kubernetes.conf"
SYSCTL_CONFIG = "/etc/sysctl.d/99-kubernetes.conf"
EXPECTED_KERNEL_MODULES = (
    "overlay",
    "br_netfilter",
)
EXPECTED_SYSCTLS = {
    "net.bridge.bridge-nf-call-iptables": "1",
    "net.bridge.bridge-nf-call-ip6tables": "1",
    "net.ipv4.ip_forward": "1",
}


@pytest.mark.parametrize("module", EXPECTED_KERNEL_MODULES)
def test_kubernetes_kernel_module_is_loaded(host, module):
    assert host.file(f"/sys/module/{module}").is_directory


@pytest.mark.parametrize("module", EXPECTED_KERNEL_MODULES)
def test_kubernetes_kernel_module_is_persistent(host, module):
    assert host.file(KERNEL_MODULES_CONFIG).contains(rf"^{module}$")


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


def test_no_swap_is_active(host):
    assert host.file("/proc/swaps").content_string.splitlines()[1:] == []


def test_fstab_has_no_active_swap_entries(host):
    swap_entry = (
        r"^[[:space:]]*[^#[:space:]][^[:space:]]*[[:space:]][[:space:]]*"
        r"[^[:space:]][^[:space:]]*[[:space:]][[:space:]]*swap[[:space:]][[:space:]]*"
    )

    assert not host.file("/etc/fstab").contains(swap_entry)


# -----------------------------------------------------------------------------
# Containerd
# -----------------------------------------------------------------------------


EXPECTED_CONTAINERD_PACKAGES = (
    "containerd",
    "containernetworking-plugins",
)


@pytest.mark.parametrize("package", EXPECTED_CONTAINERD_PACKAGES)
def test_containerd_package_is_installed(host, package):
    assert host.package(package).is_installed


def test_containerd_service_is_active_and_enabled(host):
    service = host.service("containerd")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_containerd_imports_role_dropins(host):
    config = host.file("/etc/containerd/config.toml")

    assert config.contains(r"^version[[:space:]]*=[[:space:]]*3$")
    assert config.contains(
        r'^imports[[:space:]]*=[[:space:]]*\["/etc/containerd/conf\.d/\*\.toml"\]$'
    )


def test_containerd_uses_systemd_cgroups(host):
    config = host.file("/etc/containerd/conf.d/99-kubernetes.toml")

    assert config.contains(r"^[[:space:]]*SystemdCgroup[[:space:]]*=[[:space:]]*true$")


def test_containerd_uses_kubernetes_pause_image(host):
    config = host.file("/etc/containerd/conf.d/99-kubernetes.toml")

    assert config.contains(
        r'^[[:space:]]*sandbox[[:space:]]*=[[:space:]]*"registry\.k8s\.io/pause:3\.10\.2"$'
    )


# -----------------------------------------------------------------------------
# Kubernetes packages
# -----------------------------------------------------------------------------


EXPECTED_KUBERNETES_PACKAGES = (
    "kubeadm",
    "kubectl",
    "kubelet",
)


@pytest.mark.parametrize("package", EXPECTED_KUBERNETES_PACKAGES)
def test_kubernetes_package_is_installed(host, package):
    assert host.package(package).is_installed


@pytest.mark.parametrize("package", EXPECTED_KUBERNETES_PACKAGES)
def test_kubernetes_package_is_held(host, package):
    assert package in host.check_output("apt-mark showhold").splitlines()


def test_kubernetes_repository_is_configured(host):
    source = host.file("/etc/apt/sources.list.d/kubernetes.sources")

    assert source.exists
    assert source.contains(r"^Types: deb$")
    # BRE-safe quantifiers: testinfra contains() runs plain grep, where + is literal.
    assert source.contains(r"^URIs: https://pkgs\.k8s\.io/core:/stable:/v[0-9][0-9]*\.[0-9][0-9]*/deb/$")
    assert source.contains(r"^Suites: /$")
    assert source.contains(r"^Signed-By: /etc/apt/keyrings/kubernetes\.asc$")


# -----------------------------------------------------------------------------
# Cluster
# -----------------------------------------------------------------------------


KUBEADM_CONFIG = "/etc/kubernetes/kubeadm-config.yaml"


def kubeadm_cluster_configuration(host):
    return next(
        document for document in yaml.safe_load_all(host.file(KUBEADM_CONFIG).content_string)
        if document["kind"] == "ClusterConfiguration"
    )


def test_kubeadm_admin_config_exists(host):
    config = host.file("/etc/kubernetes/admin.conf")

    assert config.exists
    assert config.user == "root"
    assert config.group == "root"


def test_kubeadm_config_uses_systemd_cgroups(host):
    assert host.file(KUBEADM_CONFIG).contains(r"^cgroupDriver: systemd$")


def test_kubeadm_config_records_saved_cluster_identity(host, saved_settings):
    config = kubeadm_cluster_configuration(host)
    assert config["clusterName"] == saved_settings["cluster_name"]
    assert config["controlPlaneEndpoint"] == saved_settings["advertise_address"] + ":6443"
    assert config["networking"]["podSubnet"] == saved_settings["pod_subnet"]
    assert config["networking"]["serviceSubnet"] == saved_settings["service_subnet"]


def test_kube_proxy_preserves_host_conntrack_limit(host):
    desired = next(
        document for document in yaml.safe_load_all(host.file(KUBEADM_CONFIG).content_string)
        if document["kind"] == "KubeProxyConfiguration"
    )
    assert desired["conntrack"]["maxPerCore"] == 0

    deployed = yaml.safe_load(host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get configmap kube-proxy -n kube-system -o jsonpath='{.data.config\\.conf}'"
    ))
    assert deployed["conntrack"]["maxPerCore"] == 0


def test_kubeadm_config_pins_kubernetes_version(host):
    assert host.file(KUBEADM_CONFIG).contains(
        r'^kubernetesVersion: "v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"$'
    )


@pytest.mark.parametrize("name, setting", (("GOGC", "apiserver_gogc"), ("GOMEMLIMIT", "apiserver_gomemlimit")))
def test_saved_apiserver_gc_settings_are_applied(host, saved_settings, name, setting):
    expected = saved_settings[setting] or None
    config = kubeadm_cluster_configuration(host)
    configured = {item["name"]: item["value"] for item in config["apiServer"].get("extraEnvs", [])}
    assert configured.get(name) == expected

    manifest = yaml.safe_load(host.file("/etc/kubernetes/manifests/kube-apiserver.yaml").content_string)
    static = {item["name"]: item.get("value") for item in manifest["spec"]["containers"][0].get("env", [])}
    assert static.get(name) == expected

    pods = json.loads(host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get pods -n kube-system -l component=kube-apiserver -o json"
    ))
    running = {item["name"]: item.get("value") for item in pods["items"][0]["spec"]["containers"][0].get("env", [])}
    assert running.get(name) == expected

    uploaded = yaml.safe_load(host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get configmap kubeadm-config -n kube-system -o jsonpath='{.data.ClusterConfiguration}'"
    ))
    stored = {item["name"]: item["value"] for item in uploaded["apiServer"].get("extraEnvs", [])}
    assert stored.get(name) == expected


def test_kubelet_service_is_active_and_enabled(host):
    service = host.service("kubelet")

    assert service.exists
    assert service.is_running
    assert service.is_enabled


def test_control_plane_taint_is_removed(host):
    taints = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get nodes -o jsonpath='{range .items[*]}{.spec.taints}{end}'"
    )

    assert "node-role.kubernetes.io/control-plane" not in taints


# -----------------------------------------------------------------------------
# CNI (Flannel)
# -----------------------------------------------------------------------------


def test_flannel_daemonset_exists(host):
    assert "daemonset.apps/kube-flannel-ds" in host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get daemonset kube-flannel-ds -n kube-flannel -o name"
    )


def test_metrics_server_image_matches_saved_version(host, saved_settings):
    image = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get deployment metrics-server -n kube-system "
        "-o jsonpath='{.spec.template.spec.containers[0].image}'"
    )

    assert image == "registry.k8s.io/metrics-server/metrics-server:" + saved_settings["metrics_server_version"]


def test_metrics_server_deployment_exists(host):
    assert "deployment.apps/metrics-server" in host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get deployment metrics-server -n kube-system -o name"
    )


def test_metrics_server_allows_self_signed_kubelet_certificates(host):
    args = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get deployment metrics-server -n kube-system "
        "-o jsonpath='{.spec.template.spec.containers[0].args}'"
    )

    assert "--kubelet-insecure-tls" in args
