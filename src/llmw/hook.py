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

    paths = ProjectPaths.for_project_root(root)
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
