import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_codex_marketplace_points_to_valid_plugin() -> None:
    marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
    entry = marketplace["plugins"][0]
    assert entry["name"] == "llm-wiki"
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["source"]["path"] == "./plugins/llm-wiki"
    plugin = ROOT / "plugins/llm-wiki"
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    assert manifest["name"] == entry["name"]
    assert (plugin / "skills/llm-wiki/SKILL.md").is_file()
    assert (plugin / "skills/llmw-init/SKILL.md").is_file()


def test_codex_and_package_versions_match() -> None:
    import tomllib

    package = tomllib.loads((ROOT / "pyproject.toml").read_text())
    manifest = json.loads(
        (ROOT / "plugins/llm-wiki/.codex-plugin/plugin.json").read_text()
    )
    assert manifest["version"] == package["project"]["version"]
