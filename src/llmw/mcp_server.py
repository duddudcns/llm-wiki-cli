"""Native MCP tools for the llm-wiki Codex plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from llmw.archive import archive_page
from llmw.bootstrap import init_project
from llmw.graph import build_graph
from llmw.health import check_health
from llmw.ingest import ingest_source
from llmw.lint import run_lint
from llmw.paths import resolve_paths
from llmw.queries import (
    IndexNotBuiltError,
    backlinks as query_backlinks,
    find_page_row,
    open_ro,
    outgoing_links as query_outgoing_links,
)
from llmw.read import PageNotFoundError, read_page
from llmw.related import DEFAULT_CATEGORIES, related as related_pages
from llmw.search import search
from llmw.status import build_status
from llmw.writer import edit_page, patch_page, write_page

mcp = FastMCP("llm-wiki")


def _paths(root: str | None):
    return resolve_paths(start=Path.cwd(), root_override=Path(root) if root else None)


@mcp.tool()
def llmw_init(path: str = ".", layout: str = "classic") -> dict[str, Any]:
    """Initialize a project-local LLM wiki. Use layout 'classic' or 'ai-wiki'."""
    paths = init_project(Path(path), claude_plugin=False, layout=layout)
    return {"project_root": str(paths.project_root), "wiki_root": str(paths.root)}


@mcp.tool()
def llmw_status(root: str | None = None) -> dict[str, Any]:
    """Return wiki/index health and page counts for a project."""
    return build_status(_paths(root)).as_dict()


@mcp.tool()
def llmw_search(query: str, root: str | None = None, limit: int = 5) -> dict[str, Any]:
    """Search the indexed project wiki by keywords."""
    return search(_paths(root), query, limit=limit).as_dict()


@mcp.tool()
def llmw_read(target: str, root: str | None = None, full: bool = False) -> dict[str, Any]:
    """Read a wiki page by path, title, or alias."""
    return read_page(_paths(root), target, full=full).as_dict()


@mcp.tool()
def llmw_write(
    path: str,
    content: str,
    reason: str,
    root: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Create a wiki page, or fully replace an existing one with force=true.
    For an existing page, prefer llmw_edit (small exact-text change) or
    llmw_patch (structural diff) over force=true unless most of the page
    is actually changing — this call requires resending the full content
    either way."""
    written = write_page(_paths(root), path, content, reason, force=force)
    return {"path": str(written), "written": True}


@mcp.tool()
def llmw_edit(
    path: str,
    old: str,
    new: str,
    reason: str,
    root: str | None = None,
    replace_all: bool = False,
) -> dict[str, Any]:
    """Exact-string replace in an existing wiki page — prefer this over
    llmw_write for a small, contiguous change so the rest of the page
    doesn't need to be read and resent in full."""
    fs_path = edit_page(_paths(root), path, old, new, reason, replace_all=replace_all)
    return {"path": str(fs_path), "edited": True}


@mcp.tool()
def llmw_patch(path: str, diff: str, reason: str, root: str | None = None) -> dict[str, Any]:
    """Apply a unified diff to an existing wiki page. Backs up first; rolls
    back (leaves the original untouched) if the patch fails to apply."""
    fs_path = patch_page(_paths(root), path, diff, reason)
    return {"path": str(fs_path), "patched": True}


@mcp.tool()
def llmw_archive(
    path: str,
    reason: str,
    root: str | None = None,
    tombstone: bool | None = None,
) -> dict[str, Any]:
    """Move a page to wiki/archived/YYYY/MM/, stamp archive frontmatter, and
    log the change. There is no delete — this is the sanctioned way to
    retire a page. tombstone (default: project config, else True) leaves a
    stub with `moved_to:` at the original path."""
    dest = archive_page(_paths(root), path, reason, tombstone=tombstone)
    return {"path": str(dest), "archived": True}


@mcp.tool()
def llmw_related(
    target: str,
    root: str | None = None,
    limit: int = 10,
    by: str = ",".join(DEFAULT_CATEGORIES),
) -> dict[str, Any]:
    """Deterministic related-page candidates for a page (shared links,
    tags, title/term overlap) — no model calls. `by` is a comma-separated
    subset of links,tags,terms."""
    categories = tuple(c.strip() for c in by.split(",") if c.strip())
    results = related_pages(_paths(root), target, limit=limit, by=categories)
    return {"results": [r.as_dict() for r in results]}


@mcp.tool()
def llmw_links(target: str, root: str | None = None) -> dict[str, Any]:
    """Outgoing links from a page, with broken status."""
    conn = open_ro(_paths(root))
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")
    try:
        row = find_page_row(conn, target)
        if row is None:
            raise PageNotFoundError(f'Page not found: "{target}"')
        items = [
            {
                "target": r["target_title"] or r["target_raw"],
                "kind": r["kind"],
                "broken": not bool(r["exists_flag"]),
            }
            for r in query_outgoing_links(conn, row["id"])
        ]
    finally:
        conn.close()
    return {"links": items}


@mcp.tool()
def llmw_backlinks(target: str, root: str | None = None) -> dict[str, Any]:
    """Incoming links to a page."""
    conn = open_ro(_paths(root))
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")
    try:
        row = find_page_row(conn, target)
        if row is None:
            raise PageNotFoundError(f'Page not found: "{target}"')
        items = [
            {"source": r["source_path"], "title": r["source_title"]}
            for r in query_backlinks(conn, row["id"])
        ]
    finally:
        conn.close()
    return {"backlinks": items}


@mcp.tool()
def llmw_lint(root: str | None = None) -> dict[str, Any]:
    """Report broken links, orphans, duplicate titles/aliases, missing
    frontmatter, and other deterministic wiki issues. Never auto-fixes —
    fix findings via llmw_edit/llmw_patch/llmw_write/llmw_archive."""
    report = run_lint(_paths(root))
    result = report.as_dict()
    result["clean"] = report.is_clean()
    return result


@mcp.tool()
def llmw_health(root: str | None = None) -> dict[str, Any]:
    """System-level checks distinct from llmw_lint's content checks: config
    readable, index db readable and on the expected schema version, no
    stale locks."""
    return check_health(_paths(root)).as_dict()


@mcp.tool()
def llmw_ingest(source: str, root: str | None = None) -> dict[str, Any]:
    """Register a raw/ source (.md/.txt only) as a wiki/sources/<slug>.md
    draft, ready for llmw_edit/llmw_write to flesh out."""
    dest = ingest_source(_paths(root), source)
    return {"path": str(dest), "ingested": True}


@mcp.tool()
def llmw_graph(root: str | None = None) -> dict[str, Any]:
    """The wiki's link graph: nodes (pages, with type/tags/degree) and
    edges (resolved wikilink/embed/mdlink references). Read-only — does
    not write graph.json/graph.html, which are derived data owned by the
    host project."""
    return build_graph(_paths(root))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
