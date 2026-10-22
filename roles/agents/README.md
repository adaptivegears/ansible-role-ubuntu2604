# Agents

Installs the [Pi coding-agent harness](https://pi.dev/docs/latest/quickstart) system-wide on Ubuntu 26.04. Node.js and npm come from Ubuntu APT; Pi is installed through npm with lifecycle scripts disabled and an explicit `/usr/local` prefix. The CLI is available at `/usr/local/bin/pi`, including to non-interactive callers.

```bash
ansible-playbook andreygubarev.com.agents
pi --version
```

`agents_pi_version` defaults to `1.x` (`>=1.0.0 <2.0.0`, excluding prereleases). Every application queries npm and installs the latest stable release in that major series; Pi 2.x is never selected automatically. If no new release exists, reapplication does not reinstall Pi. Override `agents_pi_version` with an exact stable `1.x.y` version to pin it instead. Internet access to the npm registry is required to resolve `1.x` on each run.

The npm installation resolves an exact Pi version before installation but does not lock transitive dependencies like Pi's standalone installer does.

The role installs only the harness: no BB/getbb, service, model configuration, credentials, or automatic agent execution. Pi uses each invoking user's own `~/.pi/agent/` for configuration and sessions; existing user data is left untouched. Provider authentication is a separate manual step.

The local playbook does not apply other roles. For baseline-first provisioning, apply `andreygubarev.com.ubuntu2604` separately before `andreygubarev.com.agents`.
