from pathlib import Path

import pytest
import yaml

from llmw.archive import PageNotFoundForArchiveError, archive_page
from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.safety import PathNotAllowedError, ReasonRequiredError
from llmw.writer import write_page


def test_archive_requires_reason(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "body\n", reason="seed")
    with pytest.raises(ReasonRequiredError):
        archive_page(paths, "wiki/concepts/a.md", reason="")


def test_archive_missing_file_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(PageNotFoundForArchiveError):
        archive_page(paths, "wiki/concepts/nope.md", reason="cleanup")


def test_archive_moves_file_and_stamps_frontmatter(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(
        paths,
        "wiki/concepts/old.md",
        "---\ntitle: Old\ntype: concept\n---\nbody\n",
        reason="seed",
    )

    dest = archive_page(paths, "wiki/concepts/old.md", reason="merged into New Page")

    assert dest.is_file()
    assert paths.rel(dest).startswith("wiki/archived/")
    fm = yaml.safe_load(dest.read_text(encoding="utf-8").split("---")[1])
    assert fm["archived"] is True
    assert fm["archive_reason"] == "merged into New Page"
    assert fm["status"] == "archived"


def test_archive_leaves_tombstone_by_default(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/old.md", "---\ntitle: Old\n---\nbody\n", reason="seed")

    archive_page(paths, "wiki/concepts/old.md", reason="cleanup")

    original_path = paths.root / "wiki/concepts/old.md"
    assert original_path.is_file()
    assert "archived" in original_path.read_text(encoding="utf-8")


def test_archive_without_tombstone_removes_original(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/old.md", "---\ntitle: Old\n---\nbody\n", reason="seed")

    archive_page(paths, "wiki/concepts/old.md", reason="cleanup", tombstone=False)

    assert not (paths.root / "wiki/concepts/old.md").is_file()


def test_archive_twice_raises_already_archived(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/old.md", "---\ntitle: Old\n---\nbody\n", reason="seed")
    dest = archive_page(paths, "wiki/concepts/old.md", reason="cleanup")

    with pytest.raises(PathNotAllowedError):
        archive_page(paths, paths.rel(dest), reason="again")


def test_archive_updates_log_and_index(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/old.md", "---\ntitle: Old\n---\nbody\n", reason="seed")
    rebuild(paths)

    archive_page(paths, "wiki/concepts/old.md", reason="superseded by Overview")

    log_text = paths.wiki_log.read_text(encoding="utf-8")
    assert "superseded by Overview" in log_text

    import sqlite3

    conn = sqlite3.connect(paths.index_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM pages WHERE path LIKE 'wiki/archived/%'"
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()
