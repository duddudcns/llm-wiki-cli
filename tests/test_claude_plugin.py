"""Guards the Claude Code / ZCode hook manifest against Windows dispatch drift.

A hook host that hands a bare `.sh` path to Windows resolves it through
ShellExecute: the file's associated application is launched instead of
being run, and that application never inherits the hook's stdin/stdout
pipe, so the hook times out on every matched tool call. Claude Code
itself dispatches hooks through a POSIX shell and is unaffected, but
ZCode goes through cmd.exe and is not.

The fix is not to prefix the script paths with `bash`: on a stock Windows
box `bash` resolves to `C:\\Windows\\System32\\bash.exe` (the WSL
launcher), because System32 precedes Git's `bin` on PATH — and Git for
Windows does not put `bash.exe` on PATH at all by default. So every event
whose wrapper was a pass-through now calls `llmw hook <event>` directly.
Only SessionStart still needs a script, because its self-install
bootstrap runs before `llmw` exists.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]

PLUGIN = ROOT / "plugin"

# `cmd || exit 0` short-circuits identically in cmd.exe and POSIX sh, so a
# missing `llmw` (before SessionStart's self-install finishes, or after it
# failed) still fails open instead of surfacing exit 127 on every hook.
EXPECTED_COMMANDS = {
    "SessionStart": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"',
    "UserPromptSubmit": "llmw hook userpromptsubmit || exit 0",
    "PreToolUse": "llmw hook pretooluse || exit 0",
    "Stop": "llmw hook stop || exit 0",
}

# Unchanged by the dispatch fix. Bash/PowerShell are matched because a raw
# shell write into wiki/ or raw/ has to be gated too, and Claude's matcher
# cannot express "only when the command touches those paths".
EXPECTED_MATCHER_TOOLS = {
    "Edit",
    "Write",
    "NotebookEdit",
    "Bash",
    "PowerShell",
    "mcp__llm-wiki__llmw_search",
    "mcp__llm-wiki__llmw_write",
    "mcp__llm-wiki__llmw_edit",
    "mcp__llm-wiki__llmw_patch",
    "mcp__llm-wiki__llmw_archive",
}


def _hooks() -> dict:
    return json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))


def test_claude_hooks_never_dispatch_a_bare_script_path() -> None:
    hooks = _hooks()["hooks"]
    assert set(hooks) == set(EXPECTED_COMMANDS)

    for event, expected in EXPECTED_COMMANDS.items():
        entries = hooks[event]
        assert len(entries) == 1, f"{event} should declare exactly one entry"
        commands = [h["command"] for h in entries[0]["hooks"]]
        assert commands == [expected], f"{event} command drifted: {commands}"


def test_claude_hook_commands_are_not_bare_sh_paths() -> None:
    for event, command in EXPECTED_COMMANDS.items():
        # A command may *mention* a .sh file, but never as the executable:
        # that is the ShellExecute path this manifest exists to avoid.
        assert not command.startswith("${CLAUDE_PLUGIN_ROOT}"), event
        if ".sh" in command:
            assert command.startswith("bash "), event


def test_pretooluse_matcher_still_covers_every_gated_tool() -> None:
    pretooluse = _hooks()["hooks"]["PreToolUse"][0]
    assert set(pretooluse["matcher"].split("|")) == EXPECTED_MATCHER_TOOLS


def test_pretooluse_and_stop_keep_their_timeouts() -> None:
    hooks = _hooks()["hooks"]
    assert hooks["UserPromptSubmit"][0]["hooks"][0]["timeout"] == 5
    assert hooks["PreToolUse"][0]["hooks"][0]["timeout"] == 10
    assert hooks["Stop"][0]["hooks"][0]["timeout"] == 10


def test_session_start_wrapper_still_ships_and_fails_open() -> None:
    # SessionStart is the one event that cannot call `llmw` directly: the
    # script is what installs it.
    script = PLUGIN / "hooks/session-start.sh"
    assert script.is_file()
    assert "llmw hook session-start" in script.read_text(encoding="utf-8")


CONVERTED_EVENTS = ("UserPromptSubmit", "PreToolUse", "Stop")

HARMLESS_PAYLOAD = '{"tool_name":"Bash","tool_input":{"command":"echo ok"}}'


@pytest.mark.parametrize("event", CONVERTED_EVENTS)
def test_fail_open_clause_holds_in_the_platform_shell(event: str) -> None:
    # Asserting the string `|| exit 0` is not the same as knowing the shell
    # this actually runs in honours it. cmd.exe and POSIX sh short-circuit
    # `||` identically; Windows PowerShell 5.1 would not, so if a host ever
    # dispatched hooks through it this test is what would catch the drift.
    command = EXPECTED_COMMANDS[event].replace("llmw ", "llmw_not_installed_xyz ", 1)
    result = subprocess.run(
        command,
        input=HARMLESS_PAYLOAD,
        cwd=ROOT,
        shell=True,
        capture_output=True,
        text=True,
        # cmd.exe writes its "not recognized" message in the console
        # codepage, which is not UTF-8 on a localized Windows.
        errors="replace",
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"{event} does not fail open when llmw is missing: {result.returncode} "
        f"{result.stderr[:200]}"
    )


@pytest.mark.skipif(shutil.which("llmw") is None, reason="llmw is not on PATH")
def test_pretooluse_command_runs_end_to_end_in_the_platform_shell(tmp_path: Path) -> None:
    # Runs the real CLI, so keep it out of the repo working tree: the
    # payload names no wiki path, but the hook records session state.
    result = subprocess.run(
        EXPECTED_COMMANDS["PreToolUse"],
        input=HARMLESS_PAYLOAD,
        cwd=tmp_path,
        shell=True,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[:200]


def test_retained_wrappers_still_fail_open() -> None:
    # No longer referenced by hooks.json, but kept as manual entry points
    # and as a fallback for hosts that can only take a script path.
    for name in ("pre-tool-use.sh", "stop.sh", "user-prompt-submit.sh"):
        text = (PLUGIN / "hooks" / name).read_text(encoding="utf-8")
        assert "|| true" in text, name
        assert "exit 0" in text, name
