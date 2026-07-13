import time
from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.locks import LockedError, acquire_lock


def test_acquire_lock_blocks_concurrent_acquisition(tmp_path: Path):
    paths = init_project(tmp_path)
    with acquire_lock(paths, "index"):
        with pytest.raises(LockedError):
            with acquire_lock(paths, "index"):
                pass


def test_acquire_lock_releases_on_exit(tmp_path: Path):
    paths = init_project(tmp_path)
    with acquire_lock(paths, "index"):
        pass
    # Released — a second acquisition must succeed without raising.
    with acquire_lock(paths, "index"):
        pass


def test_acquire_lock_releases_on_exception(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(ValueError):
        with acquire_lock(paths, "index"):
            raise ValueError("boom")
    with acquire_lock(paths, "index"):
        pass


def test_acquire_lock_takes_over_stale_lock(tmp_path: Path):
    paths = init_project(tmp_path)
    paths.locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = paths.locks_dir / "index.lock"
    lock_path.write_text(str(time.time()), encoding="utf-8")
    stale_time = time.time() - 120
    import os

    os.utime(lock_path, (stale_time, stale_time))

    with acquire_lock(paths, "index"):
        pass


def test_acquire_lock_is_atomic_create_not_check_then_write(tmp_path: Path, monkeypatch):
    # Regression: a prior implementation used `exists()` then a separate
    # `write_text()`, a TOCTOU window where two processes could both pass
    # the check before either had written the file. Simulate that race by
    # having a second acquirer's create attempt run *inside* the first
    # acquirer's `_create_lock_file` call (i.e. before the first process
    # would have finished creating it under the old two-step scheme).
    paths = init_project(tmp_path)
    import llmw.locks as locks_module

    real_create = locks_module._create_lock_file
    calls = []

    def racing_create(lock_path):
        calls.append(lock_path)
        if len(calls) == 1:
            # A second, concurrent acquirer tries first.
            second = real_create(lock_path)
            assert second is not None
            import os

            os.close(second)
        return real_create(lock_path)

    monkeypatch.setattr(locks_module, "_create_lock_file", racing_create)

    with pytest.raises(LockedError):
        with acquire_lock(paths, "index"):
            pass
