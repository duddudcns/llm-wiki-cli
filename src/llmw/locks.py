"""Simple advisory file locks under .llmw/locks/ to guard against concurrent
`llmw` invocations stepping on each other. Not a distributed lock — just
enough to avoid two local processes racing on the same write.
"""

from __future__ import annotations

import os
import secrets
import time
from contextlib import contextmanager

from llmw.paths import ProjectPaths

STALE_SECONDS = 60


class LockedError(RuntimeError):
    pass


def _create_lock_file(lock_path) -> int | None:
    """Atomically create the lock file, or return None if it already
    exists. O_CREAT|O_EXCL is a single kernel syscall — unlike an
    `exists()` check followed by a separate `write_text()`, two processes
    can never both believe they created it."""
    try:
        return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None


def _lock_age(lock_path) -> float | None:
    try:
        return time.time() - lock_path.stat().st_mtime
    except FileNotFoundError:
        return None


def _read_lock_token(lock_path) -> str | None:
    try:
        return lock_path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None


@contextmanager
def acquire_lock(paths: ProjectPaths, name: str):
    paths.locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = paths.locks_dir / f"{name}.lock"

    fd = _create_lock_file(lock_path)
    took_over = False
    if fd is None:
        age = _lock_age(lock_path)
        if age is not None and age < STALE_SECONDS:
            raise LockedError(
                f'"{name}" is locked (age {age:.1f}s). '
                "Another llmw process may be running; if not, delete "
                f"{lock_path} and retry."
            )
        # Stale (or the file vanished between the failed create and here,
        # e.g. the holder just released it) — take it over. On Windows,
        # unlink() can raise if another process still has the file open
        # (no FileNotFoundError-style "it's fine" case there) — treat that
        # the same as "still locked" rather than crashing.
        try:
            lock_path.unlink(missing_ok=True)
        except OSError as exc:
            raise LockedError(
                f'"{name}" appears stale but could not be taken over '
                f"(another process may still hold it): {exc}"
            ) from exc
        fd = _create_lock_file(lock_path)
        if fd is None:
            # Another process won the race to recreate it just now.
            age = _lock_age(lock_path) or 0.0
            raise LockedError(
                f'"{name}" is locked (age {age:.1f}s). '
                "Another llmw process may be running; if not, delete "
                f"{lock_path} and retry."
            )
        took_over = True

    # A per-attempt random token, not just a timestamp: two processes that
    # both observe the same stale lock can both reach this point and both
    # believe they took it over (each one's unlink()+create() pair is
    # atomic on its own, but the *pair* isn't atomic against a concurrent
    # pair). Writing a unique token and reading it back below detects the
    # case where a second process's takeover unlinked and replaced ours
    # after we wrote it.
    token = f"{time.time()} {os.getpid()} {secrets.token_hex(8)}"
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(token)

    if took_over and _read_lock_token(lock_path) != token:
        raise LockedError(
            f'"{name}" was taken over by another process during a '
            "concurrent stale-lock race. Retry."
        )

    try:
        yield
    finally:
        # Only release the lock if it's still the one we created — avoids
        # deleting a lock a different process has since taken over.
        if _read_lock_token(lock_path) == token:
            lock_path.unlink(missing_ok=True)
