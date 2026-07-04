"""Logic behind `llmw hook pretooluse` / `llmw hook session-start` — the
Claude Code plugin's PreToolUse and SessionStart hooks (see
`plugin/hooks/hooks.json`).

Claude Code's native Edit/Write/NotebookEdit tools know nothing about
`llmw`: they can silently overwrite `raw/` (meant to be immutable) or
mutate `wiki/*.md` without the `--reason` audit log, frontmatter
validation, or automatic backup that `llmw write`/`edit`/`patch` provide.
This module redirects those calls back to the sanctioned commands instead.

Every function here fails open: anything that isn't a mutation of
`wiki/*.md` or `raw/**` inside a real llmw project (including "no `.llmw`
project found at all") returns `None` ("no opinion") — never a decision.
The guard can only ever fire for a native edit aimed at a real llmw
project's `wiki/*.md` or `raw/`.
"""

from __future__ import annotations

from pathlib import Path

from llmw.indexer import load_project_config
from llmw.paths import ProjectNotFoundError, ProjectPaths, find_project_root
from llmw.status import build_status

_GUARDED_TOOLS = {"Edit", "Write", "NotebookEdit"}


def _permission_output(decision: str, reason: str) -> dict:
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


def evaluate_pretooluse(payload: dict) -> dict | None:
    tool_name = payload.get("tool_name")
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

    paths = ProjectPaths(root=root)
    config = load_project_config(paths)
    guard = config.hooks_wiki_guard
    if guard == "off":
        return None

    if paths.is_inside_raw(fs_path):
        rel = paths.rel(fs_path)
        if tool_name == "Write" and not fs_path.exists():
            return _permission_output("ask", _raw_ask_message(rel))
        return _permission_output("deny", _raw_deny_message(rel))

    if paths.is_inside_wiki(fs_path) and fs_path.suffix.lower() == ".md":
        rel = paths.rel(fs_path)
        decision = "ask" if guard == "ask" else "deny"
        return _permission_output(decision, _wiki_edit_message(rel))

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

    paths = ProjectPaths(root=root)
    status = build_status(paths)
    wiki_rel = paths.rel(paths.wiki)

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
