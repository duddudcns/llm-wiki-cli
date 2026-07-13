"""Logic behind `llmw hook pretooluse` / `llmw hook session-start` /
`llmw hook userpromptsubmit` / `llmw hook stop` — the Claude Code plugin's
PreToolUse, SessionStart, UserPromptSubmit, and Stop hooks (see
`plugin/hooks/hooks.json`).

Claude Code's native Edit/Write/NotebookEdit tools know nothing about
`llmw`: they can silently overwrite `raw/` (meant to be immutable) or
mutate `wiki/*.md` without the `--reason` audit log, frontmatter
validation, or automatic backup that `llmw write`/`edit`/`patch` provide.
`evaluate_pretooluse` redirects those calls back to the sanctioned
commands instead; `evaluate_sessionstart` and `evaluate_userpromptsubmit`
just remind the agent the wiki exists and is worth checking.

`evaluate_pretooluse` also carries two session-scoped soft gates, tracked
via `llmw.hook_state`:

- **Search-before-work**: the first real source-file edit (outside
  `wiki/`/`raw/`/`.llmw/`) in a session that hasn't run `llmw search` yet
  gets a one-time "ask" permission response instead of silently
  proceeding. The agent can confirm and continue — this is a nudge that
  forces a moment of judgment, not a hard block.
- **Update-after-work**: every real source-file edit marks the session
  "dirty"; a Bash call running `llmw write`/`edit`/`patch`/`archive`
  clears it. `evaluate_stop` (the Stop hook) uses this to remind the
  agent to update the wiki before ending a turn that changed source but
  never touched the wiki.

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
# Heuristic, not a real shell parser: matches `llmw <subcommand>` and the
# `python -m llmw[.cli] <subcommand>` / `--root <path>` variants seen in
# the docs (an env-var prefix like `LLMW_ROOT=... llmw search` or a
# wrapper like `uv run llmw search` already matches — the lookbehind only
# checks the character immediately before this pattern, not the whole
# prefix).
_LLMW_INVOCATION = r"(?:llmw|python3?\s+-m\s+llmw(?:\.cli)?)"
_ROOT_FLAG = r"(?:\s+--root(?:=\S+|\s+\S+))?"
_LLMW_SEARCH_RE = re.compile(
    rf"(?<![\w-]){_LLMW_INVOCATION}{_ROOT_FLAG}\s+search(?![\w-])"
)
_LLMW_MUTATE_RE = re.compile(
    rf"(?<![\w-]){_LLMW_INVOCATION}{_ROOT_FLAG}\s+(write|edit|patch|archive)(?![\w-])"
)


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
        "Direct edits to wiki pages skip llmw's frontmatter validation, "
        "backup, and audit log. Rerun the change as:\n"
        f'llmw edit "{rel_path}" --reason "<why>" --old "<exact old text>" '
        '--new "<new text>"\n'
        "(new page / full rewrite: `llmw write <path> --reason ... --stdin`; "
        "structural diff: `llmw patch`; delete: `llmw archive`.)\n"
        'Project owners can disable this guard: set wiki_guard = "off" '
        "under [hooks] in .llmw/config.toml."
    )


def _raw_deny_message(rel_path: str) -> str:
    return (
        f'raw/ is immutable source material ("{rel_path}"); llmw and its '
        "agents never modify it. If the user explicitly wants this file "
        "changed, they must do it manually."
    )


def _raw_ask_message(rel_path: str) -> str:
    return (
        f'Creating a new file under raw/ ("{rel_path}", user-curated source '
        "material) — confirm this was actually requested before proceeding."
    )


_SEARCH_GATE_MESSAGE = (
    "You haven't run `llmw search` yet this session. Before this edit, "
    "search the wiki for prior context on this topic "
    '(`llmw search "<topic>"`) — or if you\'ve already judged this task '
    "has no wiki-relevant history, confirm that and proceed. Project "
    'owners can disable this: set search_gate = "off" under [hooks] in '
    ".llmw/config.toml."
)


def evaluate_pretooluse(payload: dict) -> dict | None:
    tool_name = payload.get("tool_name")

    if tool_name == "Bash":
        return _evaluate_bash_pretooluse(payload)

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


def _evaluate_bash_pretooluse(payload: dict) -> None:
    """Bash calls are never gated here — only watched for `llmw search`
    (marks the session searched) and `llmw write`/`edit`/`patch`/`archive`
    (marks the session's wiki as caught up with its source edits)."""
    command = (payload.get("tool_input") or {}).get("command")
    if not command or not isinstance(command, str) or "llmw" not in command:
        return None

    try:
        root = find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    session_id = payload.get("session_id")

    if _LLMW_SEARCH_RE.search(command):
        write_session_state(paths, session_id, searched=True)
    if _LLMW_MUTATE_RE.search(command):
        write_session_state(paths, session_id, dirty=False)
    return None


_NO_PROJECT_HINT = (
    "No llmw wiki initialized in this project yet. Run `llmw init` if you "
    "want persistent, searchable project knowledge (decisions, docs, "
    "backlinks) tracked here."
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
        f"This project has an llmw wiki at {wiki_rel}/ ({pages_note}). "
        "Search it first (`llmw search`) before answering from memory or "
        "re-reading everything by hand. Mutate wiki pages only via `llmw "
        "write`/`edit`/`patch`/`archive` — never native file-edit tools."
    )


_PROMPT_REMINDER = (
    "Reminder: this project has an llmw wiki. Search it first (`llmw "
    'search "<topic>"`) before starting this request, in case it touches a '
    "prior decision, a past mistake, or existing docs."
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
    "Source files changed this turn but the wiki hasn't been touched "
    "since. Before finishing, run `llmw write`/`edit`/`patch` to record "
    "what changed and why — or explicitly decide this change doesn't "
    'warrant a wiki update. Project owners can disable this: set '
    'update_gate = "off" under [hooks] in .llmw/config.toml.'
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
