"""Shared read-only DB lookups used by read/links/backlinks/related/lint."""

from __future__ import annotations

import sqlite3

from llmw.paths import ProjectPaths


class IndexNotBuiltError(RuntimeError):
    """Raised by read-side commands when .llmw/index.sqlite does not exist yet."""


def open_ro(paths: ProjectPaths) -> sqlite3.Connection | None:
    """Open the index DB read-only, or return None if it hasn't been built."""
    if not paths.index_db.exists():
        return None
    conn = sqlite3.connect(paths.index_db)
    conn.row_factory = sqlite3.Row
    return conn


def find_page_row(conn: sqlite3.Connection, target: str) -> sqlite3.Row | None:
    """Resolve `target` (project-relative path, title, or alias) to a pages row."""
    normalized = target.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]

    row = conn.execute("SELECT * FROM pages WHERE path = ?", (normalized,)).fetchone()
    if row:
        return row

    row = conn.execute(
        "SELECT * FROM pages WHERE lower(title) = ?", (target.lower(),)
    ).fetchone()
    if row:
        return row

    row = conn.execute(
        """
        SELECT p.* FROM pages p
        JOIN aliases a ON a.page_id = p.id
        WHERE lower(a.alias) = ?
        """,
        (target.lower(),),
    ).fetchone()
    return row


def outgoing_links(conn: sqlite3.Connection, page_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT l.target_raw, l.target_heading, l.link_text, l.kind, l.exists_flag,
               tp.path AS target_path, tp.title AS target_title
        FROM links l
        LEFT JOIN pages tp ON tp.id = l.target_page_id
        WHERE l.source_page_id = ?
        ORDER BY l.id
        """,
        (page_id,),
    ).fetchall()


def backlinks(conn: sqlite3.Connection, page_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT l.target_raw, l.target_heading, l.link_text, l.kind,
               sp.path AS source_path, sp.title AS source_title
        FROM links l
        JOIN pages sp ON sp.id = l.source_page_id
        WHERE l.target_page_id = ? AND sp.id != ?
        ORDER BY sp.path
        """,
        (page_id, page_id),
    ).fetchall()


def page_tags(conn: sqlite3.Connection, page_id: int) -> list[str]:
    return [r["tag"] for r in conn.execute("SELECT tag FROM tags WHERE page_id = ?", (page_id,))]
