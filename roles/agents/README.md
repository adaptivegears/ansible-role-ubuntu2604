# Agents

Installs the [Pi coding-agent harness](https://pi.dev/docs/latest/quickstart) and the [BB server](https://github.com/get-bb/bb/blob/main/packages/bb-app/README.md) on Ubuntu 26.04 with systemd. Node.js and npm come from Ubuntu APT; both applications are installed system-wide under `/usr/local` and are available without shell initialization.

```bash
ansible-playbook andreygubarev.com.agents
pi --version
```

## Versions

- `agents_pi_version` defaults to `1.x` (`>=1.0.0 <2.0.0`, excluding prereleases). Each application selects the newest stable Pi 1.x; an exact stable `1.x.y` version pins it instead.
- `agents_bb_version` defaults to `latest`, resolving the npm stable tag on each run. An exact stable version pins BB instead.

Unchanged versions are not reinstalled. npm registry access is required to resolve moving selectors. These npm installations do not lock transitive dependencies. Pi's lifecycle scripts are disabled; BB's are enabled because its SQLite, PTY and watcher add-ons require native binaries. Build prerequisites are installed for hosts without matching prebuilt binaries.

## BB account and service

BB runs as the dedicated `bb` user, with a locked login password and private home `/home/bb`. **This account has unrestricted passwordless sudo (`NOPASSWD: ALL`): its agents can obtain root. It is for trusted workloads, not a security sandbox.**

The `bb.service` unit lives in `/home/bb/.config/systemd/user/`. Linger is enabled so the user manager and BB start at boot without an SSH login, survive logout, and restart after failures. The system-wide installation is root-owned; BB's database, configuration and history live in `/home/bb/.bb`. Pi uses `/home/bb/.pi/agent/`. Existing state and provider credentials are not overwritten.

```bash
sudo -u bb env XDG_RUNTIME_DIR=/run/user/$(id -u bb) systemctl --user status bb.service
sudo -u bb env XDG_RUNTIME_DIR=/run/user/$(id -u bb) journalctl --user -u bb.service
```

BB listens only on `127.0.0.1:38886`. Its local API is unauthenticated: do not expose it directly to the internet. Provider login and BB Connect account pairing are manual and must be performed as `bb`; the role never copies credentials or pairs an account automatically. To sign this server in, run `sudo -iu bb bb account login` and approve it as a **new server**, not as a replacement for an existing BB instance.

In-app BB updates are disabled so Ansible controls the installed version. Reapplying the role upgrades BB when needed and restarts the user service on package or unit changes.

The local playbook does not apply other roles or launch agent jobs. For baseline-first provisioning, apply `andreygubarev.com.ubuntu2604` separately before `andreygubarev.com.agents`.
