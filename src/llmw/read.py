"""`llmw read` — look up a page by path/title/alias and show it briefly or in full."""

from __future__ import annotations

from dataclasses import dataclass, field

from llmw.parser import extract_key_points, mask_non_prose, parse_page
from llmw.paths import ProjectPaths
from llmw.queries import backlinks, find_page_row, open_ro, outgoing_links, page_tags


class PageNotFoundError(RuntimeError):
    pass


@dataclass
class ReadResult:
    path: str
    title: str
    type: str | None
    status: str | None
    summary: str | None
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
    if candidate.is_file():
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

    text = fs_path.read_text(encoding="utf-8")
    page = parse_page(text, rel_path)
    masked = mask_non_prose(page.body)
    key_points = extract_key_points(page.body, masked)

    links_out: list[dict] = []
    backlinks_count: int | None = None
    backlink_paths: list[str] = []
    indexed = True

    conn = open_ro(paths)
    if conn is not None:
        try:
            row = conn.execute("SELECT id FROM pages WHERE path = ?", (rel_path,)).fetchone()
            if row is not None:
                page_id = row["id"]
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
        key_points=key_points,
        tags=page.tags,
        aliases=page.aliases,
        links=links_out,
        backlinks_count=backlinks_count,
        backlink_paths=backlink_paths,
        full_text=text if full else None,
        indexed=indexed,
    )
