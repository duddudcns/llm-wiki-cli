"""Logic behind `llmw hook pretooluse` / `llmw hook session-start` /
`llmw hook userpromptsubmit` / `llmw hook stop` — the Claude Code plugin's
PreToolUse, SessionStart, UserPromptSubmit, and Stop hooks (see
`plugin/hooks/hooks.json`).

Claude Code's native Edit/Write/NotebookEdit tools know nothing about
`llmw`: they can silently overwrite `raw/` (meant to be immutable) or
mutate `wiki/*.md` without the `--reason` audit log, frontmatter
validation, or automatic backup that `llmw write`/`edit`/`patch` provide.
`evaluate_pretooluse` redirects those calls back to the sanctioned
commands instead — and, since a shell redirect or `Set-Content` would
otherwise walk right around a guard that only watches the native tools,
asks (never denies: a command string is guesswork) before a Bash/
PowerShell command that looks like it writes into `wiki/*.md` or `raw/**`.
`evaluate_sessionstart` and `evaluate_userpromptsubmit` just remind the
agent the wiki exists and is worth checking.

`evaluate_pretooluse` also carries two session-scoped soft gates, tracked
via `llmw.hook_state`:

- **Search-before-work**: the first real source-file edit (outside
  `wiki/`/`raw/`/`.llmw/`) in a session that hasn't run `llmw search` yet
  gets a one-time "ask" permission response instead of silently
  proceeding. The agent can confirm and continue — this is a nudge that
  forces a moment of judgment, not a hard block.
- **Update-after-work**: every real source-file edit marks the session
  "dirty"; a Bash/PowerShell call running `llmw write`/`edit`/`patch`/
  `archive`, or a direct call to this plugin's own
  `mcp__llm-wiki__llmw_write`/`llmw_edit`/`llmw_patch`/`llmw_archive` MCP
  tools (a Claude Code session can have that server registered too, not
  just Codex — see `codex_hook.py`), clears it. A successful `llmw`
  mutation also clears it from inside the command itself, keyed off
  `CLAUDE_CODE_SESSION_ID` (see `hook_state.clear_dirty_for_env_session`) —
  that path doesn't depend on this module recognizing the tool name or
  parsing the command at all. `evaluate_stop` (the Stop hook) uses this to
  remind the agent to update the wiki before ending a turn that changed
  source but never touched the wiki.

`evaluate_pretooluse`'s wiki/raw guard fails open: anything that isn't a
mutation of `wiki/*.md` or `raw/**` inside a real llmw project (including
"no `.llmw` project found at all") returns `None` from that part of the
logic. The two soft gates above fail open the same way outside a real
llmw project, and can each be turned off independently via
`.llmw/config.toml`.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmw.hook_state import read_session_state, write_session_state
from llmw.indexer import load_project_config
from llmw.paths import ProjectNotFoundError, ProjectPaths, find_project_root
from llmw.status import build_status

_GUARDED_TOOLS = {"Edit", "Write", "NotebookEdit"}
# Both shell tools available in a Claude Code session (Bash, and the
# PowerShell tool offered on Windows) get the same command-string
# treatment below — neither is gated, both are only watched for
# `llmw search`/`llmw write|edit|patch|archive`.
_SHELL_TOOLS = {"Bash", "PowerShell"}

# This plugin's own MCP server (see `mcp_server.py`) exposes these tools.
# Nothing in the Claude Code plugin manifest registers that server today,
# but a project can wire it up itself (or a future release of this plugin
# could) — if so, calls to it must clear the same session-state flags a
# shelled-out `llmw write`/`edit`/... does, or `evaluate_stop` nags about
# an "un-updated" wiki that was in fact just updated through the MCP tool
# instead of a shell command. `codex_hook.py` imports these two names
# rather than redefining its own copy, so the two integrations can't drift.
WIKI_MCP_SEARCH_TOOL = "mcp__llm-wiki__llmw_search"
WIKI_MCP_MUTATE_TOOLS = {
    "mcp__llm-wiki__llmw_write",
    "mcp__llm-wiki__llmw_edit",
    "mcp__llm-wiki__llmw_patch",
    "mcp__llm-wiki__llmw_archive",
}

# Heuristic, not a real shell parser: matches `llmw <subcommand>` and the
# `llmw.exe <subcommand>` (Windows, e.g. a venv's Scripts/llmw.exe with no
# global `llmw` on PATH) / `python -m llmw[.cli] <subcommand>` /
# `--root <path>` variants seen in the docs (an env-var prefix like
# `LLMW_ROOT=... llmw search` or a wrapper like `uv run llmw search`
# already matches — the lookbehind only checks the character immediately
# before this pattern, not the whole prefix).
_LLMW_INVOCATION = r"(?:llmw(?:\.exe)?|python3?\s+-m\s+llmw(?:\.cli)?)"
_ROOT_FLAG = r"(?:\s+--root(?:=\S+|\s+\S+))?"
_LLMW_SEARCH_RE = re.compile(
    rf"(?<![\w-]){_LLMW_INVOCATION}{_ROOT_FLAG}\s+search(?![\w-])"
)
_LLMW_MUTATE_RE = re.compile(
    rf"(?<![\w-]){_LLMW_INVOCATION}{_ROOT_FLAG}\s+(write|edit|patch|archive)(?![\w-])"
)

# Prose that merely *mentions* `llmw write` — a heredoc body being piped
# into `llmw write --stdin`, a commit message, a `--reason` string — used
# to clear the update gate as if the command had actually run. Heredoc /
# here-string bodies and quoted strings are stripped before matching.
# ponytail: string scrub, not a shell parser — `bash -c 'llmw write ...'`
# is now missed (fails toward one extra reminder, never a silent clear);
# tokenize properly only if that turns out to bite.
_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?^\s*\2\s*$", re.DOTALL | re.MULTILINE)
_PS_HERESTRING_RE = re.compile(r"@(['\"]).*?^\1@", re.DOTALL | re.MULTILINE)
_QUOTED_RE = re.compile(r"'[^']*'|\"[^\"]*\"", re.DOTALL)


def _strip_shell_literals(command: str) -> str:
    """Blank out heredoc bodies and quoted strings so only real command
    text is matched against the `llmw` patterns above. Heredocs first —
    quote-stripping would otherwise eat the `'EOF'` delimiter."""
    for pattern in (_HEREDOC_RE, _PS_HERESTRING_RE):
        command = pattern.sub(" ", command)
    # A quoted string collapses to a single placeholder token rather than
    # whitespace: it was one argument, and `llmw --root "<path>" search`
    # still has to read as an argument-shaped thing to match.
    return _QUOTED_RE.sub("_", command)


# The wiki/raw guard below only reaches native Edit/Write calls; a shell
# command can rewrite `wiki/*.md` with a redirect or `Set-Content` and
# bypass llmw's reason log/validation/backup entirely. These two patterns
# are the "did this command mutate a file, and which paths did it name"
# heuristic that closes the common accidental case.
# ponytail: substring/verb heuristic — `python -c ...`, a variable-held
# path, or an unusual writer slips through. A real bypass can't be stopped
# by command parsing at all; this only has to catch the honest slip.
_SHELL_MUTATION_RE = re.compile(
    r"(?<![\w-])(?:>>?|tee|rm|mv|cp|ln|sed|touch|truncate|dd"
    r"|Set-Content|Add-Content|Clear-Content|Out-File"
    r"|New-Item|Remove-Item|Move-Item|Copy-Item)(?![\w-])",
    re.IGNORECASE,
)
_PATH_TOKEN_RE = re.compile(r"[^\s'\"|;&()<>]+")
# Tokens holding a glob or an unexpanded variable resolve to garbage paths.
_UNRESOLVABLE_CHARS = set("*?[]$%~")


def permission_output(decision: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def _target_path(tool_input: dict) -> str | None:
    return tool_input.get("file_path") or tool_input.get("notebook_path")


def _wiki_edit_message(rel_path: str) -> str:
    return (
        f'Use `llmw edit "{rel_path}" --reason "<why>" --old "<old>" '
        '--new "<new>"`; use `llmw write`, `llmw patch`, or `llmw archive` '
        "when appropriate. Direct `wiki/*.md` edits are blocked."
    )


def _raw_deny_message(rel_path: str) -> str:
    return f'raw/ is immutable: do not modify "{rel_path}".'


def _raw_ask_message(rel_path: str) -> str:
    return f'Creating raw/ source "{rel_path}" requires user confirmation.'


_SEARCH_GATE_MESSAGE = (
    'Search first: `llmw search "<topic>"`, or explicitly judge this task '
    "wiki-irrelevant."
)


def evaluate_pretooluse(payload: dict) -> dict | None:
    tool_name = payload.get("tool_name")

    if tool_name in _SHELL_TOOLS:
        return _evaluate_shell_pretooluse(payload)

    if tool_name == WIKI_MCP_SEARCH_TOOL or tool_name in WIKI_MCP_MUTATE_TOOLS:
        return _evaluate_wiki_mcp_pretooluse(payload, tool_name)

    if tool_name not in _GUARDED_TOOLS:
        return None

    raw_path = _target_path(payload.get("tool_input") or {})
    if not raw_path:
        return None

    try:
        fs_path = Path(raw_path.replace("\\", "/")).resolve()
    except (OSError, ValueError):
        return None

    try:
        root = find_project_root(fs_path.parent)
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    config = load_project_config(paths)
    guard = config.hooks_wiki_guard

    is_raw = paths.is_inside_raw(fs_path)
    is_wiki_md = paths.is_inside_wiki(fs_path) and fs_path.suffix.lower() == ".md"

    if guard != "off":
        if is_raw:
            rel = paths.rel(fs_path)
            if tool_name == "Write" and not fs_path.exists():
                return permission_output("ask", _raw_ask_message(rel))
            return permission_output("deny", _raw_deny_message(rel))

        if is_wiki_md:
            rel = paths.rel(fs_path)
            decision = "ask" if guard == "ask" else "deny"
            return permission_output(decision, _wiki_edit_message(rel))

    if is_raw or paths.is_inside_wiki(fs_path) or paths.is_inside_llmw(fs_path):
        return None

    return _track_source_edit(payload, paths, config)


def _track_source_edit(payload: dict, paths: ProjectPaths, config) -> dict | None:
    """A real source-file edit outside wiki/raw/.llmw: mark the session
    dirty (for the Stop-hook update reminder) and, on the first such edit
    of a session that hasn't searched yet, ask once before proceeding."""
    session_id = payload.get("session_id")
    state = write_session_state(paths, session_id, dirty=True)

    if config.hooks_search_gate == "off":
        return None
    if state.get("searched") or state.get("search_gate_shown"):
        return None

    write_session_state(paths, session_id, search_gate_shown=True)
    return permission_output("ask", _SEARCH_GATE_MESSAGE)


