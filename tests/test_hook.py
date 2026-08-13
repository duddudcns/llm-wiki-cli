import json
import os
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


def _powershell_payload(command: str, cwd: Path, session_id="test-session") -> dict:
    return {
        "tool_name": "PowerShell",
        "tool_input": {"command": command},
        "cwd": str(cwd),
        "session_id": session_id,
    }


def _mcp_payload(tool_name: str, cwd: Path, session_id="test-session") -> dict:
    return {"tool_name": tool_name, "tool_input": {}, "cwd": str(cwd), "session_id": session_id}


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


def test_pretooluse_denies_search_gate_on_first_source_edit(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    result = evaluate_pretooluse(_edit_payload(target, session_id="sess-a"))
    assert result is not None
    out = result["hookSpecificOutput"]
    # "deny", not "ask": the reason is addressed to the agent (search, then
    # retry), and an "ask" would interrupt the user instead.
    assert out["permissionDecision"] == "deny"
    assert "llmw search" in out["permissionDecisionReason"]
    assert "retry" in out["permissionDecisionReason"].lower()


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


def test_pretooluse_bash_llmw_search_does_not_mark_session_searched(tmp_path: Path):
    # Session state is never inferred from a command string: a real `llmw
    # search` marks the session from inside the command (see
    # `hook_state.mark_searched_for_env_session`), so `--help`, a typo, or
    # a command that never runs can't satisfy the gate on its own.
    paths = init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload("llmw search --help", tmp_path, session_id="sess-f")
    )
    assert result is None
    assert read_session_state(paths, "sess-f") == {}


def test_pretooluse_bash_llmw_edit_help_does_not_clear_dirty(tmp_path: Path):
    # Reported bug: `llmw edit --help` — no wiki byte changed — cleared the
    # update gate, because the hook pattern-matched the command string
    # instead of waiting for the mutation to actually happen.
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_edit_payload(target, session_id="sess-h"))
    assert read_session_state(paths, "sess-h").get("dirty") is True

    evaluate_pretooluse(_bash_payload("llmw edit --help", tmp_path, session_id="sess-h"))
    assert read_session_state(paths, "sess-h").get("dirty") is True


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


def test_pretooluse_powershell_never_gates_even_when_dirty(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _powershell_payload(
            'llmw edit wiki/x.md --reason "r" --old "a" --new "b"',
            tmp_path,
            session_id="sess-ps-gate",
        )
    )
    assert result is None


def test_pretooluse_powershell_ignores_commands_without_llmw(tmp_path: Path):
    paths = init_project(tmp_path)

    assert (
        evaluate_pretooluse(_powershell_payload("Get-ChildItem", tmp_path, session_id="sess-ps-noop"))
        is None
    )
    assert read_session_state(paths, "sess-ps-noop") == {}


def test_pretooluse_mcp_search_tool_marks_session_searched(tmp_path: Path):
    paths = init_project(tmp_path)

    result = evaluate_pretooluse(
        _mcp_payload("mcp__llm-wiki__llmw_search", tmp_path, session_id="sess-mcp-search")
    )
    assert result is None
    assert read_session_state(paths, "sess-mcp-search").get("searched") is True


