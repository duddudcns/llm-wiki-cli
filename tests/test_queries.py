from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.queries import open_ro


def test_open_ro_returns_none_before_index_is_built(tmp_path: Path):
    paths = init_project(tmp_path)
    assert open_ro(paths) is None


def test_open_ro_connection_is_actually_read_only(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    conn = open_ro(paths)
    try:
        with pytest.raises(Exception):
            conn.execute("DELETE FROM pages")
    finally:
        conn.close()


def test_open_ro_returns_none_for_a_corrupt_index_instead_of_raising(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    paths.index_db.write_bytes(b"not a real sqlite file")

    assert open_ro(paths) is None
