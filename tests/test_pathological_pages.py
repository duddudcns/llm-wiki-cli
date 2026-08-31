"""Every operation, over every page shape that has ever gone wrong.

The per-behaviour tests each check one thing on a well-formed page. What
they cannot say is "no operation corrupts, crashes, or silently drops a
page, whatever the page looks like" — and every defect that survived
review in this area came from a page shape nobody wrote a case for: a
frontmatter block that doesn't parse, an unquoted date that is really an
integer, a fence line inside the part that doesn't parse.

So this is a matrix, not a list of scenarios: each pathological page runs
through index → search → read → lint → the Stop hook → supersede →
archive, and the assertions are the invariants that must hold for all of
them at once.

A page here is *deliberately* not something llmw would write. `write_page`
validates, so these arrive by hand-editing, a bad merge, a half-finished
save, or a wiki adopted with `--adopt` from somewhere else — which is
exactly the population that has no other safety net.
"""

from __future__ import annotations

import sqlite3
import datetime
from pathlib import Path

import pytest

from llmw.archive import archive_page
from llmw.bootstrap import init_project
from llmw.frontmatter import InvalidFrontmatterError, split_frontmatter
from llmw.hook import evaluate_pretooluse, evaluate_stop
from llmw.indexer import rebuild
from llmw.lint import run_lint
from llmw.read import PageNotFoundError, read_page
from llmw.search import search
from llmw.writer import write_page

# Every shape that has bitten, plus the neighbours of each.
PATHOLOGICAL: dict[str, str] = {
    "empty": "",
    "whitespace_only": "   \n\n\t\n",
    "body_only": "# Just a heading\n\nNo frontmatter at all.\n",
    "frontmatter_only": "---\ntitle: T\ntype: note\n---\n",
    "unterminated_quote": '---\ntitle: "unterminated\ntype: note\n---\n\n# B\n\nBody.\n',
    "fence_inside_broken_frontmatter": (
        '---\ntitle: "unterminated\n```\n# Phantom\n[[Ghost]]\n---\n\n# Real\n\nBody.\n'
    ),
    "tilde_fence_inside_broken": (
        '---\ntitle: "unterminated\n~~~\n---\n\n# Real\n\nBody.\n'
    ),
    "frontmatter_is_a_list": "---\n- one\n- two\n---\n\n# B\n\nBody.\n",
    "frontmatter_is_a_scalar": "---\njust a string\n---\n\n# B\n\nBody.\n",
    "empty_frontmatter_block": "---\n---\n\n# B\n\nBody.\n",
    "triple_dash_in_body": "---\ntitle: T\ntype: note\n---\n\n# B\n\n---\n\nMore.\n",
    "crlf": "---\r\ntitle: T\r\ntype: note\r\n---\r\n\r\n# B\r\n\r\nBody.\r\n",
    "bom": "﻿---\ntitle: T\ntype: note\n---\n\n# B\n\nBody.\n",
    "compact_date": "---\ntitle: T\ntype: note\nupdated: 20260101\n---\n\n# B\n\nBody.\n",
    "datetime_date": (
        "---\ntitle: T\ntype: note\nupdated: 2026-01-01 09:30:00\n---\n\n# B\n\nBody.\n"
    ),
    "future_date": "---\ntitle: T\ntype: note\nupdated: 2099-01-01\n---\n\n# B\n\nBody.\n",
    "date_is_a_word": "---\ntitle: T\ntype: note\nupdated: soon\n---\n\n# B\n\nBody.\n",
    "date_is_a_list": "---\ntitle: T\ntype: note\nupdated:\n  - a\n---\n\n# B\n\nBody.\n",
    "code_is_a_string": (
        "---\ntitle: T\ntype: note\ncode: src/one.py\n---\n\n# B\n\nBody.\n"
    ),
    "code_is_nested": (
        "---\ntitle: T\ntype: note\ncode:\n  nested:\n    - src/one.py\n---\n\n# B\n\nB.\n"
    ),
    "code_points_nowhere": (
        "---\ntitle: T\ntype: note\ncode:\n  - ../../etc/passwd\n---\n\n# B\n\nBody.\n"
    ),
    "superseded_by_itself": (
        "---\ntitle: T\ntype: note\nsuperseded_by: wiki/decisions/superseded_by_itself.md\n"
        "---\n\n# B\n\nBody.\n"
    ),
    "unicode_and_emoji": (
        "---\ntitle: 스탯창 정리 🎯\ntype: note\n---\n\n# 제목\n\n본문 [[다른 문서]].\n"
    ),
    "very_long_line": "---\ntitle: T\ntype: note\n---\n\n# B\n\n" + ("x" * 20000) + "\n",
    "many_backticks": "---\ntitle: T\ntype: note\n---\n\n# B\n\n" + ("`" * 200) + "\n",
    "unclosed_fence": "---\ntitle: T\ntype: note\n---\n\n# B\n\n```python\nprint(1)\n",
    "null_ish_values": (
        "---\ntitle: T\ntype: ~\nstatus: null\nupdated:\n---\n\n# B\n\nBody.\n"
    ),
}