def test_pretooluse_mcp_write_tool_clears_dirty_flag(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    evaluate_pretooluse(_edit_payload(target, session_id="sess-mcp-write"))
    assert read_session_state(paths, "sess-mcp-write").get("dirty") is True

    result = evaluate_pretooluse(
        _mcp_payload("mcp__llm-wiki__llmw_write", tmp_path, session_id="sess-mcp-write")
    )
    assert result is None
    assert read_session_state(paths, "sess-mcp-write").get("dirty") is False


def test_pretooluse_mcp_edit_patch_archive_tools_clear_dirty(tmp_path: Path):
    # llmw_edit/llmw_patch/llmw_archive must clear dirty the same way as
    # llmw_write — matches the Codex integration's coverage in
    # test_codex_hook.py, since Claude Code sessions can have the same
    # llm-wiki MCP server registered.
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    for tool, session_id in (
        ("mcp__llm-wiki__llmw_edit", "sess-mcp-edit"),
        ("mcp__llm-wiki__llmw_patch", "sess-mcp-patch"),
        ("mcp__llm-wiki__llmw_archive", "sess-mcp-archive"),
    ):
        evaluate_pretooluse(_edit_payload(target, session_id=session_id))
        assert read_session_state(paths, session_id).get("dirty") is True

        result = evaluate_pretooluse(_mcp_payload(tool, tmp_path, session_id=session_id))
        assert result is None
        assert read_session_state(paths, session_id).get("dirty") is False


def test_pretooluse_ignores_unwatched_mcp_tools(tmp_path: Path):
    paths = init_project(tmp_path)

    assert (
        evaluate_pretooluse(_mcp_payload("mcp__llm-wiki__llmw_read", tmp_path, session_id="sess-mcp-other"))
        is None
    )
    assert read_session_state(paths, "sess-mcp-other") == {}


def test_pretooluse_mcp_outside_project_returns_none(tmp_path: Path):
    assert (
        evaluate_pretooluse(_mcp_payload("mcp__llm-wiki__llmw_write", tmp_path, session_id="sess-mcp-out"))
        is None
    )


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


def test_stop_fires_once_per_source_change_and_not_every_later_turn(tmp_path: Path):
    # The nudge is per "source changed" episode, not sticky: a turn that
    # legitimately needs no wiki update used to leave `dirty` set, so every
    # later turn in the session got blocked again with nothing to fix.
    paths = init_project(tmp_path)
    write_session_state(paths, "stop-f", dirty=True)

    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-f"})["decision"] == "block"
    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-f"}) is None


def test_stop_blocks_again_after_new_source_changes(tmp_path: Path):
    paths = init_project(tmp_path)
    target = paths.root / "README.md"
    target.write_text("hello\n", encoding="utf-8")
    write_session_state(paths, "stop-g", dirty=True)

    evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-g"})
    evaluate_pretooluse(_edit_payload(target, session_id="stop-g"))

    assert evaluate_stop({"cwd": str(tmp_path), "session_id": "stop-g"})["decision"] == "block"


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


# --- prose that only mentions an llmw command must not exempt a shell write ---


def test_pretooluse_llmw_write_with_heredoc_content_is_not_flagged_as_a_bypass(tmp_path: Path):
    # The real invocation form: `llmw write` outside the heredoc, page
    # content inside it — and markdown content routinely contains a `>`
    # blockquote, which reads as a redirect to the shell-mutation regex.
    # Recognizing the sanctioned command is what stops that false deny.
    init_project(tmp_path)
    command = (
        'llmw write "concepts/x.md" --reason "r" --stdin <<\'EOF\'\n'
        "---\ntitle: X\n---\n> quoted note\nEOF"
    )

    assert evaluate_pretooluse(_bash_payload(command, tmp_path, session_id="sess-real")) is None


def test_pretooluse_quoted_prose_mentioning_llmw_write_does_not_exempt_a_shell_write(
    tmp_path: Path,
):
    # "llmw write" appears only inside a quoted commit message; the actual
    # write is a raw redirect into a wiki page and must still be denied.
    init_project(tmp_path)
    command = 'git commit -m "docs: explain when to use llmw write" && echo hi > wiki/concepts/x.md'

    result = evaluate_pretooluse(_bash_payload(command, tmp_path, session_id="sess-quoted"))
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- shell writes into wiki/ and raw/ get the same guard as Edit/Write ---


def test_pretooluse_shell_redirect_into_wiki_page_denies(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload("echo hi > wiki/concepts/x.md", tmp_path, session_id="sess-redir")
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "llmw edit" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_pretooluse_powershell_set_content_into_wiki_page_denies(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _powershell_payload(
            'Set-Content -Path "wiki/concepts/x.md" -Value "hi"', tmp_path, session_id="sess-sc"
        )
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_shell_write_into_raw_denies(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload("rm raw/inbox/doc.md", tmp_path, session_id="sess-raw")
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "raw/" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_pretooluse_shell_guard_denies_under_default_config(tmp_path: Path):
    # The reason text of a "deny" reaches the agent, which can re-issue the
    # write as `llmw edit`/`write`/...; an "ask" would interrupt the user
    # over a decision only the agent can act on.
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_wiki_guard="deny"))

    result = evaluate_pretooluse(
        _bash_payload("echo hi > wiki/concepts/x.md", tmp_path, session_id="sess-deny")
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_shell_guard_asks_under_ask_config(tmp_path: Path):
    # `wiki_guard = "ask"` is the escape hatch for a project that does want
    # to hand-approve one-off shell surgery on a wiki file.
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_wiki_guard="ask"))

    result = evaluate_pretooluse(
        _bash_payload("echo hi > wiki/concepts/x.md", tmp_path, session_id="sess-ask")
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_pretooluse_read_only_sed_on_wiki_page_passes_through(tmp_path: Path):
    # `sed` without `-i` prints to stdout; reading a wiki page is not a
    # mutation and must not prompt at all (`sed ... > page` is caught by
    # the redirect, not by the verb).
    init_project(tmp_path)

    assert (
        evaluate_pretooluse(
            _bash_payload(
                "sed -n '1,5p' wiki/concepts/x.md", tmp_path, session_id="sess-sed-read"
            )
        )
        is None
    )


def test_pretooluse_sed_in_place_on_wiki_page_denies(tmp_path: Path):
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload("sed -i 's/a/b/' wiki/concepts/x.md", tmp_path, session_id="sess-sed-i")
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "llmw edit" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_pretooluse_shell_guard_off_under_wiki_guard_off(tmp_path: Path):
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(hooks_wiki_guard="off"))

    assert (
        evaluate_pretooluse(
            _bash_payload("echo hi > wiki/concepts/x.md", tmp_path, session_id="sess-off")
        )
        is None
    )


def test_pretooluse_shell_read_of_a_wiki_page_is_not_guarded(tmp_path: Path):
    init_project(tmp_path)

    assert (
        evaluate_pretooluse(
            _bash_payload("cat wiki/concepts/x.md", tmp_path, session_id="sess-read")
        )
        is None
    )


def test_pretooluse_llmw_command_naming_a_wiki_path_is_not_guarded(tmp_path: Path):
    # `llmw write` is the sanctioned path — it must never trip the guard
    # meant for raw shell writes, even though it names a wiki/*.md file.
    init_project(tmp_path)

    result = evaluate_pretooluse(
        _bash_payload(
            'llmw write wiki/concepts/x.md --reason "r" --stdin > /dev/null',
            tmp_path,
            session_id="sess-sanctioned",
        )
    )
    assert result is None


def test_pretooluse_shell_write_outside_wiki_is_not_guarded(tmp_path: Path):
    init_project(tmp_path)

    assert (
        evaluate_pretooluse(
            _bash_payload("echo hi > src/main.py", tmp_path, session_id="sess-src")
        )
        is None
    )


def test_llmw_write_clears_dirty_from_inside_the_command(tmp_path: Path):
    # The command clears its own flag via CLAUDE_CODE_SESSION_ID, so it no
    # longer matters whether the PreToolUse hook recognized the tool name
    # (Bash vs PowerShell vs anything else) or parsed the command string.
    paths = init_project(tmp_path)
    write_session_state(paths, "cli-env-sess", dirty=True)
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "cli-env-sess"}

    result = subprocess.run(
        [sys.executable, "-m", "llmw.cli", "write", "wiki/concepts/x.md",
         "--reason", "test", "--stdin"],
        cwd=tmp_path,
        input="---\ntitle: X\n---\nbody\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert read_session_state(paths, "cli-env-sess").get("dirty") is False


def test_llmw_search_marks_searched_from_inside_the_command(tmp_path: Path):
    # Same deal for the search gate: only a search that actually ran
    # satisfies it, whatever shell tool (or none) invoked it.
    paths = init_project(tmp_path)
    rebuild(paths)
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "cli-search-sess"}

    result = subprocess.run(
        [sys.executable, "-m", "llmw.cli", "search", "anything"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert read_session_state(paths, "cli-search-sess").get("searched") is True


def test_pretooluse_shell_guard_without_cwd_resolves_against_the_project_root(tmp_path: Path):
    # A payload with no `cwd` must not fall back to the hook process's own
    # working directory — relative tokens are resolved against the project.
    init_project(tmp_path)
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi > wiki/concepts/x.md"},
        "session_id": "sess-nocwd",
    }
    payload_with_cwd = {**payload, "cwd": str(tmp_path)}

    # find_project_root still needs a cwd to locate the project at all, so
    # run it from inside the project and drop only the payload field.
    import os

    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = evaluate_pretooluse(payload)
    finally:
        os.chdir(previous)

    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert evaluate_pretooluse(payload_with_cwd) is not None