def _evaluate_shell_pretooluse(payload: dict) -> dict | None:
    """Bash/PowerShell calls are watched for `llmw search` (marks the
    session searched) and `llmw write`/`edit`/`patch`/`archive` (marks the
    session's wiki as caught up), and — only when they aren't an llmw
    command themselves — checked for a raw shell write into `wiki/*.md` or
    `raw/**`, which would otherwise walk straight around the guard that
    covers the native Edit/Write tools. Both shell tools use the same
    `tool_input.command` shape, so one implementation covers either."""
    command = (payload.get("tool_input") or {}).get("command")
    if not command or not isinstance(command, str):
        return None
    if "llmw" not in command and not _SHELL_MUTATION_RE.search(command):
        return None

    try:
        root = find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    session_id = payload.get("session_id")
    scrubbed = _strip_shell_literals(command)

    if _LLMW_SEARCH_RE.search(scrubbed):
        write_session_state(paths, session_id, searched=True)
    if _LLMW_MUTATE_RE.search(scrubbed):
        write_session_state(paths, session_id, dirty=False)
        # A sanctioned llmw mutation naming a wiki path is not a bypass.
        return None

    return _guard_shell_wiki_write(paths, command, payload.get("cwd"))


def _guard_shell_wiki_write(paths: ProjectPaths, command: str, cwd: str | None) -> dict | None:
    """Ask before a shell command that looks like it writes to `wiki/*.md`
    or `raw/**`. Always "ask", never "deny", even under
    `wiki_guard = "deny"`: the Edit-tool path knows its exact target, this
    one is guessing from a command string, and a wrong deny breaks a
    workflow with no way out while a wrong ask costs one keystroke."""
    if load_project_config(paths).hooks_wiki_guard == "off":
        return None
    if not _SHELL_MUTATION_RE.search(command):
        return None

    # The hook process's own cwd is not the session's — with no `cwd` in the
    # payload, resolve relative tokens against the project root instead.
    base = Path(cwd) if cwd else paths.project_root
    for token in _PATH_TOKEN_RE.findall(command):
        token = token.strip("'\"")
        if "/" not in token and "\\" not in token:
            continue
        if set(token) & _UNRESOLVABLE_CHARS:
            continue
        try:
            fs_path = (base / token.replace("\\", "/")).resolve()
        except (OSError, ValueError):
            continue
        if paths.is_inside_raw(fs_path):
            return permission_output("ask", _raw_deny_message(paths.rel(fs_path)))
        if paths.is_inside_wiki(fs_path) and fs_path.suffix.lower() == ".md":
            return permission_output("ask", _wiki_edit_message(paths.rel(fs_path)))
    return None


