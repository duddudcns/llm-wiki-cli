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
    stats = rebuild(_paths(loaded))

    assert stats.files_scanned >= len(PATHOLOGICAL)
    assert stats.pages_indexed > 0
    # Anything that failed says which file and why, rather than vanishing.
    for path, message in stats.errors:
        assert path and message


def test_search_answers_over_the_whole_corpus(loaded: Path) -> None:
    response = search(_paths(loaded), "body", limit=50)

    assert response.results
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


def test_lint_reports_rather_than_raises(loaded: Path) -> None:
    report = run_lint(_paths(loaded))

    # The corpus is deliberately broken, so lint must find things — and
    # must survive finding them.
    assert not report.is_clean()
    assert isinstance(report.as_dict(), dict)


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
