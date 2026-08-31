"""Lifecycle writes must not corrupt a page they cannot fully parse.

`set_fields` and `_stamp_archive_frontmatter` both fall back to
`data, body = {}, text` when the YAML inside a frontmatter block does not
parse. That is right about `data` and wrong about `body`: `text` is the
*whole file*, delimiters included, so the old block gets re-emitted below
the new one and the page ends up carrying two. Silent, and on exactly the
pages least able to survive it.

Superseding or archiving a page whose frontmatter someone broke is an
ordinary thing to want to do — arguably it is when you most want to mark
it — so these operations have to split on the delimiters even when they
cannot read what sits between them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.frontmatter import set_fields
from llmw.writer import write_page

BROKEN = (
    "---\n"
    'title: "unterminated\n'
    "type: decision\n"
    "---\n\n# Old decision\n\nThe body still says something true.\n"
)

NEW_PAGE = (
    "---\ntitle: New decision\ntype: decision\nstatus: active\n"
    "created: 2026-08-31\nupdated: 2026-08-31\nsummary: The new answer.\n"
    "---\n\n# New decision\n\nThe new answer.\n"
)


def test_set_fields_does_not_duplicate_an_unparseable_block() -> None:
    result = set_fields(BROKEN, {"status": "superseded"})

    assert result.count("type: decision") == 1, result
    assert result.count("---") == 2, result
    assert "status: superseded" in result
    assert "The body still says something true." in result


def test_set_fields_keeps_the_body_intact_when_it_cannot_parse() -> None:
    result = set_fields(BROKEN, {"status": "superseded"})
    body = result.split("---", 2)[2]

    assert body.strip().startswith("# Old decision")


def test_superseding_a_page_with_broken_frontmatter_does_not_corrupt_it(
    tmp_path: Path,
) -> None:
    paths = init_project(tmp_path)
    old = tmp_path / "wiki" / "decisions" / "old.md"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_text(BROKEN, encoding="utf-8")

    write_page(
        paths,
        "wiki/decisions/new.md",
        NEW_PAGE,
        reason="replace it",
        supersedes="wiki/decisions/old.md",
    )

    text = old.read_text(encoding="utf-8")
    assert text.count("type: decision") == 1, text
    assert "The body still says something true." in text
    assert "superseded_by: wiki/decisions/new.md" in text


def test_archiving_a_page_with_broken_frontmatter_does_not_corrupt_it(
    tmp_path: Path,
) -> None:
    # Same fallback, same bug, in `archive.py` — and archiving a page
    # whose frontmatter someone broke is exactly what you would do.
    from llmw.archive import archive_page

    paths = init_project(tmp_path)
    page = tmp_path / "wiki" / "decisions" / "old.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(BROKEN, encoding="utf-8")

    dest = archive_page(paths, "wiki/decisions/old.md", reason="retire it")

    text = dest.read_text(encoding="utf-8")
    assert text.count("type: decision") == 1, text
    assert "The body still says something true." in text
    assert "archived: true" in text.lower()


def test_superseding_a_page_that_declares_code_keeps_the_list(
    tmp_path: Path,
) -> None:
    # `set_fields` re-dumps the whole mapping whenever a key has to be
    # replaced — `status` here — so a list-valued key has to survive the
    # round trip, and the page has to stay in `page_files` afterwards.
    import sqlite3

    from llmw.indexer import rebuild

    paths = init_project(tmp_path)
    old = tmp_path / "wiki" / "decisions" / "old.md"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_text(
        "---\ntitle: Old\ntype: decision\nstatus: active\ncreated: 2026-06-01\n"
        "updated: 2026-06-01\nsummary: s.\ncode:\n  - src/uploader.py\n"
        "  - src/retry.py\n---\n\n# Old\n\nBody.\n",
        encoding="utf-8",
    )
    rebuild(paths)

    write_page(
        paths, "wiki/decisions/new.md", NEW_PAGE,
        reason="replace it", supersedes="wiki/decisions/old.md",
    )
    rebuild(paths)

    text = old.read_text(encoding="utf-8")
    assert "src/uploader.py" in text
    assert "src/retry.py" in text
    conn = sqlite3.connect(paths.index_db)
    try:
        mapped = {
            r[0]
            for r in conn.execute(
                "SELECT file_path FROM page_files pf JOIN pages p ON p.id = pf.page_id "
                "WHERE p.path = 'wiki/decisions/old.md'"
            )
        }
    finally:
        conn.close()
    assert mapped == {"src/uploader.py", "src/retry.py"}


# `---\n---\n` is deliberately absent: the frontmatter regex requires a
# line between the delimiters, so an empty block is treated as body. That
# preserves the content rather than corrupting it, and reshaping the regex
# to recognize it would ripple through every reader for no real gain.
@pytest.mark.parametrize("text", ["", "no frontmatter at all\n"])
def test_set_fields_survives_degenerate_input(text: str) -> None:
    result = set_fields(text, {"status": "superseded"})

    assert "status: superseded" in result
    assert result.count("---") == 2, result
