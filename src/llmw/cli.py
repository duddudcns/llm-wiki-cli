"""llmw CLI entry point (typer app)."""

from __future__ import annotations

import json as jsonlib
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

import sys

from llmw import __version__
from llmw.archive import PageNotFoundForArchiveError, archive_page as do_archive
from llmw.bootstrap import ProjectAlreadyExistsError, init_project
from llmw.frontmatter import InvalidFrontmatterError
from llmw.graph import build_graph, write_graph_html, write_graph_json
from llmw.health import check_health
from llmw.indexer import index_changed, rebuild as rebuild_index
from llmw.ingest import (
    SourceAlreadyIngestedError,
    SourceNotFoundError,
    SourceNotInRawError,
    UnsupportedSourceTypeError,
    ingest_source,
)
from llmw.lint import run_lint
from llmw.locks import LockedError
from llmw.patching import PatchApplyError
from llmw.paths import ProjectNotFoundError, resolve_paths
from llmw.queries import IndexNotBuiltError, backlinks as query_backlinks, find_page_row, open_ro
from llmw.queries import outgoing_links as query_outgoing_links
from llmw.read import PageNotFoundError, read_page
from llmw.related import DEFAULT_CATEGORIES, PageNotIndexedError, related as related_pages
from llmw.safety import PathNotAllowedError, ReasonRequiredError
from llmw.search import search as search_pages
from llmw.status import build_status
from llmw.writer import (
    FileExistsConflictError,
    FileNotFoundForPatchError,
    patch_page as do_patch,
    write_page as do_write,
)

app = typer.Typer(
    name="llmw",
    help="Headless Obsidian-like LLM Wiki CLI for AI agents.",
    no_args_is_help=True,
)
# markup=False/highlight=False everywhere: wiki content (titles, summaries,
# link targets, error messages) is arbitrary user text and must never be
# parsed as rich markup — a page containing e.g. "[LEA-3004]" next to
# anything bracket-slash-shaped can otherwise raise rich.errors.MarkupError
# and crash the whole command, or silently swallow "[bold]...[/bold]"-shaped
# substrings. See git log for the bug this fixed.
console = Console(markup=False, highlight=False)
err_console = Console(stderr=True, markup=False, highlight=False)


def _err(message: object) -> None:
    err_console.print(f"ERROR: {message}", style="bold red")


def _warn(message: object) -> None:
    err_console.print(f"WARN: {message}", style="yellow")


def _print_json(payload) -> None:
    # Deliberately bypass rich here, not just its markup parsing: Console
    # also soft-wraps long lines at terminal width by default, which would
    # inject a hard newline into the middle of a JSON string value and
    # break `json.loads` on the other end. Plain stdlib print has neither
    # failure mode.
    print(jsonlib.dumps(payload, indent=2))


def _version_callback(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


def _require_paths():
    try:
        return resolve_paths()
    except ProjectNotFoundError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True
    ),
) -> None:
    """llmw: headless Obsidian-like LLM Wiki CLI."""


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Project root to initialize."),
    force: bool = typer.Option(False, "--force", help="Reinitialize an existing project."),
    claude_plugin: bool = typer.Option(
        True,
        "--claude-plugin/--no-claude-plugin",
        help=(
            "Scaffold a project-local .claude/skills/llm-wiki/ and "
            ".claude-plugin/plugin.json. Use --no-claude-plugin if the "
            "llm-wiki Claude Code plugin is already installed from the "
            "marketplace, to avoid a redundant local copy of the same skill."
        ),
    ),
) -> None:
    """Scaffold raw/, wiki/, .llmw/, and (by default) the Claude Code skill/plugin."""
    try:
        paths = init_project(path, force=force, claude_plugin=claude_plugin)
    except ProjectAlreadyExistsError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    console.print(f"Initialized llmw project at {paths.root}", style="bold")


