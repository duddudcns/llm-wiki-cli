import json
import subprocess
import sys
from pathlib import Path

from llmw.bootstrap import init_project
from llmw.config import Config, save_config
from llmw.hook import (
    evaluate_pretooluse,
    evaluate_sessionstart,
    evaluate_stop,
    evaluate_userpromptsubmit,
)
from llmw.hook_state import read_session_state, write_session_state
from llmw.indexer import rebuild


def _run_hook(cwd: Path, *args: str, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", "hook", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
    )


def _edit_payload(file_path: Path, old="a", new="b", session_id="test-session") -> dict:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(file_path), "old_string": old, "new_string": new},
        "session_id": session_id,
    }


def _write_payload(file_path: Path, content="x", session_id="test-session") -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": str(file_path), "content": content},
        "session_id": session_id,
    }


def _bash_payload(command: str, cwd: Path, session_id="test-session") -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
        "session_id": session_id,
    }


def test_pretooluse_denies_edit_on_wiki_md(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.wiki / "concepts" / "a.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("---\ntitle: A\n---\nbody\n", encoding="utf-8")

    result = evaluate_pretooluse(_edit_payload(target))
    assert result is not None
    out = result["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert "llmw edit" in out["permissionDecisionReason"]
    assert "wiki/concepts/a.md" in out["permissionDecisionReason"]


def test_pretooluse_denies_edit_on_wiki_md_in_ai_wiki_layout(tmp_path: Path):
    paths = init_project(tmp_path, layout="ai-wiki")
    target = paths.wiki / "concepts" / "a.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("---\ntitle: A\n---\nbody\n", encoding="utf-8")

    result = evaluate_pretooluse(_edit_payload(target))
    assert result is not None
    out = result["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny"
    # rel() stays relative to the wiki container (ai-wiki/), matching what
    # `llmw edit` expects as its path argument.
    assert "wiki/concepts/a.md" in out["permissionDecisionReason"]


def test_pretooluse_denies_edit_on_existing_raw_file(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.raw / "README.md"

    result = evaluate_pretooluse(_edit_payload(target))
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "immutable" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_pretooluse_asks_for_new_raw_file(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.raw / "inbox" / "new-source.md"

    result = evaluate_pretooluse(_write_payload(target))
    assert result["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_pretooluse_denies_write_on_existing_raw_file(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.raw / "README.md"

    result = evaluate_pretooluse(_write_payload(target))
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_ignores_files_outside_llmw_project(tmp_path: Path):
    outside = tmp_path / "wiki" / "concepts" / "a.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("no .llmw here\n", encoding="utf-8")

    assert evaluate_pretooluse(_edit_payload(outside)) is None


def test_pretooluse_ignores_non_md_under_wiki(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.wiki / "assets" / "img.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"\x89PNG")

    assert evaluate_pretooluse(_edit_payload(target)) is None


def test_pretooluse_ignores_files_under_llmw_dir(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.llmw_dir / "index.sqlite"

    assert evaluate_pretooluse(_edit_payload(target)) is None


def test_pretooluse_asks_search_gate_on_first_source_edit(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    result = evaluate_pretooluse(_edit_payload(target, session_id="sess-a"))
    assert result is not None
    out = result["hookSpecificOutput"]
    assert out["permissionDecision"] == "ask"
    assert "llmw search" in out["permissionDecisionReason"]


def test_pretooluse_search_gate_fires_only_once_per_session(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    first = evaluate_pretooluse(_edit_payload(target, session_id="sess-b"))
    second = evaluate_pretooluse(_edit_payload(target, old="b", new="c", session_id="sess-b"))
    assert first is not None
    assert second is None


def test_pretooluse_search_gate_skipped_once_session_has_searched(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")
    write_session_state(paths, "sess-c", searched=True)

    assert evaluate_pretooluse(_edit_payload(target, session_id="sess-c")) is None


def test_pretooluse_search_gate_off_never_asks(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_search_gate="off"))
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    assert evaluate_pretooluse(_edit_payload(target, session_id="sess-d")) is None


def test_pretooluse_source_edit_marks_session_dirty(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_edit_payload(target, session_id="sess-e"))
    assert read_session_state(paths, "sess-e").get("dirty") is True


def test_pretooluse_bash_llmw_search_marks_session_searched(tmp_path: Path):
    paths = init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload('llmw search "topic"', tmp_path, session_id="sess-f")
    )
    assert result is None
    assert read_session_state(paths, "sess-f").get("searched") is True


def test_pretooluse_bash_search_prevents_subsequent_edit_gate(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_bash_payload("llmw search topic", tmp_path, session_id="sess-g"))
    assert evaluate_pretooluse(_edit_payload(target, session_id="sess-g")) is None


def test_pretooluse_bash_llmw_write_clears_dirty_flag(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_edit_payload(target, session_id="sess-h"))
    assert read_session_state(paths, "sess-h").get("dirty") is True

    evaluate_pretooluse(
        _bash_payload('llmw write wiki/x.md --reason "r" --stdin', tmp_path, session_id="sess-h")
    )
    assert read_session_state(paths, "sess-h").get("dirty") is False


def test_pretooluse_bash_never_gates_even_when_dirty(tmp_path: Path):
    paths = init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload('llmw edit wiki/x.md --reason "r" --old "a" --new "b"', tmp_path, session_id="sess-i")
    )
    assert result is None


def test_pretooluse_bash_ignores_commands_without_llmw(tmp_path: Path):
    paths = init_project(tmp_path)

    assert evaluate_pretooluse(_bash_payload("git status", tmp_path, session_id="sess-j")) is None
    assert read_session_state(paths, "sess-j") == {}


def test_pretooluse_bash_outside_project_returns_none(tmp_path: Path):
    assert evaluate_pretooluse(_bash_payload("llmw search x", tmp_path, session_id="sess-k")) is None


def test_pretooluse_ignores_non_guarded_tools(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.wiki / "index.md"

    assert evaluate_pretooluse({"tool_name": "Read", "tool_input": {"file_path": str(target)}}) is None
    assert evaluate_pretooluse({"tool_name": "Bash", "tool_input": {"command": "cat wiki/index.md"}}) is None


def test_pretooluse_handles_missing_or_malformed_payload():
    assert evaluate_pretooluse({}) is None
    assert evaluate_pretooluse({"tool_name": "Edit"}) is None
    assert evaluate_pretooluse({"tool_name": "Edit", "tool_input": {}}) is None


def test_pretooluse_handles_windows_backslash_paths(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.wiki / "concepts" / "a.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("body\n", encoding="utf-8")

    windows_style = str(target).replace("/", "\\")
    result = evaluate_pretooluse(_edit_payload(Path(windows_style)))
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_respects_wiki_guard_off(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_wiki_guard="off"))
    target = paths.wiki / "index.md"

    assert evaluate_pretooluse(_edit_payload(target)) is None


def test_pretooluse_respects_wiki_guard_ask(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_wiki_guard="ask"))
    target = paths.wiki / "index.md"

    result = evaluate_pretooluse(_edit_payload(target))
    assert result["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_pretooluse_nested_project_resolves_to_its_own_llmw(tmp_path: Path):
    outer = init_project(tmp_path / "outer")
    inner = init_project(tmp_path / "outer" / "nested-project")
    target = inner.wiki / "concepts" / "a.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("body\n", encoding="utf-8")

    result = evaluate_pretooluse(_edit_payload(target))
    assert result is not None
    # Path reported in the message must be relative to the INNER project,
    # not the outer one (proves resolution walked up from the file, not
    # from some unrelated ancestor project).
    assert "nested-project" not in result["hookSpecificOutput"]["permissionDecisionReason"]
    assert "wiki/concepts/a.md" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_sessionstart_emits_context_inside_project(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)

    context = evaluate_sessionstart(str(tmp_path))
    assert context is not None
    assert "llmw" in context
    assert "search" in context.lower()


def test_sessionstart_shows_ai_wiki_prefix_in_nested_layout(tmp_path: Path):
    paths = init_project(tmp_path, layout="ai-wiki")
    rebuild(paths)

    context = evaluate_sessionstart(str(tmp_path))
    assert context is not None
    assert "ai-wiki/wiki/" in context


def test_sessionstart_hints_init_outside_project(tmp_path: Path):
    context = evaluate_sessionstart(str(tmp_path))
    assert context is not None
    assert "llmw init" in context


def test_sessionstart_detects_project_from_nested_cwd(tmp_path: Path):
    paths = init_project(tmp_path)
    nested_cwd = paths.wiki / "concepts"
    nested_cwd.mkdir(parents=True, exist_ok=True)

    assert evaluate_sessionstart(str(nested_cwd)) is not None


def test_hook_cli_malformed_stdin_exits_zero_silently(tmp_path: Path):
    result = _run_hook(tmp_path, "pretooluse", stdin="not json at all")
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_cli_pretooluse_emits_valid_hookspecificoutput_json(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.wiki / "index.md"
    payload = json.dumps(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "a",
                "new_string": "b",
            },
        }
    )

    result = _run_hook(tmp_path, "pretooluse", stdin=payload)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_cli_pretooluse_silent_when_no_opinion(tmp_path: Path):
    result = _run_hook(
        tmp_path,
        "pretooluse",
        stdin=json.dumps({"tool_name": "Read", "tool_input": {"file_path": "whatever.md"}}),
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_cli_session_start_emits_context_inside_project(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    payload = json.dumps({"cwd": str(tmp_path)})

    result = _run_hook(tmp_path, "session-start", stdin=payload)
    assert result.returncode == 0
    assert "llmw" in result.stdout


def test_hook_cli_session_start_hints_init_outside_project(tmp_path: Path):
    payload = json.dumps({"cwd": str(tmp_path)})
    result = _run_hook(tmp_path, "session-start", stdin=payload)
    assert result.returncode == 0
    assert "llmw init" in result.stdout


def test_userpromptsubmit_reminds_to_search_inside_project(tmp_path: Path):
    paths = init_project(tmp_path)

    context = evaluate_userpromptsubmit(
        {"prompt": "please add retry logic to the uploader module", "cwd": str(tmp_path)}
    )
    assert context is not None
    assert "llmw search" in context


def test_userpromptsubmit_reminds_even_without_index_built(tmp_path: Path):
    paths = init_project(tmp_path)

    context = evaluate_userpromptsubmit(
        {"prompt": "explain how the indexer works", "cwd": str(tmp_path)}
    )
    assert context is not None


def test_userpromptsubmit_ignores_files_outside_llmw_project(tmp_path: Path):
    assert (
        evaluate_userpromptsubmit(
            {"prompt": "explain how the indexer works", "cwd": str(tmp_path)}
        )
        is None
    )


def test_userpromptsubmit_ignores_missing_or_empty_prompt(tmp_path: Path):
    paths = init_project(tmp_path)

    assert evaluate_userpromptsubmit({"cwd": str(tmp_path)}) is None
    assert evaluate_userpromptsubmit({"prompt": "", "cwd": str(tmp_path)}) is None


def test_userpromptsubmit_ignores_trivial_prompts(tmp_path: Path):
    paths = init_project(tmp_path)

    assert evaluate_userpromptsubmit({"prompt": "ok", "cwd": str(tmp_path)}) is None
    assert evaluate_userpromptsubmit({"prompt": "thanks", "cwd": str(tmp_path)}) is None
    assert evaluate_userpromptsubmit({"prompt": "yes continue", "cwd": str(tmp_path)}) is None
    assert evaluate_userpromptsubmit({"prompt": "/compact", "cwd": str(tmp_path)}) is None


def test_hook_cli_userpromptsubmit_emits_context(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    payload = json.dumps(
        {"prompt": "explain how the indexer works", "cwd": str(tmp_path)}
    )

    result = _run_hook(tmp_path, "userpromptsubmit", stdin=payload)
    assert result.returncode == 0
    assert "llmw" in result.stdout


def test_stop_returns_none_when_nothing_is_dirty(tmp_path: Path):
    init_project(tmp_path)

    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-a"}) is None


def test_stop_blocks_when_source_changed_without_wiki_update(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-b", dirty=True)

    result = evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-b"})
    assert result is not None
    assert result["decision"] == "block"
    assert "llmw write" in result["reason"]


def test_stop_respects_stop_hook_active_to_avoid_looping(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-c", dirty=True)

    result = evaluate_stop(
        {"cwd": str(tmp_path), "session_id": "stop-c", "stop_hook_active": True}
    )
    assert result is None


def test_stop_respects_update_gate_off(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_update_gate="off"))
    write_session_state(paths, "stop-d", dirty=True)

    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-d"}) is None


def test_stop_ignores_outside_llmw_project(tmp_path: Path):
    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-e"}) is None


def test_stop_clears_after_llmw_write_via_bash(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_edit_payload(target, session_id="stop-f"))
    evaluate_pretooluse(
        _bash_payload('llmw write wiki/x.md --reason "r" --stdin', tmp_path, session_id="stop-f")
    )

    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-f"}) is None


def test_hook_cli_stop_emits_block_decision(tmp_path: Path):
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-cli", dirty=True)
    payload = json.dumps({"cwd": str(tmp_path), "session_id": "stop-cli"})

    result = _run_hook(tmp_path, "stop", stdin=payload)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["decision"] == "block"


def test_hook_cli_stop_silent_when_not_dirty(tmp_path: Path):
    init_project(tmp_path)
    payload = json.dumps({"cwd": str(tmp_path), "session_id": "stop-cli-2"})

    result = _run_hook(tmp_path, "stop", stdin=payload)
    assert result.returncode == 0
    assert result.stdout == ""
