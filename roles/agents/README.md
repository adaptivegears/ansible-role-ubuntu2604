# andreygubarev.com.agents

Installs `~/.agents/skills/infrastructure/SKILL.md` for an existing user. The skill explains the collection's Ubuntu, Kubernetes, tooling, and GitOps contracts, where to discover actual configuration, and how to make scoped changes safely. Its presence does not mean those roles or workloads are installed.

```bash
ansible-playbook andreygubarev.com.agents
```

Defaults to the invoking/SSH user; use `-e agents_user=operator` to select another existing account. The role resolves their home and primary group through `getent`, creates private (`0700`) skill directories, and installs a user-owned `0644` instruction file. Root or sudo access is required; add `-K` if sudo requires a password.

Reapplication updates the managed `infrastructure/SKILL.md`. Other skills and extra files are preserved. The role does not inspect installed infrastructure, copy secrets, create users, install agent software, configure agent clients, or apply any other role. The client must support discovery under `~/.agents/skills/`.

[Skill](files/skills/infrastructure/SKILL.md) · [Task index](tasks/main.yml) · [Apache-2.0](../../LICENSE)