def _evaluate_wiki_mcp_pretooluse(payload: dict, tool_name: str) -> None:
    """A direct call to this plugin's own llm-wiki MCP tools rather than a
    shell-invoked `llmw` command — same session-state bookkeeping as
    `_evaluate_shell_pretooluse`, keyed off the MCP tool name instead of
    parsing a command string."""
    try:
        root = find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    session_id = payload.get("session_id")

    if tool_name == WIKI_MCP_SEARCH_TOOL:
        write_session_state(paths, session_id, searched=True)
    else:
        write_session_state(paths, session_id, dirty=False)
    return None


_NO_PROJECT_HINT = (
    "No llmw wiki here. Run `llmw init` for persistent project knowledge."
)


def evaluate_sessionstart(cwd: str) -> str | None:
    try:
        root = find_project_root(Path(cwd))
    except ProjectNotFoundError:
        return _NO_PROJECT_HINT

    paths = ProjectPaths.for_project_root(root)
    status = build_status(paths)
    # Relative to the project root (not `paths.root`/wiki_root), so this
    # correctly reads "ai-wiki/wiki" when the wiki is nested there.
    wiki_rel = paths.wiki.resolve().relative_to(paths.project_root.resolve()).as_posix()

    if not status.index_exists:
        pages_note = "index not built yet — run `llmw rebuild`"
    else:
        pages_note = f"{status.wiki_page_count} pages indexed"

    return (
        f"llmw wiki: {wiki_rel}/ ({pages_note}). Search with `llmw search`; "
        "change wiki only through `llmw write`/`edit`/`patch`/`archive`."
    )


