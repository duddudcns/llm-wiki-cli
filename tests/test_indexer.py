import sqlite3
import time
from pathlib import Path

from llmw.bootstrap import init_project
from llmw.indexer import index_changed, rebuild


def _write(paths_root: Path, rel: str, content: str) -> Path:
    p = paths_root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_rebuild_indexes_all_pages_and_resolves_links(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/a.md",
        "---\ntitle: A\n---\n# A\n\nSee [[B]] and [[Missing]].\n",
    )
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\n---\n# B\n\nbody\n")

    stats = rebuild(paths)
    assert stats.pages_indexed >= 5  # index.md, overview.md, log.md, a.md, b.md
    assert stats.errors == []

    conn = sqlite3.connect(paths.index_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        assert count == stats.pages_indexed

        rows = conn.execute(
            "SELECT target_raw, target_page_id, exists_flag FROM links "
            "WHERE source_page_id = (SELECT id FROM pages WHERE path = 'wiki/concepts/a.md')"
        ).fetchall()
        by_target = {r[0]: (r[1], r[2]) for r in rows}
        assert by_target["B"][1] == 1
        assert by_target["Missing"][1] == 0
    finally:
        conn.close()


def test_index_changed_skips_unmodified_files(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nbody\n")
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    before_id = conn.execute(
        "SELECT id FROM pages WHERE path = 'wiki/concepts/a.md'"
    ).fetchone()[0]
    conn.close()

    stats = index_changed(paths)
    assert stats.pages_indexed == 0

    conn = sqlite3.connect(paths.index_db)
    after_id = conn.execute(
        "SELECT id FROM pages WHERE path = 'wiki/concepts/a.md'"
    ).fetchone()[0]
    conn.close()
    assert before_id == after_id


def test_index_changed_reindexes_modified_file(tmp_path: Path):
    paths = init_project(tmp_path)
    fs_path = _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nold body\n")
    rebuild(paths)

    time.sleep(0.05)
    fs_path.write_text("---\ntitle: A\n---\nnew body\n", encoding="utf-8")

    stats = index_changed(paths)
    assert stats.pages_indexed == 1

    conn = sqlite3.connect(paths.index_db)
    body = conn.execute(
        "SELECT body FROM pages WHERE path = 'wiki/concepts/a.md'"
    ).fetchone()[0]
    conn.close()
    assert "new body" in body


def test_index_changed_removes_deleted_file(tmp_path: Path):
    paths = init_project(tmp_path)
    fs_path = _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nbody\n")
    rebuild(paths)

    fs_path.unlink()
    stats = index_changed(paths)
    assert stats.pages_removed == 1

    conn = sqlite3.connect(paths.index_db)
    count = conn.execute(
        "SELECT COUNT(*) FROM pages WHERE path = 'wiki/concepts/a.md'"
    ).fetchone()[0]
    conn.close()
    assert count == 0


def test_mdlink_resolves_relative_to_source_directory(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "[link](other.md)\n")
    _write(tmp_path, "wiki/concepts/other.md", "---\ntitle: Other\n---\nbody\n")

    rebuild(paths)
    conn = sqlite3.connect(paths.index_db)
    try:
        row = conn.execute(
            "SELECT exists_flag FROM links WHERE target_raw = 'other.md'"
        ).fetchone()
        assert row[0] == 1
    finally:
        conn.close()


def test_fts_search_query_works(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/context.md",
        "---\ntitle: Context Window Overhead\n---\nMCP tool schemas add context overhead.\n",
    )
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    try:
        rows = conn.execute(
            "SELECT path FROM pages_fts WHERE pages_fts MATCH 'overhead'"
        ).fetchall()
        assert any(r[0] == "wiki/concepts/context.md" for r in rows)
    finally:
        conn.close()
