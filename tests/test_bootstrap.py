import sqlite3
from pathlib import Path

import pytest

from llmw.bootstrap import ProjectAlreadyExistsError, init_project
from llmw.indexer import rebuild
from llmw.status import build_status


def test_init_creates_expected_structure(tmp_path: Path) -> None:
    paths = init_project(tmp_path)

    assert paths.raw.is_dir()
    assert paths.wiki.is_dir()
    assert paths.llmw_dir.is_dir()
    assert (paths.wiki / "index.md").is_file()
    assert (paths.wiki / "overview.md").is_file()
    assert paths.wiki_log.is_file()
    assert paths.config_path.is_file()
    assert (paths.claude_skill_dir / "SKILL.md").is_file()
    assert (paths.claude_skill_dir / "reference.md").is_file()
    assert (paths.claude_skill_dir / "examples.md").is_file()
    assert (paths.claude_plugin_dir / "plugin.json").is_file()


def test_init_twice_without_force_raises(tmp_path: Path) -> None:
    init_project(tmp_path)
    with pytest.raises(ProjectAlreadyExistsError):
        init_project(tmp_path)


def test_init_twice_with_force_succeeds(tmp_path: Path) -> None:
    init_project(tmp_path)
    init_project(tmp_path, force=True)


def test_status_before_rebuild_reports_no_index(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    report = build_status(paths)

    assert report.index_exists is False
    assert report.wiki_page_count == 3
    assert report.raw_source_count == 0


def test_default_scaffolded_pages_have_no_broken_links(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    try:
        broken = conn.execute(
            "SELECT target_raw FROM links WHERE exists_flag = 0"
        ).fetchall()
    finally:
        conn.close()
    assert broken == []


def test_init_writes_lf_only_even_on_windows(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    for fs_path in paths.wiki.rglob("*.md"):
        raw = fs_path.read_bytes()
        assert b"\r\n" not in raw, f"{fs_path} contains CRLF"
    assert b"\r\n" not in paths.config_path.read_bytes()
    assert b"\r\n" not in (paths.claude_skill_dir / "SKILL.md").read_bytes()
