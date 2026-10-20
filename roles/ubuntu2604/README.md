# andreygubarev.com.ubuntu2604

Provider-neutral Ansible role for Ubuntu 26.04 container-worker VMs, included in the `andreygubarev.com` collection.

[Quickstart](../../docs/getting-started/quickstart.md) · [Configuration](../../docs/reference/configuration.md) · [Task index](tasks/main.yml)

Set `ubuntu2604_hostname` on the first run. All public settings remain in `defaults/main.yml`; the complete validated configuration is saved in local facts before application and reused on later runs.

Tasks use numbered `XX-section.yml` files; `main.yml` declares their static import order.

## License

[Apache-2.0](../../LICENSE).
