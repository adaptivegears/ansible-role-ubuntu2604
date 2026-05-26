# ansible-role-ubuntu-2604

## Role target

- This role configures Ubuntu 26.04 VMs that are expected to actively run container workloads.
- Prefer host defaults that support container networking, dense service processes, and predictable VM recovery.

## Ansible style

- Keep role tasks in `ubuntu_2604/tasks/main.yml` until the file becomes too large to navigate.
- Group tasks with comment sections using full-width separators and a short rationale:

  ```yaml
  # -----------------------------------------------------------------------------
  # Section name
  # -----------------------------------------------------------------------------
  # Explain why this section exists and why this approach is used. Do not repeat
  # what the tasks already say.
  # -----------------------------------------------------------------------------
  ```

- Prefix task names with the semantic section, for example `APT | Update package cache`.
- When commenting individual settings, explain both the effect and the reason; assume the reader may not know the kernel/sysctl name.
- Prefer clear literals over variables for values that are not real user-facing configuration.
- Add defaults only for values users are expected to override.
- Use fully qualified module names, for example `ansible.builtin.apt`.
- Keep tasks readable and lint-clean with `make check`.

## Testinfra verification

- Use testinfra for production deployment verification.
- Keep verification in `ubuntu_2604/tests/test_ubuntu_2604.py`.
- Keep tests self-contained by hardcoding the expected role contract in the tests.
- Use native testinfra modules such as `host.sysctl`, `host.file`, `host.service`, and `host.package`.
- Place expected-value constants close to the tests that use them, grouped by semantic section.
- Use parametrized tests for repeated settings such as sysctls, kernel modules, and PAM limits.
- Run verification through `make test`, which uses pytest/testinfra with xdist parallelism and SSH ControlPersist connection reuse.

## Makefile style

- Prefix Ansible-related knobs with `ANSIBLE_` and testinfra-related knobs with `TESTINFRA_`.
- Group Makefile variables by tool area with short comments such as `# Ansible` and `# Testinfra`.
- Put each `.PHONY` declaration immediately above the target it declares.
