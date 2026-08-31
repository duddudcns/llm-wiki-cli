"""Corpus-level invariants the per-behaviour tests structurally can't give.

The defect that got furthest — a permanent divergence note on 21 of this
project's own 31 pages — lived in the *interaction* between one lifecycle
operation and every other page's read surface. Every individual test
passed while it was live, because each pinned one behaviour and none
looked at the corpus as a whole.

Two pins here, both class-level rather than case-level:

1. no metadata-only operation may change what any page's freshness line
   says — not the page it operated on, and not any other;
2. an index built by an older release must still answer, since `open_ro`
   never migrates and the plugin's skill sends an upgraded agent straight
   into `llmw search`.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

# Deliberately awkward shapes: a compact unquoted date, a datetime, a
# normal date, and one page with no `updated` at all.
PAGES = {
    "compact": "20260101",
    "stamped": "2026-02-05T09:30:00",
    "ordinary": "2026-03-01",
    "undated": None,
}

NEW_PAGE = (
    "---\ntitle: Replacement\ntype: decision\nstatus: active\n"
    "created: 2026-08-31\nupdated: 2026-08-31\nsummary: s.\n---\n\n# R\n\nBody.\n"
)


def run(
    cwd: Path, *args: str, stdin_text: str | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "llmw.cli", *args],
        cwd=cwd,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _corpus(tmp_path: Path) -> None:
    run(tmp_path, "init")
    for name, updated in PAGES.items():
        page = tmp_path / "wiki" / "decisions" / f"{name}.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        dated = f"updated: {updated}\n" if updated else ""
        page.write_text(
            f"---\ntitle: {name}\ntype: decision\nstatus: active\n"
            f"created: 2026-01-01\n{dated}summary: A page about retries.\n"
            f"---\n\n# {name}\n\nThe uploader owns the retry budget.\n",
            encoding="utf-8",
        )
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "uploader.py").write_text("a\n", encoding="utf-8")
    run(tmp_path, "rebuild")


def _freshness_lines(tmp_path: Path) -> dict[str, str | None]:
    """What every page's freshness line would say, keyed by path."""
    payload = json.loads(
        run(tmp_path, "search", "retries", "--limit", "20", "--json").stdout
    )
    from llmw.freshness import describe

    return {
        r["path"]: describe(r["updated"], r["body_changed_at"])
        for r in payload["results"]
    }


def test_no_metadata_only_operation_changes_any_freshness_line(
    tmp_path: Path,
) -> None:
    # The exact failure class: a lifecycle write made a read surface noisy
    # — on the page it touched, and by repetition on most of the wiki.
    # None of these restates a claim, so none may change what any page
    # says about its own freshness.
    _corpus(tmp_path)
    before = _freshness_lines(tmp_path)
    assert before, "the corpus must actually be searchable for this to mean anything"

    run(
        tmp_path, "edit", "wiki/decisions/compact.md", "--old", "type: decision",
        "--new", "type: decision\ncode:\n  - src/uploader.py", "--reason", "declare",
    )
    run(
        tmp_path, "edit", "wiki/decisions/stamped.md", "--old", "type: decision",
        "--new", "type: decision\ntags:\n  - retries", "--reason", "retag",
    )
    run(
        tmp_path, "write", "wiki/decisions/replacement.md", "--reason", "replace",
        "--supersedes", "wiki/decisions/ordinary.md", "--stdin", stdin_text=NEW_PAGE,
    )
    run(tmp_path, "archive", "wiki/decisions/undated.md", "--reason", "retire")
    run(tmp_path, "rebuild")

    after = _freshness_lines(tmp_path)
    for path, line in before.items():
        assert after.get(path, line) == line, (
            f"{path}: freshness line changed from {line!r} to {after.get(path)!r} "
            f"after metadata-only writes"
        )


def test_a_real_body_change_does_move_the_line(tmp_path: Path) -> None:
    # The invariant above is only meaningful if the signal still works;
    # a `describe` that always returned None would satisfy it trivially.
    _corpus(tmp_path)
    before = _freshness_lines(tmp_path)

    run(
        tmp_path, "edit", "wiki/decisions/ordinary.md",
        "--old", "The uploader owns the retry budget.",
        "--new", "The client owns the retry budget again.",
        "--reason", "reverse it",
    )

    after = _freshness_lines(tmp_path)
    assert after["wiki/decisions/ordinary.md"] != before["wiki/decisions/ordinary.md"]
    assert "body changed" in after["wiki/decisions/ordinary.md"]