# Which shapes must reach the index and which must be reported as errors.
# `pages_indexed > 0` would pass while twenty of them silently fell out —
# and "the page is silently absent from the index" is exactly the defect
# this file exists to catch. Pinning the split turns any future "that
# shape quietly stopped indexing" into a named failure.
EXPECTED_ERRORED = {
    "unterminated_quote",
    "fence_inside_broken_frontmatter",
    "tilde_fence_inside_broken",
    "frontmatter_is_a_list",
    "frontmatter_is_a_scalar",
}
EXPECTED_INDEXED = set(PATHOLOGICAL) - EXPECTED_ERRORED

REPLACEMENT = (
    "---\ntitle: Replacement\ntype: decision\nstatus: active\n"
    "created: 2026-08-31\nupdated: 2026-08-31\nsummary: s.\n---\n\n# R\n\nBody.\n"
)


def _seed(tmp_path: Path, name: str, content: str) -> Path:
    page = tmp_path / "wiki" / "decisions" / f"{name}.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(content, encoding="utf-8", newline="")
    return page


@pytest.fixture(scope="module")
def loaded(tmp_path_factory) -> Path:
    """One project holding every pathological page at once — the read-side
    checks are about the whole corpus surviving, not one page at a time."""
    root = tmp_path_factory.mktemp("pathological")
    paths = init_project(root)
    for name, content in PATHOLOGICAL.items():
        _seed(root, name, content)
    rebuild(paths)
    return root


def _paths(root: Path):
    from llmw.paths import ProjectPaths

    return ProjectPaths.for_project_root(root)


def test_indexing_the_whole_corpus_reports_errors_without_aborting(
    loaded: Path,
) -> None:
    # One unreadable page must not stop the rest from being indexed; a
    # rebuild that aborts leaves the wiki invisible until someone repairs
    # a file they have not been told about.
    paths = _paths(loaded)
    stats = rebuild(paths)

    assert stats.files_scanned >= len(PATHOLOGICAL)
    # Anything that failed says which file and why, rather than vanishing.
    for path, message in stats.errors:
        assert path and message

    conn = sqlite3.connect(paths.index_db)
    try:
        indexed = {
            Path(row[0]).stem
            for row in conn.execute("SELECT path FROM pages")
        }
    finally:
        conn.close()
    assert EXPECTED_INDEXED <= indexed, EXPECTED_INDEXED - indexed
    assert not (EXPECTED_ERRORED & indexed), EXPECTED_ERRORED & indexed


def test_search_answers_over_the_whole_corpus(loaded: Path) -> None:
    response = search(_paths(loaded), "body", limit=50)

    # Named pages, not just "some results": asserting the list is
    # non-empty passes while any particular shape has quietly stopped
    # being findable. These three all literally contain "Body." and their
    # frontmatter parses, so each must come back.
    found = {Path(r.path).stem for r in response.results}
    assert {"crlf", "bom", "compact_date"} <= found, found
    # And one that must not: its body is Korean and mentions no such word.
    assert "unicode_and_emoji" not in found
    for result in response.results:
        # Rendering must not depend on any field being present.
        assert result.path
        assert isinstance(result.title, str)


def test_reading_every_page_either_answers_or_says_not_found(
    loaded: Path,
) -> None:
    paths = _paths(loaded)
    for name in PATHOLOGICAL:
        rel = f"wiki/decisions/{name}.md"
        try:
            result = read_page(paths, rel)
        except PageNotFoundError:
            continue  # an honest answer
        assert result.path == rel


def test_freshness_renders_for_every_page_without_raising(loaded: Path) -> None:
    # `describe` runs on hand-written frontmatter, so every shape above
    # reaches it: an integer date, a list, a word, a null, a missing key.
    from llmw.freshness import describe

    conn = sqlite3.connect((loaded / ".llmw" / "index.sqlite"))
    conn.row_factory = sqlite3.Row
    try:
        rows = list(conn.execute("SELECT updated_at, body_changed_at FROM pages"))
    finally:
        conn.close()

    for row in rows:
        line = describe(row["updated_at"], row["body_changed_at"])
        assert line is None or isinstance(line, str)

    # Not a tautology: at least one shape has to actually render, or the
    # loop above is satisfied by a `describe` that answers None to
    # everything — which is what a dead feature looks like.
    rendered = [
        describe(row["updated_at"], row["body_changed_at"]) for row in rows
    ]
    assert any(line for line in rendered), "no page rendered a freshness line"
    assert describe("2026-01-01", None, today=datetime.date(2026, 8, 31)) == (
        "2026-01-01 (242d ago)"
    )


