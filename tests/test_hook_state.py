import os
import time
from pathlib import Path

from llmw.bootstrap import init_project
from llmw.hook_state import read_session_state, write_session_state


def test_write_then_read_roundtrip(tmp_path: Path):
    paths = init_project(tmp_path)

    written = write_session_state(paths, "session-1", dirty=True, searched=False)
    assert written == {"dirty": True, "searched": False}
    assert read_session_state(paths, "session-1") == {"dirty": True, "searched": False}


def test_write_merges_into_existing_state(tmp_path: Path):
    paths = init_project(tmp_path)

    write_session_state(paths, "session-1", dirty=True)
    merged = write_session_state(paths, "session-1", searched=True)

    assert merged == {"dirty": True, "searched": True}


def test_read_missing_session_returns_empty_dict(tmp_path: Path):
    paths = init_project(tmp_path)

    assert read_session_state(paths, "never-written") == {}


def test_read_write_ignore_none_session_id(tmp_path: Path):
    paths = init_project(tmp_path)

    assert write_session_state(paths, None, dirty=True) == {}
    assert read_session_state(paths, None) == {}


def test_session_id_path_traversal_is_rejected(tmp_path: Path):
    paths = init_project(tmp_path)
    malicious = "../../outside"

    assert write_session_state(paths, malicious, dirty=True) == {}
    assert read_session_state(paths, malicious) == {}
    assert not (tmp_path / "outside").exists()
    assert not (paths.llmw_dir.parent / "outside").exists()


def test_session_id_with_path_separator_is_rejected(tmp_path: Path):
    paths = init_project(tmp_path)

    assert write_session_state(paths, "a/b", dirty=True) == {}
    assert read_session_state(paths, "a/b") == {}


def test_session_id_with_null_byte_is_rejected(tmp_path: Path):
    paths = init_project(tmp_path)

    assert write_session_state(paths, "a\x00b", dirty=True) == {}


def test_session_state_isolated_between_sessions(tmp_path: Path):
    paths = init_project(tmp_path)

    write_session_state(paths, "session-a", dirty=True)
    write_session_state(paths, "session-b", dirty=False)

    assert read_session_state(paths, "session-a") == {"dirty": True}
    assert read_session_state(paths, "session-b") == {"dirty": False}


def test_stale_session_files_are_pruned_on_write(tmp_path: Path):
    paths = init_project(tmp_path)
    sessions_dir = paths.llmw_dir / "sessions"

    write_session_state(paths, "old-session", dirty=True)
    stale_file = sessions_dir / "old-session.json"
    eight_days_ago = time.time() - 8 * 24 * 60 * 60
    os.utime(stale_file, (eight_days_ago, eight_days_ago))

    write_session_state(paths, "new-session", dirty=True)

    assert not stale_file.exists()
    assert (sessions_dir / "new-session.json").exists()


def test_recent_session_files_survive_prune(tmp_path: Path):
    paths = init_project(tmp_path)
    sessions_dir = paths.llmw_dir / "sessions"

    write_session_state(paths, "recent-session", dirty=True)
    write_session_state(paths, "another-session", dirty=True)

    assert (sessions_dir / "recent-session.json").exists()
