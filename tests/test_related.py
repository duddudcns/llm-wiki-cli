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
