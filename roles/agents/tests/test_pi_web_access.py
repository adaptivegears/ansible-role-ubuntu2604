"""Verify the BB account's Pi web tools without credentials or model calls."""

import json


PI_AGENT = "/home/bb/.pi/agent"
WEB_ACCESS = f"{PI_AGENT}/npm/node_modules/pi-web-access"


def test_pi_web_access_is_current_and_owned_by_bb(host):
    package = host.file(f"{WEB_ACCESS}/package.json")
    assert package.is_file
    assert package.user == "bb"
    metadata = json.loads(package.content_string)
    assert metadata["name"] == "pi-web-access"
    latest = json.loads(host.check_output("/usr/bin/npm view pi-web-access@latest version --json"))
    assert metadata["version"] == latest


def test_pi_web_access_is_registered_once_in_user_settings(host):
    settings = host.file(f"{PI_AGENT}/settings.json")
    assert settings.user == "bb"
    metadata = json.loads(host.file(f"{WEB_ACCESS}/package.json").content_string)
    packages = json.loads(settings.content_string)["packages"]
    sources = [entry if isinstance(entry, str) else entry["source"] for entry in packages]
    web_sources = [source for source in sources if source.startswith("npm:pi-web-access@")]
    assert web_sources == [f"npm:pi-web-access@{metadata['version']}"]


def test_pi_loads_the_web_access_tools_without_extension_errors(host):
    script = """
        import { DefaultResourceLoader } from
            '/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/index.js';
        const loader = new DefaultResourceLoader({
            cwd: '/home/bb', agentDir: '/home/bb/.pi/agent'
        });
        await loader.reload();
        const result = loader.getExtensions();
        const tools = result.extensions
            .filter(extension => extension.path.includes('/pi-web-access/'))
            .flatMap(extension => [...extension.tools.keys()]);
        console.log(JSON.stringify({errors: result.errors, tools}));
    """
    result = host.run(
        "sudo -u bb -H env PI_OFFLINE=1 timeout 30 /usr/bin/node --input-type=module -e %s",
        script,
    )
    assert result.rc == 0, result.stderr
    loaded = json.loads(result.stdout)
    assert not loaded["errors"]
    assert {"web_search", "source_check", "fetch_content", "get_search_content"} <= set(loaded["tools"])
