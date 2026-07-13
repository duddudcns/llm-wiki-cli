"""`llmw graph` — build and export the wiki's link graph (nodes = pages,
edges = resolved wikilink/embed/mdlink references). No AI calls; pure DB
query + a small self-contained (no external CDN) HTML viewer.
"""

from __future__ import annotations

import json as jsonlib

from llmw.paths import ProjectPaths
from llmw.queries import IndexNotBuiltError, open_ro


def build_graph(paths: ProjectPaths) -> dict:
    conn = open_ro(paths)
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")

    try:
        pages = {
            row["id"]: row
            for row in conn.execute("SELECT id, path, title, type FROM pages")
        }
        tags_by_page: dict[int, list[str]] = {}
        for row in conn.execute("SELECT page_id, tag FROM tags"):
            tags_by_page.setdefault(row["page_id"], []).append(row["tag"])

        degree = {pid: 0 for pid in pages}
        edges = []
        for row in conn.execute(
            "SELECT source_page_id, target_page_id, kind, link_text FROM links "
            "WHERE target_page_id IS NOT NULL"
        ):
            src, tgt = row["source_page_id"], row["target_page_id"]
            if src == tgt or src not in pages or tgt not in pages:
                continue
            edges.append(
                {
                    "source": pages[src]["path"],
                    "target": pages[tgt]["path"],
                    "kind": row["kind"],
                    "text": row["link_text"],
                }
            )
            degree[src] += 1
            degree[tgt] += 1

        nodes = [
            {
                "id": row["path"],
                "title": row["title"],
                "type": row["type"],
                "tags": tags_by_page.get(pid, []),
                "degree": degree.get(pid, 0),
            }
            for pid, row in pages.items()
        ]
        return {"nodes": nodes, "edges": edges}
    finally:
        conn.close()


def write_graph_json(paths: ProjectPaths, graph: dict | None = None) -> dict:
    graph = graph if graph is not None else build_graph(paths)
    paths.llmw_dir.mkdir(parents=True, exist_ok=True)
    paths.graph_json.write_text(
        jsonlib.dumps(graph, indent=2), encoding="utf-8", newline="\n"
    )
    return graph


_HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>llmw graph</title>
<style>
  html, body { margin: 0; height: 100%; background: #10141a; color: #e8e8e8; font-family: sans-serif; }
  #info { position: absolute; top: 8px; left: 8px; font-size: 13px; opacity: 0.85; }
  canvas { display: block; }
</style>
</head>
<body>
<div id="info">__NODE_COUNT__ nodes, __EDGE_COUNT__ edges</div>
<canvas id="c"></canvas>
<script>
const GRAPH = __GRAPH_JSON__;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
window.addEventListener('resize', resize);
resize();

const nodes = GRAPH.nodes.map((n, i) => ({
  ...n,
  x: canvas.width / 2 + Math.cos(i) * 100,
  y: canvas.height / 2 + Math.sin(i) * 100,
  vx: 0, vy: 0,
}));
const indexOf = Object.fromEntries(nodes.map((n, i) => [n.id, i]));
const edges = GRAPH.edges
  .filter(e => indexOf[e.source] !== undefined && indexOf[e.target] !== undefined)
  .map(e => ({ a: indexOf[e.source], b: indexOf[e.target] }));

function step() {
  const cx = canvas.width / 2, cy = canvas.height / 2;
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    n.vx += (cx - n.x) * 0.001;
    n.vy += (cy - n.y) * 0.001;
    for (let j = i + 1; j < nodes.length; j++) {
      const m = nodes[j];
      let dx = n.x - m.x, dy = n.y - m.y;
      let d2 = dx * dx + dy * dy || 0.01;
      let f = 800 / d2;
      let d = Math.sqrt(d2);
      n.vx += (dx / d) * f; n.vy += (dy / d) * f;
      m.vx -= (dx / d) * f; m.vy -= (dy / d) * f;
    }
  }
  for (const e of edges) {
    const a = nodes[e.a], b = nodes[e.b];
    const dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const targetLen = 140;
    const f = (d - targetLen) * 0.01;
    a.vx += (dx / d) * f; a.vy += (dy / d) * f;
    b.vx -= (dx / d) * f; b.vy -= (dy / d) * f;
  }
  for (const n of nodes) {
    n.vx *= 0.85; n.vy *= 0.85;
    n.x += n.vx; n.y += n.vy;
  }
}

function draw() {
  ctx.fillStyle = '#10141a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'rgba(150,170,200,0.35)';
  ctx.beginPath();
  for (const e of edges) {
    const a = nodes[e.a], b = nodes[e.b];
    ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
  }
  ctx.stroke();
  for (const n of nodes) {
    const r = 4 + Math.min(10, n.degree);
    ctx.fillStyle = '#7fb2ff';
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#e8e8e8';
    ctx.font = '11px sans-serif';
    ctx.fillText(n.title, n.x + r + 3, n.y + 3);
  }
}

function loop() { step(); draw(); requestAnimationFrame(loop); }
loop();
</script>
</body>
</html>
"""


def render_graph_html(graph: dict) -> str:
    # Page titles/tags come from wiki content (frontmatter an agent wrote,
    # possibly derived from untrusted raw/ material) and land verbatim in
    # this JSON blob. Without escaping "</", a title containing
    # "</script><script>..." would break out of the literal and execute in
    # whatever opens the exported graph.html.
    graph_json = jsonlib.dumps(graph).replace("</", "<\\/")
    return (
        _HTML_TEMPLATE.replace("__NODE_COUNT__", str(len(graph["nodes"])))
        .replace("__EDGE_COUNT__", str(len(graph["edges"])))
        .replace("__GRAPH_JSON__", graph_json)
    )


def write_graph_html(paths: ProjectPaths, graph: dict | None = None) -> None:
    graph = graph if graph is not None else build_graph(paths)
    paths.llmw_dir.mkdir(parents=True, exist_ok=True)
    paths.graph_html.write_text(render_graph_html(graph), encoding="utf-8", newline="\n")
