import json
import subprocess
import sys
from pathlib import Path

from llmw.bootstrap import init_project
from llmw.codex_hook import evaluate_codex_pretooluse, evaluate_codex_stop
from llmw.config import Config, save_config
from llmw.hook_state import read_session_state, write_session_state


def _run_hook(cwd: Path, *args: str, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", "hook", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
    )


def _apply_patch_payload(cwd: Path, session_id="codex-session") -> dict:
    return {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Begin Patch\n*** End Patch\n"},
        "cwd": str(cwd),
        "session_id": session_id,
    }


def _mcp_payload(tool_name: str, cwd: Path, session_id="codex-session") -> dict:
    return {"tool_name": tool_name, "tool_input": {}, "cwd": str(cwd), "session_id": session_id}


def test_codex_pretooluse_asks_search_gate_on_first_apply_patch(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-a"))
    assert result is not None
    out = result["hookSpecificOutput"]
    assert out["permissionDecision"] == "ask"
    assert "llmw_search" in out["permissionDecisionReason"]


def test_codex_pretooluse_search_gate_fires_only_once_per_session(tmp_path: Path):
    init_project(tmp_path)

    first = evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-b"))
    second = evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-b"))
    assert first is not None
    assert second is None


def test_codex_pretooluse_mcp_search_tool_clears_gate(tmp_path: Path):
    paths = init_project(tmp_path)

    result = evaluate_codex_pretooluse(
        _mcp_payload("mcp__llm-wiki__llmw_search", tmp_path, session_id="sess-c")
    )
    assert result is None
    assert read_session_state(paths, "sess-c").get("searched") is True
    assert evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-c")) is None


def test_codex_pretooluse_mcp_write_tool_clears_dirty(tmp_path: Path):
    paths = init_project(tmp_path)

    evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-d"))
    assert read_session_state(paths, "sess-d").get("dirty") is True

    result = evaluate_codex_pretooluse(
        _mcp_payload("mcp__llm-wiki__llmw_write", tmp_path, session_id="sess-d")
    )
    assert result is None
    assert read_session_state(paths, "sess-d").get("dirty") is False


def test_codex_pretooluse_search_gate_off(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_search_gate="off"))

    assert evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-e")) is None


def test_codex_pretooluse_ignores_unwatched_tools(tmp_path: Path):
    init_project(tmp_path)

    assert evaluate_codex_pretooluse(_mcp_payload("shell", tmp_path, session_id="sess-f")) is None
    assert (
        evaluate_codex_pretooluse(
            _mcp_payload("mcp__llm-wiki__llmw_read", tmp_path, session_id="sess-f")
        )
        is None
    )


def test_codex_pretooluse_outside_project_returns_none(tmp_path: Path):
    assert evaluate_codex_pretooluse(_apply_patch_payload(tmp_path, session_id="sess-g")) is None


def test_codex_pretooluse_handles_missing_payload():
    assert evaluate_codex_pretooluse({}) is None


def test_codex_stop_returns_none_when_nothing_is_dirty(tmp_path: Path):
    init_project(tmp_path)

    assert evaluate_codex_stop({"cwd": str(tmp_path), "session_id": "stop-a"}) is None


def test_codex_stop_blocks_when_source_changed_without_wiki_update(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-b", dirty=True)

    result = evaluate_codex_stop({"cwd": str(tmp_path), "session_id": "stop-b"})
    assert result is not None
    assert result["decision"] == "block"
    assert "llmw_write" in result["reason"]


def test_codex_stop_respects_stop_hook_active(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-c", dirty=True)

    result = evaluate_codex_stop(
        {"cwd": str(tmp_path), "session_id": "stop-c", "stop_hook_active": True}
    )
    assert result is None


def test_codex_stop_respects_update_gate_off(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_update_gate="off"))
    write_session_state(paths, "stop-d", dirty=True)

    assert evaluate_codex_stop({"cwd": str(tmp_path), "session_id": "stop-d"}) is None


def test_codex_stop_ignores_outside_llmw_project(tmp_path: Path):
    assert evaluate_codex_stop({"cwd": str(tmp_path), "session_id": "stop-e"}) is None


def test_hook_cli_codex_pretooluse_emits_valid_json(tmp_path: Path):
    init_project(tmp_path)
    payload = json.dumps(_apply_patch_payload(tmp_path, session_id="cli-sess"))

    result = _run_hook(tmp_path, "codex-pretooluse", stdin=payload)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_hook_cli_codex_stop_emits_block_decision(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "cli-stop", dirty=True)
    payload = json.dumps({"cwd": str(tmp_path), "session_id": "cli-stop"})

    result = _run_hook(tmp_path, "codex-stop", stdin=payload)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["decision"] == "block"


def test_hook_cli_codex_malformed_stdin_exits_zero_silently(tmp_path: Path):
    result = _run_hook(tmp_path, "codex-pretooluse", stdin="not json")
    assert result.returncode == 0
    assert result.stdout == ""
