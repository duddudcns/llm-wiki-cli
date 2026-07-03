from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.search import IndexNotBuiltError, search


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_search_before_rebuild_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(IndexNotBuiltError):
        search(paths, "anything")


def test_search_finds_matching_page(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/context.md",
        "---\ntitle: Context Window Overhead\ntags:\n  - ai-agent\n---\n"
        "Tool schemas and long instructions increase agent context pressure.\n",
    )
    rebuild(paths)

    results = search(paths, "context overhead")
    assert any(r.path == "wiki/concepts/context.md" for r in results)
    top = next(r for r in results if r.path == "wiki/concepts/context.md")
    assert top.title == "Context Window Overhead"
    assert "ai-agent" in top.tags


def test_search_respects_limit(tmp_path: Path):
    paths = init_project(tmp_path)
    for i in range(10):
        _write(
            tmp_path,
            f"wiki/concepts/page{i}.md",
            f"---\ntitle: Page {i}\n---\nshared keyword lookup term\n",
        )
    rebuild(paths)

    results = search(paths, "shared keyword", limit=3)
    assert len(results) == 3


def test_search_type_filter(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntype: concept\n---\nfindme term\n")
    _write(tmp_path, "wiki/decisions/b.md", "---\ntitle: B\ntype: decision\n---\nfindme term\n")
    rebuild(paths)

    results = search(paths, "findme", type_filter="decision")
    paths_found = [r.path for r in results]
    assert paths_found == ["wiki/decisions/b.md"]


def test_search_no_tokens_returns_empty(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    assert search(paths, "???") == []
