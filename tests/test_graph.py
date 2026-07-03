from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.graph import build_graph, render_graph_html, write_graph_html, write_graph_json
from llmw.indexer import rebuild
from llmw.queries import IndexNotBuiltError


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_build_graph_before_rebuild_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(IndexNotBuiltError):
        build_graph(paths)


def test_build_graph_nodes_and_edges(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[B]].\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\n---\nbody\n")
    rebuild(paths)

    graph = build_graph(paths)
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "wiki/concepts/a.md" in node_ids
    assert "wiki/concepts/b.md" in node_ids

    edge = next(e for e in graph["edges"] if e["source"] == "wiki/concepts/a.md")
    assert edge["target"] == "wiki/concepts/b.md"
    assert edge["kind"] == "wikilink"


def test_write_graph_json_creates_file(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    graph = write_graph_json(paths)
    assert paths.graph_json.is_file()
    assert "nodes" in graph and "edges" in graph


def test_write_graph_html_is_self_contained(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    write_graph_html(paths)
    html = paths.graph_html.read_text(encoding="utf-8")
    assert "<html>" in html
    assert "http://" not in html
    assert "https://" not in html


def test_render_graph_html_embeds_node_count():
    html = render_graph_html({"nodes": [{"id": "a"}], "edges": []})
    assert "1 nodes" in html
