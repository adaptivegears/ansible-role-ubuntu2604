# andreygubarev.com

## IMPORTANT behavioral guardrails

These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### Think before coding

- State material assumptions explicitly.
- If multiple reasonable interpretations exist, present them instead of choosing silently.
- If a simpler approach exists, say so. Push back when warranted.
- If the request is materially unclear, stop, name the ambiguity, and ask.

### Simplicity first

- Implement the minimum code that solves the request.
- Do not add speculative features, abstractions, configurability, or future-proofing.
- Do not add error handling for hypothetical scenarios outside the role contract.
- If the solution is much larger than necessary, simplify before finalizing.

### Surgical changes

- Touch only what the request requires.
- Do not refactor, reformat, or "improve" adjacent unrelated code.
- Match existing style, even when another style would be preferable.
- Remove only imports, variables, functions, or files made unused by your own change.
- Mention unrelated dead code or issues instead of changing them.

Every changed line should trace directly to the user request or to keeping that change correct, tested, and lint-clean.

## Collection scope

- This repository is the `andreygubarev.com` collection of public infrastructure roles and playbooks.
- Keep roles in `roles/` and collection playbooks in `playbooks/`; use fully qualified role names.

## Ubuntu 26.04 role target

- The `ubuntu2604` role configures Ubuntu 26.04 VMs that are expected to actively run container workloads.
- Prefer host defaults that support container networking, dense service processes, and predictable VM recovery.
- Keep all public Ubuntu settings in `defaults/main.yml`, resolving saved facts before fallback defaults. Validate and persist the complete configuration before application; hostname is required on first use.

## Kubernetes role target

- The `kubernetes` role provisions a standalone single-node kubeadm cluster on Ubuntu 26.04.
- Keep public settings in `defaults/main.yml` with local-fact fallbacks. Validate and save the complete desired configuration; reject changes to stored cluster identity before writing.
- Both included playbooks target localhost; the Kubernetes playbook does not automatically apply the Ubuntu role.

## Ansible style

- Keep each role's `tasks/main.yml` as an explicit, ordered list of static `ansible.builtin.import_tasks` entries.
- Keep tasks in numbered `XX-section.yml` files: tens group related areas, units identify their parts.
- Preserve task-level tags and execution order when splitting files; do not auto-discover task files.
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

- Use testinfra to verify role application in a fresh local Incus VM.
- Keep verification in `roles/ubuntu2604/tests/test_ubuntu2604.py` and `roles/kubernetes/tests/test_kubernetes.py`.
- `make test` applies Ubuntu followed by Kubernetes to a fresh VM and verifies both roles. The roles remain independently usable; standalone Kubernetes testing is not required.
- Keep tests self-contained by hardcoding the expected role contract in the tests.
- Use native testinfra modules such as `host.sysctl`, `host.file`, `host.service`, and `host.package`.
- Place expected-value constants close to the tests that use them, grouped by semantic section.
- Use parametrized tests for repeated settings such as sysctls, kernel modules, and PAM limits.
- Run verification through `make test`, which uses pytest/testinfra with xdist parallelism and SSH ControlPersist connection reuse, checks repeat application for `changed=0`, and verifies persistence after reboot.
- Delete successful test VMs; retain failed or interrupted runs and their diagnostics under `.cache/`. Do not target existing hosts or instances.

## Releases

- A release includes updating `galaxy.yml` and `CHANGELOG.md`, committing and pushing the changes, and creating and pushing the matching numeric version tag without a `v` prefix. Do not leave tag creation as a separate manual step; pushing the tag triggers Galaxy publication.

## Makefile style

- Prefix Ansible-related knobs with `ANSIBLE_` and testinfra-related knobs with `TESTINFRA_`.
- Group Makefile variables by tool area with short comments such as `# Ansible`, `# Incus`, and `# Testinfra`.
- Put each `.PHONY` declaration immediately above the target it declares.
