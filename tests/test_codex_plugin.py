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
    assert manifest["mcpServers"] == "./.mcp.json"
    mcp = json.loads((plugin / ".mcp.json").read_text())
    server = mcp["mcpServers"]["llm-wiki"]
    assert server["type"] == "stdio"
    assert server["command"] == "uvx"
    assert any("@v0.1.19" in arg for arg in server["args"])


def test_codex_plugin_ships_hooks_at_default_path() -> None:
    plugin = ROOT / "plugins/llm-wiki"
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    # Codex checks `./hooks/hooks.json` automatically; a manifest `hooks`
    # entry is only needed for a non-default location.
    assert "hooks" not in manifest

    hooks = json.loads((plugin / "hooks/hooks.json").read_text())
    assert hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"] == (
        "${PLUGIN_ROOT}/hooks/session-start.sh"
    )
    pretooluse = hooks["hooks"]["PreToolUse"][0]
    assert "apply_patch" in pretooluse["matcher"]
    assert "mcp__llm-wiki__llmw_search" in pretooluse["matcher"]
    assert "mcp__llm-wiki__llmw_write" in pretooluse["matcher"]
    assert pretooluse["hooks"][0]["command"] == "llmw hook codex-pretooluse"
    assert hooks["hooks"]["Stop"][0]["hooks"][0]["command"] == "llmw hook codex-stop"
    assert (plugin / "hooks/session-start.sh").is_file()


def test_codex_skill_is_discoverable_from_plain_wiki_intent() -> None:
    text = (ROOT / "plugins/llm-wiki/skills/llm-wiki/SKILL.md").read_text()
    metadata = text.split("---", 2)[1].lower()
    for phrase in ("project wiki", "check the wiki", "update the wiki", "프로젝트 위키", "위키 확인", "위키 업데이트"):
        assert phrase.lower() in metadata
    assert "llmw_status" in text
    assert "llmw_write" in text


def test_codex_and_package_versions_match() -> None:
    import tomllib

    package = tomllib.loads((ROOT / "pyproject.toml").read_text())
    manifest = json.loads(
        (ROOT / "plugins/llm-wiki/.codex-plugin/plugin.json").read_text()
    )
    assert manifest["version"] == package["project"]["version"]
