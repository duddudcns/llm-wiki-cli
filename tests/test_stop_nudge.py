"""The turn-end nudge names the pages that describe what you changed.

`_UPDATE_GATE_MESSAGE` said "record durable knowledge" and stopped there,
which puts the whole burden of remembering *which* page went stale on the
agent — the same burden that produced the staleness problem. The
information needed to answer it exists at exactly that moment: PreToolUse
saw every file edited this turn, and pages can declare which source files
they describe.

Why a declared `code:` list rather than searching page bodies for the
file name: measured on this repo's own wiki, "hook" appears in 20 of 30
pages and every FTS result scores a flat 0.0 — IDF collapses on a small
corpus that is topically about its own search terms, so "top-3 by
relevance" is arbitrary ordering. A page saying which files it describes
is the only precise answer.

`code:` values are source paths, not wiki pages, so they deliberately do
not go through the link machinery: they would resolve as broken links and
inflate `lint`'s broken_links and orphan_pages for every page declaring
one.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from llmw.bootstrap import init_project
from llmw.hook import evaluate_pretooluse, evaluate_stop
from llmw.hook_state import read_session_state
from llmw.indexer import rebuild
from llmw.lint import run_lint

SESSION = "stop-nudge-test"


def _page(root: Path, name: str, code: list[str]) -> Path:
    page = root / "wiki" / "decisions" / f"{name}.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    listed = "".join(f"  - {c}\n" for c in code)
    page.write_text(
        f"---\ntitle: {name}\ntype: decision\nstatus: active\n"
        f"created: 2026-06-01\nupdated: 2026-06-01\n"
        f"summary: How {name} works.\ncode:\n{listed}---\n\n# {name}\n\nBody.\n",
        encoding="utf-8",
    )
    return page


def _edit(paths, file_path: Path) -> None:
    evaluate_pretooluse(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(file_path),
                "old_string": "a",
                "new_string": "b",
            },
            "session_id": SESSION,
            "cwd": str(paths.project_root),
        }
    )


def _stop(paths) -> dict | None:
    return evaluate_stop({"session_id": SESSION, "cwd": str(paths.project_root)})


def _project(tmp_path: Path, pages: dict[str, list[str]]):
    paths = init_project(tmp_path)
    for name, code in pages.items():
        _page(tmp_path, name, code)
    (tmp_path / "src").mkdir(exist_ok=True)
    for source in {c for refs in pages.values() for c in refs}:
        target = tmp_path / source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("a\n", encoding="utf-8")
    rebuild(paths)
    return paths


def test_a_declared_code_ref_does_not_become_a_link(tmp_path: Path) -> None:
    # The reason `code:` is not in LINK_FIELDS: a source path is not a
    # wiki page, so routing it through link resolution would report every
    # page that declares one as having a broken link.
    paths = _project(tmp_path, {"retry": ["src/uploader.py"]})

    report = run_lint(paths)

    assert report.broken_links == []
    # Checked against the links table itself: "no broken links" would also
    # hold if `code:` produced links that happened to resolve. Orphan
    # status is not the assertion — a standalone test page is an orphan
    # whether or not it declares source files.
    conn = sqlite3.connect(paths.index_db)
    try:
        targets = [r[0] for r in conn.execute("SELECT target_raw FROM links")]
        mapped = [r[0] for r in conn.execute("SELECT file_path FROM page_files")]
    finally:
        conn.close()
    assert "src/uploader.py" not in targets
    assert mapped == ["src/uploader.py"]


def test_the_nudge_names_a_page_that_declares_the_changed_file(
    tmp_path: Path,
) -> None:
    paths = _project(
        tmp_path,
        {"retry": ["src/uploader.py"], "unrelated": ["src/parser.py"]},
    )

    _edit(paths, tmp_path / "src" / "uploader.py")
    result = _stop(paths)

    assert result is not None
    assert "wiki/decisions/retry.md" in result["reason"]
    assert "unrelated" not in result["reason"]


def test_the_nudge_still_fires_when_nothing_declares_the_file(
    tmp_path: Path,
) -> None:
    # Nobody has adopted `code:` yet on most wikis, so the plain reminder
    # has to survive an empty mapping rather than the nudge going silent.
    paths = _project(tmp_path, {"retry": ["src/uploader.py"]})

    _edit(paths, tmp_path / "src" / "something-else.py")
    result = _stop(paths)

    assert result is not None
    assert "record durable knowledge" in result["reason"]
    assert "retry.md" not in result["reason"]


def test_touched_files_accumulate_across_a_turn(tmp_path: Path) -> None:
    paths = _project(
        tmp_path,
        {"retry": ["src/uploader.py"], "parsing": ["src/parser.py"]},
    )

    _edit(paths, tmp_path / "src" / "uploader.py")
    _edit(paths, tmp_path / "src" / "parser.py")
    result = _stop(paths)

    assert result is not None
    assert "retry.md" in result["reason"]
    assert "parsing.md" in result["reason"]


def test_touched_is_cleared_with_dirty(tmp_path: Path) -> None:
    # `dirty` resets once the reminder fires, so a later turn does not
    # re-block. `touched` must reset with it or the next episode names
    # files that were already reconciled.
    paths = _project(tmp_path, {"retry": ["src/uploader.py"]})

    _edit(paths, tmp_path / "src" / "uploader.py")
    _stop(paths)

    assert read_session_state(paths, SESSION).get("touched") in (None, [])


def test_an_index_without_the_mapping_table_does_not_crash_the_hook(
    tmp_path: Path,
) -> None:
    # `ensure_schema` runs only on write connects; the Stop hook reads
    # through `open_ro`, which never migrates. An index built before this
    # table existed must degrade to the plain reminder, not raise.
    paths = _project(tmp_path, {"retry": ["src/uploader.py"]})
    conn = sqlite3.connect(paths.index_db)
    conn.execute("DROP TABLE page_files")
    conn.commit()
    conn.close()

    _edit(paths, tmp_path / "src" / "uploader.py")
    result = _stop(paths)

    assert result is not None
    assert "record durable knowledge" in result["reason"]


def test_the_most_recently_updated_pages_come_first(tmp_path: Path) -> None:
    # A long-lived file accumulates decisions: `src/llmw/hook.py` is named
    # by nine pages in this repo's own wiki. Ordering by path would name
    # five of nine alphabetically and leave out the one written last,
    # which is the one most likely to need the update.
    paths = init_project(tmp_path)
    for i, updated in enumerate(["2026-01-01", "2026-08-30", "2026-03-01"]):
        page = tmp_path / "wiki" / "decisions" / f"page{i}.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(
            f"---\ntitle: page{i}\ntype: decision\nstatus: active\n"
            f"created: 2026-01-01\nupdated: {updated}\nsummary: s.\n"
            f"code:\n  - src/shared.py\n---\n\n# page{i}\n\nBody.\n",
            encoding="utf-8",
        )
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "shared.py").write_text("a\n", encoding="utf-8")
    rebuild(paths)

    _edit(paths, tmp_path / "src" / "shared.py")
    reason = _stop(paths)["reason"]

    named = [p for p in ("page1.md", "page2.md", "page0.md") if p in reason]
    assert named == ["page1.md", "page2.md", "page0.md"], reason


def test_a_truncated_list_says_how_many_it_left_out(tmp_path: Path) -> None:
    # A cap that hides its own existence reads as "these are all of them",
    # which is worse than the long list it replaced.
    pages = {f"page{i:02d}": ["src/shared.py"] for i in range(9)}
    paths = _project(tmp_path, pages)

    _edit(paths, tmp_path / "src" / "shared.py")
    reason = _stop(paths)["reason"]

    assert reason.count("wiki/decisions/") == 5
    assert "9" in reason, reason


def test_a_wide_refactor_does_not_produce_a_wall_of_text(tmp_path: Path) -> None:
    # A twenty-file session would otherwise enumerate twenty files and
    # every page touching them, which is the reminder-fatigue this hook
    # already documents as the reason its trivial-prompt filter exists.
    pages = {f"page{i}": [f"src/mod{i}.py"] for i in range(20)}
    paths = _project(tmp_path, pages)

    for i in range(20):
        _edit(paths, tmp_path / "src" / f"mod{i}.py")
    result = _stop(paths)

    assert result is not None
    assert len(result["reason"]) < 600, result["reason"]
    assert result["reason"].count("wiki/decisions/") <= 5


def test_rebuild_does_not_leave_stale_mapping_rows(tmp_path: Path) -> None:
    paths = _project(tmp_path, {"retry": ["src/uploader.py"]})
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    try:
        rows = conn.execute("SELECT COUNT(*) FROM page_files").fetchone()[0]
    finally:
        conn.close()
    assert rows == 1