def _downgrade_index(index_db: Path) -> None:
    """Reshape `pages` into the pre-0.1.31 layout. `ALTER TABLE DROP
    COLUMN` refuses here — SQLite re-parses the stored CREATE statement
    and chokes on the SQL comments in it — so the table is rebuilt."""
    conn = sqlite3.connect(index_db)
    legacy = (
        "id,path,title,type,status,summary,body,hash,mtime,created_at,updated_at"
    )
    conn.executescript(
        f"CREATE TABLE pages_legacy AS SELECT {legacy} FROM pages;"
        "DROP TABLE pages;"
        "ALTER TABLE pages_legacy RENAME TO pages;"
        "DROP TABLE page_files;"
    )
    conn.commit()
    conn.close()


def test_an_index_from_an_older_release_still_answers(tmp_path: Path) -> None:
    # `open_ro` never migrates, and nothing on the read path grafts the
    # columns on: `status` and `health` open the DB raw, so session start
    # does not either. The plugin's skill sends an upgraded agent straight
    # into `llmw search`, so this crashed with a raw OperationalError for
    # every project whose index predated the column.
    _corpus(tmp_path)
    _downgrade_index(tmp_path / ".llmw" / "index.sqlite")

    found = run(tmp_path, "search", "retries")
    read = run(tmp_path, "read", "wiki/decisions/ordinary.md")
    stopped = run(tmp_path, "hook", "stop", stdin_text=json.dumps({"cwd": "."}))

    assert found.returncode == 0, found.stderr
    assert "ordinary" in found.stdout
    assert read.returncode == 0, read.stderr
    assert "2026-03-01" in read.stdout
    assert stopped.returncode == 0, stopped.stderr
    # No history is knowable from a legacy index, so nothing may claim any.
    assert "body changed" not in found.stdout
    assert "body changed" not in read.stdout


def test_a_write_against_a_legacy_index_grafts_the_columns_back(
    tmp_path: Path,
) -> None:
    _corpus(tmp_path)
    _downgrade_index(tmp_path / ".llmw" / "index.sqlite")

    run(
        tmp_path, "edit", "wiki/decisions/ordinary.md", "--old", "type: decision",
        "--new", "type: note", "--reason", "reclassify",
    )

    conn = sqlite3.connect(tmp_path / ".llmw" / "index.sqlite")
    try:
        columns = {r[1] for r in conn.execute("PRAGMA table_info(pages)")}
    finally:
        conn.close()
    assert {"body_hash", "body_changed_at"} <= columns


def test_rebuild_keeps_the_observed_history(tmp_path: Path) -> None:
    # `rebuild` clears `pages` before re-syncing, so every page came back
    # with no history — silently, and toward *trust*. llmw's own error
    # messages advise running it, so following the tool's advice erased
    # the feature's memory, and an unwanted note had `rebuild` as a
    # laundering path.
    _corpus(tmp_path)
    run(
        tmp_path, "edit", "wiki/decisions/ordinary.md",
        "--old", "The uploader owns the retry budget.",
        "--new", "The client owns the retry budget again.",
        "--reason", "reverse it",
    )
    assert "body changed" in _freshness_lines(tmp_path)["wiki/decisions/ordinary.md"]

    run(tmp_path, "rebuild")

    assert "body changed" in _freshness_lines(tmp_path)["wiki/decisions/ordinary.md"]


def test_a_page_restated_today_in_compact_form_gets_no_notice(
    tmp_path: Path,
) -> None:
    # The today-skip compared raw text, so an unquoted `updated: 20260831`
    # — the exact shape the ordering fix was about — never matched and the
    # notice re-fired on a page restated today.
    today = datetime.date.today()
    run(tmp_path, "init")
    page = tmp_path / "wiki" / "decisions" / "compact-today.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        f"---\ntitle: T\ntype: decision\nstatus: active\ncreated: 2026-01-01\n"
        f"updated: {today.strftime('%Y%m%d')}\nsummary: s.\n---\n\n# T\n\nBody line.\n",
        encoding="utf-8",
    )
    run(tmp_path, "rebuild")

    result = run(
        tmp_path, "edit", "wiki/decisions/compact-today.md",
        "--old", "Body line.", "--new", "Different body line.", "--reason", "edit",
    )

    assert result.returncode == 0, result.stderr
    assert "not bumped" not in result.stderr, result.stderr
