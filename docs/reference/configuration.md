# Configuration

The `ubuntu_2604` role exposes one user-configurable variable. All other settings are applied as fixed defaults tuned for container-worker VMs.

## Variables

### `ubuntu_2604_locale`

The system locale to generate and set as the default.

| Attribute     | Value          |
|---------------|----------------|
| Type          | String         |
| Default       | `en_US.UTF-8`  |
| Required      | No             |

Example: set a different locale in your playbook or inventory.

```yaml
- hosts: workers
  vars:
    ubuntu_2604_locale: C.UTF-8
  roles:
    - role: ubuntu_2604
```

## Fixed defaults

The following settings are not exposed as variables because they are intrinsic to the role's purpose. Change them only by forking or overriding the role tasks.

### Kernel modules

Loaded and persisted on every boot:

- `br_netfilter` — enables bridge netfilter for container bridge policy
- `nf_conntrack` — supports NAT capacity tuning before runtimes start
- `overlay` — common writable layer for container images

### Sysctl parameters

Applied via `/etc/sysctl.d/99-ubuntu-2604.conf`:

| Category | Parameters | Rationale |
|----------|------------|-----------|
| Bridge netfilter | `net.bridge.bridge-nf-call-arptables`, `bridge-nf-call-ip6tables`, `bridge-nf-call-iptables` | Allow host policy to see L2/L3 container traffic |
| File descriptors | `fs.file-max`, `fs.nr_open` | Size host pool for dense workers |
| File watching | `fs.inotify.max_queued_events`, `max_user_instances`, `max_user_watches` | Absorb bursts from build and reload tools |
| Recovery | `kernel.panic`, `kernel.panic_on_oops` | Reboot automatically after kernel faults |
| Process space | `kernel.pid_max` | Expand global PID space before cgroup limits |
| Observability | `kernel.task_delayacct` | Track per-task CPU, I/O, and memory delays |
| Networking core | `net.core.netdev_max_backlog`, `net.core.somaxconn` | Queue ingress bursts and deeper accept queues |
| IPv4 | `net.ipv4.ip_forward`, `ip_local_port_range`, `ip_unprivileged_port_start`, `neigh.default.gc_thresh*`, `tcp_*` | Routing, NAT, ARP, and TCP tuning for containers |
| IPv6 | `net.ipv6.conf.all.accept_ra`, `all.forwarding`, `default.accept_ra`, `default.forwarding` | Enable IPv6 routing while preserving SLAAC |
| Connection tracking | `net.netfilter.nf_conntrack_max` | Hold more NAT flow state |
| User namespaces | `user.max_user_namespaces` | Permit rootless containers and build sandboxes |
| Memory | `vm.max_map_count`, `vm.min_free_kbytes`, `vm.overcommit_memory`, `vm.panic_on_oom`, `vm.swappiness` | Support mmap-heavy services and predictable OOM behavior |

### PAM limits

Applied for all users (`*` domain):

| Limit | Type | Value |
|-------|------|-------|
| `nofile` | soft | `65536` |
| `nofile` | hard | `65536` |
| `nproc` | soft | `65536` |
| `nproc` | hard | `65536` |

### Swap

Swap is disabled at runtime and all swap entries are removed from `/etc/fstab`.

### Transparent hugepages

A systemd one-shot service (`transparent-hugepages-madvise`) sets THP to `madvise` on boot, letting runtimes opt in without forcing global hugepages.

## Related pages

- [Quickstart](../getting-started/quickstart.md) — Apply the role and verify results.
