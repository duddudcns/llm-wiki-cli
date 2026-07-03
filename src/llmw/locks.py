"""Simple advisory file locks under .llmw/locks/ to guard against concurrent
`llmw` invocations stepping on each other. Not a distributed lock — just
enough to avoid two local processes racing on the same write.
"""

from __future__ import annotations

import time
from contextlib import contextmanager

from llmw.paths import ProjectPaths

STALE_SECONDS = 60


class LockedError(RuntimeError):
    pass


@contextmanager
def acquire_lock(paths: ProjectPaths, name: str):
    paths.locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = paths.locks_dir / f"{name}.lock"

    if lock_path.exists():
        age = time.time() - lock_path.stat().st_mtime
        if age < STALE_SECONDS:
            raise LockedError(
                f'"{name}" is locked (age {age:.1f}s). '
                "Another llmw process may be running; if not, delete "
                f"{lock_path} and retry."
            )
        # Stale lock: a previous process likely crashed. Proceed, but leave
        # a trace by overwriting it below.

    lock_path.write_text(str(time.time()), encoding="utf-8", newline="\n")
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)
