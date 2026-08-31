"""`llmw read` — look up a page by path/title/alias and show it briefly or in full."""

from __future__ import annotations

from dataclasses import dataclass, field

from llmw.frontmatter import InvalidFrontmatterError, body_after_block
from llmw.parser import extract_key_points, mask_non_prose, parse_page
from llmw.paths import ProjectPaths
from llmw.queries import (
    backlinks,
    find_page_row,
    open_ro,
    outgoing_links,
    page_columns,
    page_tags,
)


class PageNotFoundError(RuntimeError):
    pass


@dataclass
class ReadResult:
    path: str
    title: str
    type: str | None
    status: str | None
    summary: str | None
    # Set when the page has a frontmatter block that does not parse. The
    # page is still returned — losing its content over a broken metadata
    # field is the "worse than nothing" trade this tool exists to avoid.
    frontmatter_error: str | None
    # See llmw.freshness: the page's own claim vs. when the index last
    # observed the body change.
    updated: str | None
    body_changed_at: str | None
    key_points: list[str]
    tags: list[str]
    aliases: list[str]
    links: list[dict]
    backlinks_count: int | None
    backlink_paths: list[str]
    full_text: str | None = None
    indexed: bool = True

    def as_dict(self) -> dict:
        d = {
            "path": self.path,
            "title": self.title,
            "type": self.type,
            "status": self.status,
            "summary": self.summary,
            "frontmatter_error": self.frontmatter_error,
            "updated": self.updated,
            "body_changed_at": self.body_changed_at,
            "key_points": self.key_points,
            "tags": self.tags,
            "aliases": self.aliases,
            "links": self.links,
            "backlinks_count": self.backlinks_count,
            "backlink_paths": self.backlink_paths,
            "indexed": self.indexed,
        }
        if self.full_text is not None:
            d["full_text"] = self.full_text
        return d


def _resolve_path(paths: ProjectPaths, target: str) -> str | None:
    """Resolve `target` to a project-relative wiki path using the DB if
    available, falling back to a direct on-disk path check."""
    conn = open_ro(paths)
    if conn is not None:
        try:
            row = find_page_row(conn, target)
            if row is not None:
                return row["path"]
        finally:
            conn.close()

    normalized = target.replace("\\", "/")
    candidate = paths.root / normalized
    if candidate.is_file() and paths.is_inside_wiki(candidate):
        try:
            return paths.rel(candidate)
        except ValueError:
            # candidate resolves to a real file outside the project root
            # (e.g. target="../secret.md") — not a wiki page, so this is
            # "not found", not a crash.
            return None
    return None


def read_page(paths: ProjectPaths, target: str, full: bool = False) -> ReadResult:
    rel_path = _resolve_path(paths, target)
    if rel_path is None:
        raise PageNotFoundError(
            f'Page not found: "{target}"\n'
            f'Hint: Run `llmw search "{target}" --limit 5`.'
        )

    fs_path = paths.root / rel_path
    if not fs_path.is_file():
        raise PageNotFoundError(
            f"Page indexed but missing on disk: {rel_path}. Run `llmw rebuild`."
        )

    try:
        text = fs_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PageNotFoundError(
            f"{rel_path} is not valid UTF-8 text and can't be read as a wiki "
            f"page: {exc}"
        ) from exc
    try:
        page = parse_page(text, rel_path)
        frontmatter_error: str | None = None
    except InvalidFrontmatterError as exc:
        # The metadata is unreadable; the page is not. Refusing to show it
        # loses the content over a broken date field, and raising here put
        # a raw YAML traceback on the terminal. Read it as an untitled
        # page and say what is wrong — `llmw lint` reports the same thing
        # under `invalid_frontmatter`.
        frontmatter_error = str(exc).splitlines()[0]
        page = parse_page(body_after_block(text), rel_path)
    masked = mask_non_prose(page.body)
    key_points = extract_key_points(page.body, masked)

    links_out: list[dict] = []
    backlinks_count: int | None = None
    backlink_paths: list[str] = []
    body_changed_at: str | None = None
    indexed = True

    conn = open_ro(paths)
    if conn is not None:
        try:
            # See `queries.page_columns`: an index built before 0.1.31 has
            # no `body_changed_at`, and naming it made `llmw read` die.
            has_history = "body_changed_at" in page_columns(conn)
            row = conn.execute(
                "SELECT id, body_changed_at FROM pages WHERE path = ?"
                if has_history
                else "SELECT id FROM pages WHERE path = ?",
                (rel_path,),
            ).fetchone()
            if row is not None:
                page_id = row["id"]
                if has_history:
                    body_changed_at = row["body_changed_at"]
                for link in outgoing_links(conn, page_id):
                    links_out.append(
                        {
                            "target": link["target_title"] or link["target_raw"],
                            "kind": link["kind"],
                            "broken": not bool(link["exists_flag"]),
                        }
                    )
                back_rows = backlinks(conn, page_id)
                backlinks_count = len(back_rows)
                backlink_paths = [r["source_path"] for r in back_rows]
            else:
                indexed = False
        finally:
            conn.close()
    else:
        indexed = False

    return ReadResult(
        path=rel_path,
        title=page.title,
        type=page.type,
        status=page.status,
        summary=page.summary,
        frontmatter_error=frontmatter_error,
        updated=page.updated,
        # Only the index has the history this needs; None when the page
        # isn't indexed, which reads as "no divergence known".
        body_changed_at=body_changed_at,
        key_points=key_points,
        tags=page.tags,
        aliases=page.aliases,
        links=links_out,
        backlinks_count=backlinks_count,
        backlink_paths=backlink_paths,
        full_text=text if full else None,
        indexed=indexed,
    )
