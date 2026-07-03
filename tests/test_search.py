from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.search import IndexNotBuiltError, build_match_query, search


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

    response = search(paths, "context overhead")
    assert response.mode == "strict"
    assert any(r.path == "wiki/concepts/context.md" for r in response.results)
    top = next(r for r in response.results if r.path == "wiki/concepts/context.md")
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

    response = search(paths, "shared keyword", limit=3)
    assert len(response.results) == 3


def test_search_type_filter(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\ntype: concept\n---\nfindme term\n")
    _write(tmp_path, "wiki/decisions/b.md", "---\ntitle: B\ntype: decision\n---\nfindme term\n")
    rebuild(paths)

    response = search(paths, "findme", type_filter="decision")
    paths_found = [r.path for r in response.results]
    assert paths_found == ["wiki/decisions/b.md"]


def test_search_no_tokens_returns_empty(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    response = search(paths, "???")
    assert response.results == []
    assert response.mode == "strict"


def test_build_match_query_extracts_non_ascii_tokens():
    assert build_match_query("미니맵") == "미니맵*"
    assert build_match_query("미니맵 레이아웃 에디터") == "미니맵* 레이아웃* 에디터*"


def test_search_finds_korean_query(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/components/미니맵 레이아웃 에디터.md",
        "---\ntitle: 미니맵 레이아웃 에디터\n---\n"
        "스탯창 미니맵 위젯의 좌표와 크기를 조정하는 에디터 도구.\n",
    )
    rebuild(paths)

    response = search(paths, "미니맵")
    assert any(r.path == "wiki/components/미니맵 레이아웃 에디터.md" for r in response.results)

    response_multi = search(paths, "미니맵 레이아웃 에디터")
    assert any(
        r.path == "wiki/components/미니맵 레이아웃 에디터.md" for r in response_multi.results
    )


def test_build_match_query_replaces_korean_particles():
    assert build_match_query("스탯창을") == "스탯창*"
    assert build_match_query("포탈에서") == "포탈*"


def test_search_particle_query_ranks_bare_word_page_first(tmp_path: Path):
    # The target page's *title* is the bare noun; a distractor page merely
    # *mentions* the inflected form in its body. Without stem replacement +
    # title-weighted bm25, the distractor used to win on literal-string luck.
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/stat-window.md",
        "---\ntitle: 스탯창\n---\n스탯창 레이아웃과 배치를 설명한다.\n",
    )
    _write(
        tmp_path,
        "wiki/concepts/distractor.md",
        "---\ntitle: Distractor\n---\n"
        "스탯창을 조정하는 방법. 스탯창을 다시 조정한다. 스탯창을 또 조정한다.\n",
    )
    rebuild(paths)

    response = search(paths, "스탯창을")
    assert response.mode == "strict"
    assert response.results
    assert response.results[0].path == "wiki/concepts/stat-window.md"


def test_search_full_sentence_relaxes_to_content_words(tmp_path: Path):
    # "눌러" (press, irregular conjugation of 누르다) shares no prefix with
    # the document's "누르면" form, and "이동하" (stemmed from "이동하는")
    # shares no prefix with the document's "이동이" form — real Korean verb
    # conjugation llmw deliberately doesn't stem. Both terms are
    # unmatchable anywhere in the corpus, so strict AND must fail and the
    # relaxed tier must drop exactly those two to find the page via the
    # remaining terms, all of which co-occur in it (note "맵을" -> "맵"
    # also needs stemming: the doc's bare "맵" is *shorter* than the
    # unstemmed query term and could never prefix-match it).
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/portal-gate.md",
        "---\ntitle: PortalGate\n---\n"
        "포탈 위에서 위 화살표키를 누르면 맵 이동이 가능한 원본 방식이다.\n",
    )
    _write(
        tmp_path,
        "wiki/concepts/unrelated.md",
        "---\ntitle: Unrelated\n---\n이것은 전혀 관련 없는 내용이다.\n",
    )
    rebuild(paths)

    sentence = "포탈 위에서 위 화살표키를 눌러 맵을 이동하는 원본 방식"
    strict_response = search(paths, sentence, strict=True)
    assert strict_response.results == []

    response = search(paths, sentence)
    assert response.mode == "relaxed"
    assert set(response.dropped_tokens) == {"눌러", "이동하"}
    assert any(r.path == "wiki/concepts/portal-gate.md" for r in response.results)


def test_search_or_fallback_when_terms_only_partially_overlap(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/alpha.md", "---\ntitle: Alpha\n---\nfoo keyword only\n")
    _write(tmp_path, "wiki/concepts/beta.md", "---\ntitle: Beta\n---\nbar keyword only\n")
    rebuild(paths)

    # No page contains both "foo" and "bar", but each individually matches
    # a page, so the relaxed tier (which never drops a nonzero-df term) is a
    # no-op and the query must fall all the way to the OR tier.
    response = search(paths, "foo bar")
    assert response.mode == "any"
    found = {r.path for r in response.results}
    assert found == {"wiki/concepts/alpha.md", "wiki/concepts/beta.md"}


def test_search_strict_flag_disables_all_fallback(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/alpha.md", "---\ntitle: Alpha\n---\nfoo keyword only\n")
    rebuild(paths)

    assert search(paths, "foo bar", strict=True).results == []


def test_search_token_cap_does_not_error(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    long_query = " ".join(f"word{i}" for i in range(20))
    response = search(paths, long_query)
    assert response.results == []
