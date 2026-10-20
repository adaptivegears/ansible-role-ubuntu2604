"""Production verification for the kubernetes role."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment


def grep_literal(value: str) -> str:
    """Escape a literal for the POSIX grep regexes used by File.contains()."""
    return re.sub(r"([][\\.^$*])", r"\\\1", value)


# -----------------------------------------------------------------------------
# Cluster name input and local-fact reuse
# -----------------------------------------------------------------------------


@pytest.fixture
def cluster_name_contract():
    role = Path(__file__).resolve().parents[1]
    tasks = yaml.safe_load((role / "tasks/main.yml").read_text())
    return role, tasks, {task["name"]: task for task in tasks}, Environment()


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
    cluster_name_contract, saved_name, overrides, expected, accepted
):
    _role, _tasks, tasks, environment = cluster_name_contract
    saved = {} if saved_name is None else {
        "cluster_name": saved_name,
        "kubernetes_version": "1.37",
        "pod_subnet": "10.244.0.0/16",
        "service_subnet": "10.96.0.0/16",
    }
    context = {
        "kubernetes__cluster_facts": saved,
        "kubernetes_version": "1.37",
        "kubernetes_pod_subnet": "10.244.0.0/16",
        "kubernetes_service_subnet": "10.96.0.0/16",
        **overrides,
    }
    selection = tasks["Prerequisite | Select cluster name"]["ansible.builtin.set_fact"]["kubernetes__cluster_name"]
    value = environment.compile_expression(selection.strip()[2:-2].strip())(**context)
    assert value == expected
    assert type(value) is type(expected)
    context["kubernetes__cluster_name"] = value

    conditions = tasks["Prerequisite | Assert cluster name is known"]["ansible.builtin.assert"]["that"]
    valid = all(environment.compile_expression(condition)(**context) for condition in conditions)
    if valid and saved:
        conditions = tasks["Prerequisite | Assert immutable cluster identity matches stored facts"]["ansible.builtin.assert"]["that"]
        valid = all(environment.compile_expression(condition)(**context) for condition in conditions)
    assert valid is accepted


def test_cluster_name_is_optional_only_after_first_storage(cluster_name_contract):
    role, ordered, tasks, environment = cluster_name_contract
    assert "kubernetes_cluster_name" not in yaml.safe_load((role / "defaults/main.yml").read_text())
    names = [task["name"] for task in ordered]
    for check in (
        "Prerequisite | Assert cluster name is known",
        "Prerequisite | Assert immutable cluster identity matches stored facts",
    ):
        assert names.index(check) < names.index("Prerequisite | Ensure local facts directory exists")
        assert names.index(check) < names.index("Prerequisite | Store immutable cluster networking facts")

    for task_name, prefix, expected in (
        ("Prerequisite | Store immutable cluster networking facts", "cluster_name=", "cluster_name=my-cluster"),
        ("Kubeadm | Configure cluster", "clusterName:", 'clusterName: "my-cluster"'),
    ):
        content = tasks[task_name]["ansible.builtin.copy"]["content"]
        line = next(line for line in content.splitlines() if line.startswith(prefix))
        assert environment.from_string(line).render(kubernetes__cluster_name="my-cluster") == expected


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


def test_kubeadm_admin_config_exists(host):
    config = host.file("/etc/kubernetes/admin.conf")

    assert config.exists
    assert config.user == "root"
    assert config.group == "root"


def test_kubeadm_config_uses_systemd_cgroups(host):
    assert host.file(KUBEADM_CONFIG).contains(r"^cgroupDriver: systemd$")


def test_kubeadm_config_records_cluster_identity(host):
    config = host.file(KUBEADM_CONFIG)

    assert config.contains(r'^clusterName: "[^"[:space:]][^"]*"$')
    assert config.contains(r'^controlPlaneEndpoint: "[^"[:space:]][^"]*:6443"$')
    assert config.contains(r'^  advertiseAddress: "[^"[:space:]][^"]*"$')
    assert config.contains(r'^  podSubnet: "[^"[:space:]][^"]*"$')
    assert config.contains(r'^  serviceSubnet: "[^"[:space:]][^"]*"$')


def test_kubeadm_config_pins_kubernetes_version(host):
    assert host.file(KUBEADM_CONFIG).contains(
        r'^kubernetesVersion: "v[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"$'
    )


def test_kubeadm_config_bounds_apiserver_gc(host):
    config = host.file(KUBEADM_CONFIG)

    assert config.contains(r"^  extraEnvs:$")
    assert config.contains(r"^    - name: GOGC$")
    assert config.contains(r'^      value: "50"$')


def test_apiserver_static_pod_bounds_gc(host):
    manifest = host.file("/etc/kubernetes/manifests/kube-apiserver.yaml")

    assert manifest.exists
    assert manifest.contains(r"^[[:space:]]*- name: GOGC$")
    assert manifest.contains(r'^[[:space:]]*value: "50"$')


def test_running_apiserver_bounds_gc(host):
    value = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get pods -n kube-system -l component=kube-apiserver "
        "-o jsonpath='{.items[0].spec.containers[0].env[?(@.name==\"GOGC\")].value}'"
    )

    assert value == "50"


def test_cluster_configuration_configmap_records_apiserver_gc_env(host):
    cluster_configuration = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get configmap kubeadm-config -n kube-system "
        "-o jsonpath='{.data.ClusterConfiguration}'"
    )

    assert "GOGC" in cluster_configuration


def test_immutable_cluster_identity_is_stored_as_local_fact(host):
    facts = host.file("/etc/ansible/facts.d/kubernetes.fact")

    assert facts.exists
    assert facts.user == "root"
    assert facts.group == "root"
    assert facts.mode == 0o644
    assert facts.contains(r"^\[cluster\]$")
    assert facts.contains(r"^cluster_name=[^[:space:]][^[:space:]]*$")
    assert facts.contains(r"^kubernetes_version=[^[:space:]][^[:space:]]*$")
    assert facts.contains(r"^pod_subnet=[^[:space:]][^[:space:]]*$")
    assert facts.contains(r"^service_subnet=[^[:space:]][^[:space:]]*$")


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


def test_metrics_server_image_is_version_pinned(host):
    image = host.check_output(
        "kubectl --kubeconfig /etc/kubernetes/admin.conf "
        "get deployment metrics-server -n kube-system "
        "-o jsonpath='{.spec.template.spec.containers[0].image}'"
    )

    assert re.fullmatch(
        r"registry\.k8s\.io/metrics-server/metrics-server:v\d+\.\d+\.\d+", image
    )


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
