import sqlite3
from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.ingest import (
    SourceAlreadyIngestedError,
    SourceNotFoundError,
    SourceNotInRawError,
    UnsupportedSourceTypeError,
    ingest_source,
)


def test_ingest_md_creates_source_draft(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    source = paths.raw_inbox / "meeting-notes.md"
    source.write_text("Discussed the auth redesign.\n", encoding="utf-8")

    dest = ingest_source(paths, "raw/inbox/meeting-notes.md")

    assert dest.is_file()
    assert paths.rel(dest) == "wiki/sources/meeting-notes.md"
    content = dest.read_text(encoding="utf-8")
    assert "source_path: raw/inbox/meeting-notes.md" in content
    assert "TODO: The agent should read the source and summarize it." in content
    assert "source_hash:" in content


def test_ingest_txt_supported(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    source = paths.raw_inbox / "notes.txt"
    source.write_text("plain text notes\n", encoding="utf-8")

    dest = ingest_source(paths, "raw/inbox/notes.txt")
    assert dest.is_file()


def test_ingest_missing_file_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    with pytest.raises(SourceNotFoundError):
        ingest_source(paths, "raw/inbox/nope.md")


def test_ingest_outside_raw_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    outside = tmp_path / "wiki" / "index.md"
    with pytest.raises(SourceNotInRawError):
        ingest_source(paths, paths.rel(outside))


def test_ingest_unsupported_extension_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    source = paths.raw_inbox / "deck.pdf"
    source.write_bytes(b"%PDF-1.4 fake")

    with pytest.raises(UnsupportedSourceTypeError):
        ingest_source(paths, "raw/inbox/deck.pdf")


def test_ingest_twice_raises_already_ingested(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    source = paths.raw_inbox / "notes.md"
    source.write_text("content\n", encoding="utf-8")

    ingest_source(paths, "raw/inbox/notes.md")
    with pytest.raises(SourceAlreadyIngestedError):
        ingest_source(paths, "raw/inbox/notes.md")


def test_ingest_updates_index(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    source = paths.raw_inbox / "notes.md"
    source.write_text("content\n", encoding="utf-8")

    ingest_source(paths, "raw/inbox/notes.md")

    conn = sqlite3.connect(paths.index_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM pages WHERE path = 'wiki/sources/notes.md'"
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()
