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
import os
import re
import time
from pathlib import Path

from llmw.paths import ProjectPaths

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_STALE_AFTER_SECONDS = 7 * 24 * 60 * 60  # 7 days
_LOCK_WAIT_SECONDS = 0.5
_LOCK_STALE_SECONDS = 5


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


def _acquire_session_lock(lock_path: Path) -> int | None:
    """Best-effort mutual exclusion for a session-state read-modify-write.

    Never blocks for long and never raises: two hook invocations for the
    same session (concurrent tool calls, or a Stop hook racing a lingering
    Bash-backed PreToolUse hook) can otherwise both read the same state,
    apply their own update, and have the later write silently clobber the
    earlier one's flag. If the lock can't be acquired within
    `_LOCK_WAIT_SECONDS` (e.g. a crashed process left it stale-but-young),
    the caller proceeds unlocked rather than block or fail a hook.
    """
    deadline = time.time() + _LOCK_WAIT_SECONDS
    while True:
        try:
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                age = None
            if age is not None and age > _LOCK_STALE_SECONDS:
                try:
                    lock_path.unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            if time.time() >= deadline:
                return None
            time.sleep(0.01)


def write_session_state(paths: ProjectPaths, session_id: str | None, **updates: object) -> dict:
    """Merge `updates` into the session's stored state and persist it.

    Silently no-ops (returns `{}`) when `session_id` isn't a safe token or
    the write fails — a hook must never crash a tool call over bookkeeping.
    """
    safe_id = _sanitize_session_id(session_id)
    if safe_id is None:
        return {}

    session_dir = _sessions_dir(paths)
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return read_session_state(paths, safe_id)

    lock_fd = _acquire_session_lock(session_dir / f"{safe_id}.lock")
    try:
        state = read_session_state(paths, safe_id)
        state.update(updates)
        try:
            _session_path(paths, safe_id).write_text(json.dumps(state), encoding="utf-8")
            _prune_stale_sessions(session_dir)
        except OSError:
            return state
        return state
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            try:
                (session_dir / f"{safe_id}.lock").unlink(missing_ok=True)
            except OSError:
                pass


def _prune_stale_sessions(session_dir: Path) -> None:
    cutoff = time.time() - _STALE_AFTER_SECONDS
    try:
        entries = list(session_dir.iterdir())
    except OSError:
        return
    for entry in entries:
        try:
            if entry.suffix in (".json", ".lock") and entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            continue
