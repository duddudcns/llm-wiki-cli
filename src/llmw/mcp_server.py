"""Native MCP tools for the llm-wiki Codex plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from llmw.bootstrap import init_project
from llmw.paths import resolve_paths
from llmw.read import read_page
from llmw.search import search
from llmw.status import build_status
from llmw.writer import write_page

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
    """Safely write a wiki Markdown page with audit reason and index update."""
    written = write_page(_paths(root), path, content, reason, force=force)
    return {"path": str(written), "written": True}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