@app.command()
def status(
    brief: bool = typer.Option(True, "--brief/--no-brief"),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Show a quick summary of the wiki and index state."""
    paths = _require_paths()
    report = build_status(paths)

    if json:
        _print_json(report.as_dict())
        return

    console.print(f"wiki pages:     {report.wiki_page_count}")
    console.print(f"raw sources:    {report.raw_source_count}")
    if not report.index_exists:
        console.print("index:          not built yet — run `llmw rebuild`")
        return
    console.print(f"indexed pages:  {report.indexed_page_count}")
    console.print(f"broken links:   {report.broken_links_count}")
    console.print(f"orphan pages:   {report.orphan_pages_count}")
    console.print(f"dirty pages:    {report.dirty_pages_count}")
    console.print(f"last indexed:   {report.last_indexed}")


def _report_sync(label: str, stats, json: bool) -> None:
    if json:
        console.print(
            jsonlib.dumps(
                {
                    "files_scanned": stats.files_scanned,
                    "pages_indexed": stats.pages_indexed,
                    "pages_removed": stats.pages_removed,
                    "errors": stats.errors,
                },
                indent=2,
            )
        )
        return
    console.print(
        f"{label}: scanned {stats.files_scanned}, indexed {stats.pages_indexed}, "
        f"removed {stats.pages_removed}"
    )
    for path, message in stats.errors:
        _warn(f"{path}: {message}")


@app.command()
def rebuild(json: bool = typer.Option(False, "--json")) -> None:
    """Fully re-index wiki/**/*.md from scratch."""
    paths = _require_paths()
    stats = rebuild_index(paths)
    _report_sync("rebuild", stats, json)


@app.command()
def index(
    changed: bool = typer.Option(
        True, "--changed/--all", help="Only reindex files whose mtime and hash changed."
    ),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Incrementally re-index wiki/**/*.md (hash/mtime based)."""
    paths = _require_paths()
    stats = rebuild_index(paths) if not changed else index_changed(paths)
    _report_sync("index", stats, json)


@app.command()
def search(
    query: str = typer.Argument(...),
    limit: int = typer.Option(5, "--limit"),
    type: Optional[str] = typer.Option(None, "--type"),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Full-text search over wiki page title/summary/body."""
    paths = _require_paths()
    try:
        results = search_pages(paths, query, limit=limit, type_filter=type)
    except IndexNotBuiltError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc

    if json:
        _print_json([r.as_dict() for r in results])
        return

    if not results:
        console.print(f'No results for "{query}".')
        return
    for i, r in enumerate(results, start=1):
        console.print(f"{i}. {r.path}")
        console.print(f"   score: {r.score}")
        if r.summary:
            console.print(f"   summary: {r.summary}")
        if r.links:
            console.print(f"   links: {', '.join(f'[[{t}]]' for t in r.links[:5])}")


@app.command()
def read(
    target: str = typer.Argument(..., help="Path, title, or alias."),
    full: bool = typer.Option(False, "--full/--brief"),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Read a wiki page by path, title, or alias (brief by default)."""
    paths = _require_paths()
    try:
        result = read_page(paths, target, full=full)
    except PageNotFoundError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc

    if json:
        _print_json(result.as_dict())
        return

    if full:
        console.print(result.full_text)
        return

    console.print(f"title:     {result.title}")
    console.print(f"type:      {result.type}")
    console.print(f"status:    {result.status}")
    console.print(f"summary:   {result.summary}")
    if result.key_points:
        console.print("key points:")
        for kp in result.key_points:
            console.print(f"  - {kp}")
    if result.links:
        broken = sum(1 for l in result.links if l["broken"])
        console.print(f"links:     {len(result.links)} ({broken} broken)")
    if result.indexed:
        console.print(f"backlinks: {result.backlinks_count}")
    else:
        console.print("backlinks: unknown (run `llmw rebuild`)")


@app.command()
def related(
    target: str = typer.Argument(...),
    limit: int = typer.Option(10, "--limit"),
    by: str = typer.Option(
        ",".join(DEFAULT_CATEGORIES), "--by", help="Comma-separated: links,tags,terms"
    ),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Deterministic related-page candidates (links/tags/terms), no model calls."""
    paths = _require_paths()
    categories = tuple(c.strip() for c in by.split(",") if c.strip())
    try:
        results = related_pages(paths, target, limit=limit, by=categories)
    except (IndexNotBuiltError, PageNotIndexedError) as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc

    if json:
        _print_json([r.as_dict() for r in results])
        return

    if not results:
        console.print("No related pages found.")
        return
    for i, r in enumerate(results, start=1):
        console.print(f"{i}. {r.path}")
        console.print(f"   relation: {', '.join(r.reasons)}")
        console.print(f"   score: {r.score}")


def _resolve_or_exit(conn, target: str):
    row = find_page_row(conn, target)
    if row is None:
        _err(f'Page not found: "{target}"\nHint: Run `llmw search "{target}" --limit 5`.')
        raise typer.Exit(code=1)
    return row


@app.command()
def links(target: str = typer.Argument(...), json: bool = typer.Option(False, "--json")) -> None:
    """Outgoing links from a page, with broken status."""
    paths = _require_paths()
    conn = open_ro(paths)
    if conn is None:
        _err("Index not built yet. Run `llmw rebuild` first.")
        raise typer.Exit(code=1)
    try:
        row = _resolve_or_exit(conn, target)
        rows = query_outgoing_links(conn, row["id"])
        items = [
            {
                "target": r["target_title"] or r["target_raw"],
                "kind": r["kind"],
                "broken": not bool(r["exists_flag"]),
            }
            for r in rows
        ]
    finally:
        conn.close()

    if json:
        _print_json(items)
        return
    if not items:
        console.print("No outgoing links.")
        return
    for item in items:
        flag = " (broken)" if item["broken"] else ""
        console.print(f"[[{item['target']}]] ({item['kind']}){flag}")


@app.command()
def backlinks(
    target: str = typer.Argument(...), json: bool = typer.Option(False, "--json")
) -> None:
    """Incoming links to a page."""
    paths = _require_paths()
    conn = open_ro(paths)
    if conn is None:
        _err("Index not built yet. Run `llmw rebuild` first.")
        raise typer.Exit(code=1)
    try:
        row = _resolve_or_exit(conn, target)
        rows = query_backlinks(conn, row["id"])
        items = [{"source": r["source_path"], "title": r["source_title"]} for r in rows]
    finally:
        conn.close()

    if json:
        _print_json(items)
        return
    if not items:
        console.print("No backlinks.")
        return
    for item in items:
        console.print(f"{item['source']}  ({item['title']})")


@app.command()
def lint(
    brief: bool = typer.Option(False, "--brief"),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Report broken links, orphans, duplicate titles/aliases, missing
    frontmatter, and other deterministic wiki issues. Never auto-fixes."""
    paths = _require_paths()
    try:
        report = run_lint(paths)
    except IndexNotBuiltError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc

    if json:
        _print_json(report.as_dict())
        raise typer.Exit(code=0 if report.is_clean() else 1)

    counts = report.counts()
    if brief:
        for name, count in counts.items():
            console.print(f"{name}: {count}")
        raise typer.Exit(code=0 if report.is_clean() else 1)

    for name, count in counts.items():
        if count == 0:
            continue
        console.print(f"{name} ({count})", style="bold")
        items = getattr(report, name)
        entries = items.items() if isinstance(items, dict) else enumerate(items)
        for _, value in list(entries)[:10]:
            console.print(f"  - {value}")
    if report.is_clean():
        console.print("No issues found.")
    raise typer.Exit(code=0 if report.is_clean() else 1)


@app.command()
def health(brief: bool = typer.Option(False, "--brief")) -> None:
    """System-level checks: config, index db, schema version, directories, locks."""
    paths = _require_paths()
    report = check_health(paths)

    if brief:
        console.print("healthy" if report.is_healthy() else "unhealthy")
        raise typer.Exit(code=0 if report.is_healthy() else 1)

    for name, ok in report.checks.items():
        mark = "OK" if ok else "FAIL"
        detail = f" — {report.details[name]}" if name in report.details else ""
        console.print(f"[{mark}] {name}{detail}")
    raise typer.Exit(code=0 if report.is_healthy() else 1)


graph_app = typer.Typer(help="Build/export the wiki link graph.")
app.add_typer(graph_app, name="graph")


@graph_app.command("build")
def graph_build(json: bool = typer.Option(False, "--json")) -> None:
    """Regenerate .llmw/graph.json."""
    paths = _require_paths()
    try:
        graph = write_graph_json(paths)
    except IndexNotBuiltError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    if json:
        _print_json(graph)
    else:
        console.print(
            f"graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges "
            f"-> {paths.graph_json}"
        )


@graph_app.command("export")
def graph_export(
    format: str = typer.Option("json", "--format", help="json | html | both"),
) -> None:
    """Write graph.json and/or graph.html."""
    paths = _require_paths()
    try:
        graph = build_graph(paths)
    except IndexNotBuiltError as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc

    if format in ("json", "both"):
        write_graph_json(paths, graph)
        console.print(f"wrote {paths.graph_json}")
    if format in ("html", "both"):
        write_graph_html(paths, graph)
        console.print(f"wrote {paths.graph_html}")
    if format not in ("json", "html", "both"):
        _err(f"unknown --format {format!r}")
        raise typer.Exit(code=1)


def _read_stdin_content(stdin: bool) -> str:
    if not stdin:
        _err("Provide content via `--stdin` (pipe it in).")
        raise typer.Exit(code=1)
    return sys.stdin.read()


@app.command()
def write(
    path: str = typer.Argument(...),
    reason: str = typer.Option(..., "--reason"),
    stdin: bool = typer.Option(False, "--stdin", help="Read new page content from stdin."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing page."),
) -> None:
    """Create a new wiki page from stdin. Fails if it already exists unless --force."""
    paths = _require_paths()
    content = _read_stdin_content(stdin)
    try:
        fs_path = do_write(paths, path, content, reason=reason, force=force)
    except (
        ReasonRequiredError,
        PathNotAllowedError,
        FileExistsConflictError,
        InvalidFrontmatterError,
        LockedError,
    ) as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    console.print(f"wrote {paths.rel(fs_path)}")


@app.command()
def patch(
    path: str = typer.Argument(...),
    reason: str = typer.Option(..., "--reason"),
    stdin: bool = typer.Option(False, "--stdin", help="Read a unified diff from stdin."),
) -> None:
    """Apply a unified diff to an existing wiki page. Backs up first; rolls
    back (leaves the original untouched) if the patch fails to apply."""
    paths = _require_paths()
    diff_text = _read_stdin_content(stdin)
    try:
        fs_path = do_patch(paths, path, diff_text, reason=reason)
    except (
        ReasonRequiredError,
        PathNotAllowedError,
        FileNotFoundForPatchError,
        PatchApplyError,
        InvalidFrontmatterError,
        LockedError,
    ) as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    console.print(f"patched {paths.rel(fs_path)}")


@app.command()
def archive(
    path: str = typer.Argument(...),
    reason: str = typer.Option(..., "--reason"),
    tombstone: Optional[bool] = typer.Option(
        None, "--tombstone/--no-tombstone", help="Leave a stub at the original path (default: on)."
    ),
) -> None:
    """Move a page to wiki/archived/YYYY/MM/, stamp archive frontmatter, log the change."""
    paths = _require_paths()
    try:
        dest = do_archive(paths, path, reason=reason, tombstone=tombstone)
    except (
        ReasonRequiredError,
        PathNotAllowedError,
        PageNotFoundForArchiveError,
        LockedError,
    ) as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    console.print(f"archived to {paths.rel(dest)}")


@app.command()
def ingest(source: str = typer.Argument(..., help="Path under raw/ to register.")) -> None:
    """Register a raw/ source as a wiki/sources/<slug>.md draft (.md/.txt only in MVP)."""
    paths = _require_paths()
    try:
        dest = ingest_source(paths, source)
    except (
        SourceNotFoundError,
        SourceNotInRawError,
        UnsupportedSourceTypeError,
        SourceAlreadyIngestedError,
    ) as exc:
        _err(exc)
        raise typer.Exit(code=1) from exc
    console.print(f"ingested -> {paths.rel(dest)}")


if __name__ == "__main__":
    app()
