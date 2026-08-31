import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _package_version() -> str:
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]


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
    assert any(f"@v{_package_version()}" in arg for arg in server["args"])


def test_codex_plugin_ships_hooks_at_default_path() -> None:
    plugin = ROOT / "plugins/llm-wiki"
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    # Codex checks `./hooks/hooks.json` automatically; a manifest `hooks`
    # entry is only needed for a non-default location.
    assert "hooks" not in manifest

    hooks = json.loads((plugin / "hooks/hooks.json").read_text())
    # SessionStart is the only event still routed through a script: its
    # self-install bootstrap is what puts `llmw` on PATH in the first
    # place. Every other command calls `llmw` directly, because a hook
    # host that hands a bare `.sh` path to Windows resolves it through
    # ShellExecute — launching the file's associated application, which
    # never inherits the hook's stdin/stdout pipe. Prefixing the paths
    # with `bash` does not fix that: on a stock Windows box `bash` is
    # `C:\Windows\System32\bash.exe` (the WSL launcher), since System32
    # precedes Git's `bin` on PATH and Git for Windows does not put
    # `bash.exe` on PATH by default.
    assert hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"] == (
        'bash "${PLUGIN_ROOT}/hooks/session-start.sh"'
    )
    pretooluse = hooks["hooks"]["PreToolUse"][0]
    assert "apply_patch" in pretooluse["matcher"]
    assert "mcp__llm-wiki__llmw_search" in pretooluse["matcher"]
    for tool in ("llmw_write", "llmw_edit", "llmw_patch", "llmw_archive"):
        assert f"mcp__llm-wiki__{tool}" in pretooluse["matcher"]
    # `|| exit 0` short-circuits identically in cmd.exe and POSIX sh, so a
    # missing `llmw` (before SessionStart's self-install finishes, or
    # after it failed) still fails open instead of surfacing exit 127 on
    # every hook — the guarantee the wrapper scripts used to provide.
    assert pretooluse["hooks"][0]["command"] == "llmw hook codex-pretooluse || exit 0"
    assert hooks["hooks"]["Stop"][0]["hooks"][0]["command"] == (
        "llmw hook codex-stop || exit 0"
    )
    assert (plugin / "hooks/session-start.sh").is_file()
    # Retained as manual entry points and as a fallback for hosts that can
    # only take a script path, so they keep their own fail-open guards.
    assert (plugin / "hooks/pre-tool-use.sh").is_file()
    assert (plugin / "hooks/stop.sh").is_file()
    for script in ("pre-tool-use.sh", "stop.sh"):
        text = (plugin / "hooks" / script).read_text()
        assert "|| true" in text
        assert "exit 0" in text


def test_codex_skill_is_discoverable_from_plain_wiki_intent() -> None:
    text = (ROOT / "plugins/llm-wiki/skills/llm-wiki/SKILL.md").read_text()
    metadata = text.split("---", 2)[1].lower()
    for phrase in ("project wiki", "check the wiki", "update the wiki", "프로젝트 위키", "위키 확인", "위키 업데이트"):
        assert phrase.lower() in metadata
    assert "llmw_status" in text
    assert "llmw_write" in text
    assert "without waiting to be asked" in text
    assert "Mechanism, not narrative" in text


def test_codex_and_package_versions_match() -> None:
    manifest = json.loads(
        (ROOT / "plugins/llm-wiki/.codex-plugin/plugin.json").read_text()
    )
    assert manifest["version"] == _package_version()