def test_lint_reports_rather_than_raises(loaded: Path) -> None:
    report = run_lint(_paths(loaded))

    # The corpus is deliberately broken, so lint must find things — and
    # must survive finding them.
    assert not report.is_clean()
    flagged = {Path(entry["path"]).stem for entry in report.invalid_frontmatter}
    assert EXPECTED_ERRORED <= flagged, EXPECTED_ERRORED - flagged


def test_the_stop_hook_answers_over_a_broken_corpus(loaded: Path) -> None:
    paths = _paths(loaded)
    (loaded / "src").mkdir(exist_ok=True)
    source = loaded / "src" / "one.py"
    source.write_text("a\n", encoding="utf-8")

    evaluate_pretooluse(
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(source),
                "old_string": "a",
                "new_string": "b",
            },
            "session_id": "pathological",
            "cwd": str(paths.project_root),
        }
    )
    result = evaluate_stop(
        {"session_id": "pathological", "cwd": str(paths.project_root)}
    )

    assert result is not None
    assert "record durable knowledge" in result["reason"]
    # The named-pages half, over a corpus where five shapes fail to
    # index: `code_is_a_string` declares `code: src/one.py` as a scalar
    # rather than a list, which the reader must still normalize.
    assert "code_is_a_string.md" in result["reason"], result["reason"]


@pytest.mark.parametrize("name", sorted(PATHOLOGICAL))
def test_superseding_any_page_leaves_it_parseable_and_marked(
    name: str, tmp_path: Path
) -> None:
    # The invariant a lifecycle write owes every page shape: afterwards
    # the page parses, the mark is there *as data*, and the original text
    # is still somewhere in the file.
    paths = init_project(tmp_path)
    old = _seed(tmp_path, name, PATHOLOGICAL[name])
    before = old.read_text(encoding="utf-8")

    write_page(
        paths,
        "wiki/decisions/replacement.md",
        REPLACEMENT,
        reason="replace it",
        supersedes=f"wiki/decisions/{name}.md",
    )

    after = old.read_text(encoding="utf-8")
    data, _ = split_frontmatter(after)  # must not raise
    assert data.get("status") == "superseded"
    assert data.get("superseded_by") == "wiki/decisions/replacement.md"
    assert before != after, f"{name}: the flip wrote nothing"


@pytest.mark.parametrize("name", sorted(PATHOLOGICAL))
def test_archiving_any_page_leaves_it_parseable_and_marked(
    name: str, tmp_path: Path
) -> None:
    paths = init_project(tmp_path)
    _seed(tmp_path, name, PATHOLOGICAL[name])

    dest = archive_page(paths, f"wiki/decisions/{name}.md", reason="retire it")

    data, _ = split_frontmatter(dest.read_text(encoding="utf-8"))  # must not raise
    assert data.get("status") == "archived"
    assert data.get("archived") is True


@pytest.mark.parametrize("name", sorted(PATHOLOGICAL))
def test_no_page_shape_makes_a_lifecycle_write_lose_the_body(
    name: str, tmp_path: Path
) -> None:
    # Separate from the parse check above: a fix that made pages parse by
    # discarding what it could not read would satisfy that one.
    paths = init_project(tmp_path)
    page = _seed(tmp_path, name, PATHOLOGICAL[name])
    original = page.read_text(encoding="utf-8")

    write_page(
        paths, "wiki/decisions/replacement.md", REPLACEMENT,
        reason="replace it", supersedes=f"wiki/decisions/{name}.md",
    )

    after = page.read_text(encoding="utf-8")
    for word in ("Body.", "Phantom", "unterminated", "제목", "just a string"):
        if word in original:
            assert word in after, f"{name}: lost {word!r}"


def test_a_broken_page_never_leaks_a_link_or_heading_into_the_parse(
    tmp_path: Path,
) -> None:
    # The salvage wrapper must contain whatever it demotes. Checked for
    # every shape whose unreadable half carries markdown.
    from llmw.parser import parse_page

    paths = init_project(tmp_path)
    for name in ("fence_inside_broken_frontmatter", "tilde_fence_inside_broken"):
        page = _seed(tmp_path, name, PATHOLOGICAL[name])
        write_page(
            paths, f"wiki/decisions/new-{name}.md", REPLACEMENT,
            reason="r", supersedes=f"wiki/decisions/{name}.md",
        )
        parsed = parse_page(page.read_text(encoding="utf-8"), "wiki/x.md")
        assert "Phantom" not in [h.text for h in parsed.headings], name
        assert "Ghost" not in [link.target_raw for link in parsed.links], name


