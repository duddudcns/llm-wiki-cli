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


def test_concurrent_stale_lock_takeover_only_one_winner(tmp_path: Path, monkeypatch):
    # Two processes both observe the *same* stale lock and both attempt
    # takeover. Each individual unlink()+create() pair is atomic, but the
    # pair-of-pairs isn't: process A can finish writing its fresh lock only
    # to have process B (racing off the same stale observation) unlink A's
    # fresh lock and install its own right before A verifies it still owns
    # what it wrote. A must detect the mismatch and raise LockedError
    # instead of proceeding alongside B.
    import os as os_module

    paths = init_project(tmp_path)
    paths.locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = paths.locks_dir / "index.lock"
    lock_path.write_text("stale", encoding="utf-8")
    stale_time = time.time() - 120
    os_module.utime(lock_path, (stale_time, stale_time))

    import llmw.locks as locks_module

    real_read_token = locks_module._read_lock_token
    state = {"b_has_raced": False}

    def racing_read_token(path):
        # This is called exactly once by A, right after A wrote its own
        # token, to verify it still owns the lock. Inject B's full
        # concurrent takeover at this exact point, before A's read.
        if not state["b_has_raced"]:
            state["b_has_raced"] = True
            path.unlink(missing_ok=True)
            fd_b = locks_module._create_lock_file(path)
            with os_module.fdopen(fd_b, "w", encoding="utf-8", newline="\n") as f:
                f.write("B-token")
        return real_read_token(path)

    monkeypatch.setattr(locks_module, "_read_lock_token", racing_read_token)

    with pytest.raises(LockedError):
        with acquire_lock(paths, "index"):
            pytest.fail("A must not believe it holds the lock after losing the race")

    # B's lock must survive — A's loss must not delete the winner's lock.
    assert lock_path.read_text(encoding="utf-8") == "B-token"
