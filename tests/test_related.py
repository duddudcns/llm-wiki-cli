from pathlib import Path

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.related import related


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_related_direct_link_and_backlink(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[B]].\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\n---\nSee [[A]].\n")
    rebuild(paths)

    results = related(paths, "A", by=("links",))
    b_result = next(r for r in results if r.path == "wiki/concepts/b.md")
    assert "direct-link" in b_result.reasons
    assert "backlink" in b_result.reasons
    assert b_result.score == 9  # 5 (direct-link) + 4 (backlink)


def test_related_shared_tag(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntags:\n  - infra\n---\nbody\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\ntags:\n  - infra\n---\nbody\n")
    rebuild(paths)

    results = related(paths, "A", by=("tags",))
    b_result = next(r for r in results if r.path == "wiki/concepts/b.md")
    assert b_result.score == 3
    assert "shared-tag:infra" in b_result.reasons


def test_related_respects_by_filter(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntags:\n  - infra\n---\nSee [[B]].\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\ntags:\n  - infra\n---\nbody\n")
    rebuild(paths)

    results = related(paths, "A", by=("tags",))
    for r in results:
        assert "direct-link" not in r.reasons


def test_related_title_mention(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/decisions/auth-redesign.md",
        "---\ntitle: Auth Redesign\n---\nSession tokens move out of the middleware.\n",
    )
    _write(
        tmp_path,
        "wiki/sources/meeting-notes.md",
        "---\ntitle: Meeting Notes\n---\nWe discussed the Auth Redesign plan today.\n",
    )
    rebuild(paths)

    results = related(paths, "Auth Redesign", by=("terms",))
    notes_result = next(r for r in results if r.path == "wiki/sources/meeting-notes.md")
    assert "title-mention" in notes_result.reasons


def test_related_term_overlap_with_korean_particle_in_title(tmp_path: Path):
    # The title carries a trailing particle ("을"); without stemming the
    # generated FTS query the AND-of-title-terms match would require the
    # 4-char literal "스탯창을*" as a prefix, which the other page's bare
    # 3-char "스탯창" token can't satisfy — term-overlap would silently
    # never fire. This asserts stemming reaches related() unchanged.
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/decisions/stat-window-adjust.md",
        "---\ntitle: 스탯창을 조정\n---\n스탯창 크기 조정에 대한 결정.\n",
    )
    _write(
        tmp_path,
        "wiki/concepts/other.md",
        "---\ntitle: Other\n---\n스탯창 위치를 조정한다.\n",
    )
    rebuild(paths)

    results = related(paths, "스탯창을 조정", by=("terms",))
    other_result = next(r for r in results if r.path == "wiki/concepts/other.md")
    assert "term-overlap" in other_result.reasons


def test_related_page_title_containing_fts5_keyword_does_not_raise(tmp_path: Path):
    # related() builds an FTS query from the target page's *title* — a
    # title containing a bare FTS5 operator keyword (AND/OR/NOT) used to
    # raise sqlite3.OperationalError before the query terms were quoted.
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/decisions/find-and-fix.md",
        "---\ntitle: Find AND Fix\n---\nA decision page whose title is a boolean phrase.\n",
    )
    rebuild(paths)

    results = related(paths, "Find AND Fix", by=("terms",))
    assert results == []


def test_related_respects_limit(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntags:\n  - infra\n---\nbody\n")
    for i in range(5):
        _write(
            tmp_path,
            f"wiki/concepts/p{i}.md",
            f"---\ntitle: P{i}\ntags:\n  - infra\n---\nbody\n",
        )
    rebuild(paths)

    results = related(paths, "A", by=("tags",), limit=2)
    assert len(results) == 2


def test_related_negative_limit_does_not_return_unbounded_results(tmp_path: Path):
    # Python's results[:limit] with a negative limit drops from the end
    # rather than truncating to a bounded count — same class of bug as
    # search()'s SQL LIMIT -1, fixed the same way (clamp to >= 1).
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntags:\n  - infra\n---\nbody\n")
    for i in range(5):
        _write(
            tmp_path,
            f"wiki/concepts/p{i}.md",
            f"---\ntitle: P{i}\ntags:\n  - infra\n---\nbody\n",
        )
    rebuild(paths)

    results = related(paths, "A", by=("tags",), limit=-1)
    assert len(results) == 1
