"""Per-session state for the PreToolUse/Stop hooks.

Tracks, per Claude Code session, whether the agent has run `llmw search`
yet and whether source files have changed since the wiki was last touched
(`llmw write`/`edit`/`patch`/`archive`). Backs the search-before-work soft
gate and the update-after-work reminder in `llmw.hook`.

Each session gets its own small JSON file under `.llmw/sessions/<id>.json`
so concurrent sessions never clobber each other's state. Session ids come
from Claude Code and land directly in a filesystem path, so they're
sanitized before use; anything that doesn't look like a safe token is
treated as "no session" (state reads as empty, writes are silently
skipped) rather than trusted.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from llmw.paths import ProjectPaths

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_STALE_AFTER_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _sanitize_session_id(session_id: str | None) -> str | None:
    if not session_id or not isinstance(session_id, str):
        return None
    if not _SESSION_ID_RE.match(session_id):
        return None
    return session_id


def _sessions_dir(paths: ProjectPaths) -> Path:
    return paths.llmw_dir / "sessions"


def _session_path(paths: ProjectPaths, session_id: str) -> Path:
    return _sessions_dir(paths) / f"{session_id}.json"


def read_session_state(paths: ProjectPaths, session_id: str | None) -> dict:
    safe_id = _sanitize_session_id(session_id)
    if safe_id is None:
        return {}
    try:
        raw = _session_path(paths, safe_id).read_text(encoding="utf-8")
        state = json.loads(raw)
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def write_session_state(paths: ProjectPaths, session_id: str | None, **updates: object) -> dict:
    """Merge `updates` into the session's stored state and persist it.

    Silently no-ops (returns `{}`) when `session_id` isn't a safe token or
    the write fails — a hook must never crash a tool call over bookkeeping.
    """
    safe_id = _sanitize_session_id(session_id)
    if safe_id is None:
        return {}

    state = read_session_state(paths, safe_id)
    state.update(updates)

    session_dir = _sessions_dir(paths)
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        _session_path(paths, safe_id).write_text(json.dumps(state), encoding="utf-8")
        _prune_stale_sessions(session_dir)
    except OSError:
        return state
    return state


def _prune_stale_sessions(session_dir: Path) -> None:
    cutoff = time.time() - _STALE_AFTER_SECONDS
    try:
        entries = list(session_dir.iterdir())
    except OSError:
        return
    for entry in entries:
        try:
            if entry.suffix == ".json" and entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            continue