_PROMPT_REMINDER = (
    "Project wiki available: run `llmw search` before substantive work if relevant."
)

# Below this, a prompt is almost certainly a trivial reply ("ok", "thanks",
# "yes continue") or a slash command with no chance of being wiki-relevant —
# reminding the agent to search there just teaches it to tune the reminder
# out, and can even prompt a pointless `llmw search` call mid-task. This is
# a length check, not a relevance guess: still no keyword-matching.
_TRIVIAL_WORD_THRESHOLD = 4
_TRIVIAL_CHAR_THRESHOLD = 20


def _is_trivial_prompt(prompt: str) -> bool:
    stripped = prompt.strip()
    if stripped.startswith("/"):
        return True
    return (
        len(stripped) < _TRIVIAL_CHAR_THRESHOLD
        and len(stripped.split()) < _TRIVIAL_WORD_THRESHOLD
    )


def evaluate_userpromptsubmit(payload: dict) -> str | None:
    """UserPromptSubmit hook: on every non-trivial user message, remind the
    agent to search the wiki itself before starting work. Deliberately does
    not try to guess relevance by keyword-matching the prompt text — a
    mechanical match can miss a note that's phrased differently, and a
    false "no related notes" signal is worse than a generic reminder; the
    actual search is left to the agent's own judgment. Fails open (returns
    None) outside a real llmw project or for a trivially short prompt.
    """
    prompt = payload.get("prompt")
    if not prompt or not isinstance(prompt, str):
        return None

    if _is_trivial_prompt(prompt):
        return None

    try:
        find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    return _PROMPT_REMINDER


_UPDATE_GATE_MESSAGE = (
    "Source changed: record durable knowledge with `llmw write`/`edit`/"
    "`patch` and `--reason`, or explicitly decide no wiki update is needed."
)


def evaluate_stop(payload: dict) -> dict | None:
    """Stop hook: fires at the end of every agent turn. If source files
    changed this session since the wiki was last touched, blocks the stop
    once with a reminder — relies on Claude Code's `stop_hook_active` flag
    (set on the forced-continuation retry) to fire at most once per turn
    rather than looping. Fails open outside a real llmw project or once
    the update gate is turned off."""
    if payload.get("stop_hook_active"):
        return None

    try:
        root = find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    config = load_project_config(paths)
    if config.hooks_update_gate == "off":
        return None

    state = read_session_state(paths, payload.get("session_id"))
    if not state.get("dirty"):
        return None

    return {"decision": "block", "reason": _UPDATE_GATE_MESSAGE}
