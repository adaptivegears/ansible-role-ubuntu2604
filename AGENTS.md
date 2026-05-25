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