def test_a_code_ref_escaping_the_project_is_never_matched(tmp_path: Path) -> None:
    # `code: ../../etc/passwd` is indexed as written, but `_touched_rel`
    # only ever produces paths *inside* the project, so nothing can match
    # it. Pinned because the natural "fix" — resolving code refs against
    # the filesystem — would turn a wiki page into a path oracle.
    paths = init_project(tmp_path)
    _seed(tmp_path, "escaper", PATHOLOGICAL["code_points_nowhere"])
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    try:
        refs = [r[0] for r in conn.execute("SELECT file_path FROM page_files")]
    finally:
        conn.close()

    assert refs == ["../../etc/passwd"]
    assert not any(Path(ref).is_absolute() for ref in refs)


def test_a_backdated_page_actually_renders_a_divergence_note(tmp_path: Path) -> None:
    """The read-side divergence surface, in its *firing* state.

    Every corpus test here creates its scaffolding today, and
    `body_changed_at` starts None on a page seen for the first time, so
    divergence cannot render in any of them — the whole surface was
    exercised only while silent. That is exactly how `wiki/log.md` came
    to carry a permanent note nobody's test could see.
    """
    paths = init_project(tmp_path)
    page = tmp_path / "wiki" / "decisions" / "old.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "---\ntitle: Old\ntype: decision\nstatus: active\ncreated: 2026-01-01\n"
        "updated: 2026-01-01\nsummary: s.\n---\n\n# Old\n\nThe uploader owns it.\n",
        encoding="utf-8",
    )
    rebuild(paths)

    from llmw.writer import edit_page

    edit_page(
        paths, "wiki/decisions/old.md",
        "The uploader owns it.", "The client owns it again.",
        reason="reverse it",
    )

    from llmw.freshness import describe

    conn = sqlite3.connect(paths.index_db)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT updated_at, body_changed_at FROM pages WHERE path = ?",
            ("wiki/decisions/old.md",),
        ).fetchone()
    finally:
        conn.close()

    today = datetime.date.today().isoformat()
    assert describe(row["updated_at"], row["body_changed_at"]) == (
        f"2026-01-01 ({(datetime.date.today() - datetime.date(2026, 1, 1)).days}d ago, "
        f"body changed {today})"
    )


def test_the_activity_log_never_diverges_from_itself(tmp_path: Path) -> None:
    """`append_log` writes this page's body on every mutation.

    Its `updated` was written once by `init` and — by the write-side rule
    — must never be bumped for an ordinary edit, so the read side showed
    a permanent "body changed" note the agent could not act on: bumping it
    by hand re-diverges on the next append. For a running log an append
    *is* the restatement, so the append does the bump.
    """
    from llmw.freshness import describe
    from llmw.writer import write_page

    paths = init_project(tmp_path)
    log = paths.wiki_log
    log.write_text(
        log.read_text(encoding="utf-8").replace(
            f"updated: {datetime.date.today().isoformat()}", "updated: 2026-01-01"
        ),
        encoding="utf-8",
    )
    rebuild(paths)

    write_page(
        paths, "wiki/decisions/anything.md", REPLACEMENT, reason="one ordinary write"
    )
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT updated_at, body_changed_at FROM pages WHERE path LIKE '%log.md'"
        ).fetchone()
    finally:
        conn.close()

    line = describe(row["updated_at"], row["body_changed_at"])
    assert line is None or "body changed" not in line, line


@pytest.mark.parametrize(
    ("first", "second"),
    [("supersede", "archive"), ("archive", "supersede")],
)
def test_one_lifecycle_operation_after_another_leaves_a_parseable_page(
    first: str, second: str, tmp_path: Path
) -> None:
    # Single shape x single operation is covered above; operation *after*
    # operation is not, and each one rewrites the same frontmatter keys
    # the other set.
    from llmw.archive import archive_page
    from llmw.writer import write_page

    paths = init_project(tmp_path)
    _seed(tmp_path, "target", PATHOLOGICAL["unterminated_quote"])
    rel = "wiki/decisions/target.md"

    def supersede(path: str) -> str:
        write_page(
            paths, f"wiki/decisions/new-{first}{second}.md", REPLACEMENT,
            reason="replace", supersedes=path,
        )
        return path

    def archive(path: str) -> str:
        return paths.rel(archive_page(paths, path, reason="retire"))

    current = rel
    for step in (first, second):
        current = {"supersede": supersede, "archive": archive}[step](current)

    data, _ = split_frontmatter(
        (paths.root / current).read_text(encoding="utf-8")
    )  # must not raise
    assert data.get("status") in {"superseded", "archived"}
