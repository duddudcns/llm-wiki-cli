"""Logic behind `llmw hook codex-pretooluse` / `llmw hook codex-stop` — the
Codex CLI plugin's PreToolUse and Stop hooks (see
`plugins/llm-wiki/hooks/hooks.json`).

Codex's hook payload/event model closely mirrors Claude Code's: the same
`session_id`/`cwd`/`tool_name`/`tool_input`/`stop_hook_active` fields, and
the same PreToolUse `permissionDecision` / Stop `decision: "block"` output
shapes as [[hook.py]]. What differs is the tool surface: Codex has no CLI
equivalent of `llmw` for the agent to shell out to, so file edits go
through the `apply_patch` tool and wiki search/write go through this
plugin's own MCP tools (`mcp__llm-wiki__llmw_search`,
`mcp__llm-wiki__llmw_write`) rather than a Bash command containing the
literal string "llmw". This module ports `hook.py`'s session-scoped
search-before-work / update-after-work soft gates to that tool surface,
sharing the same `llmw.hook_state` session store (session ids never
collide across platforms, so one project can be worked on from both a
Claude Code and a Codex session without cross-talk).

Unlike the Claude Code integration, there is no wiki/raw PreToolUse guard
here: wiki mutations already only happen through the validated
`llmw_write` MCP tool in the intended Codex workflow — there's no
separate `llmw_edit`/`patch`/`archive` MCP tool to guard around — so an
`apply_patch` call is treated as "real work" for gating purposes without
inspecting its target path.
"""

from __future__ import annotations

from pathlib import Path

from llmw.hook import permission_output
from llmw.hook_state import read_session_state, write_session_state
from llmw.indexer import load_project_config
from llmw.paths import ProjectNotFoundError, ProjectPaths, find_project_root

_SOURCE_EDIT_TOOLS = {"apply_patch"}
_SEARCH_TOOL = "mcp__llm-wiki__llmw_search"
_WRITE_TOOL = "mcp__llm-wiki__llmw_write"
_WATCHED_TOOLS = _SOURCE_EDIT_TOOLS | {_SEARCH_TOOL, _WRITE_TOOL}

_SEARCH_GATE_MESSAGE = (
    "You haven't called the llm-wiki search tool yet this session. Before "
    "this edit, call `llmw_search` for prior context on this topic — or "
    "if you've already judged this task has no wiki-relevant history, "
    'confirm that and proceed. Project owners can disable this: set '
    'search_gate = "off" under [hooks] in .llmw/config.toml.'
)

_UPDATE_GATE_MESSAGE = (
    "Source files changed this turn but the wiki hasn't been touched "
    "since. Before finishing, call `llmw_write` with a meaningful reason "
    "to record what changed and why — or explicitly decide this change "
    'doesn\'t warrant a wiki update. Project owners can disable this: set '
    'update_gate = "off" under [hooks] in .llmw/config.toml.'
)


def evaluate_codex_pretooluse(payload: dict) -> dict | None:
    tool_name = payload.get("tool_name")
    if tool_name not in _WATCHED_TOOLS:
        return None

    try:
        root = find_project_root(Path(payload.get("cwd") or "."))
    except ProjectNotFoundError:
        return None

    paths = ProjectPaths.for_project_root(root)
    session_id = payload.get("session_id")

    if tool_name == _SEARCH_TOOL:
        write_session_state(paths, session_id, searched=True)
        return None
    if tool_name == _WRITE_TOOL:
        write_session_state(paths, session_id, dirty=False)
        return None

    # tool_name == "apply_patch": a real source-file edit.
    config = load_project_config(paths)
    state = write_session_state(paths, session_id, dirty=True)
    if config.hooks_search_gate == "off":
        return None
    if state.get("searched") or state.get("search_gate_shown"):
        return None
    write_session_state(paths, session_id, search_gate_shown=True)
    return permission_output("ask", _SEARCH_GATE_MESSAGE)


def evaluate_codex_stop(payload: dict) -> dict | None:
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
