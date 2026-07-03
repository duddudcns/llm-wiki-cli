"""SQLite index over wiki/*.md — the only derived, rebuildable data store.

Deviations from the original design sketch, both for robustness:
- The `links.exists` column is named `exists_flag` (`EXISTS` is a SQL
  keyword).
- `pages_fts` is a *standalone* FTS5 table (not `content=`-linked to
  `pages`) so deleting/updating a row never requires re-supplying the old
  indexed column values — a plain `DELETE ... WHERE rowid = ?` suffices.
"""

from __future__ import annotations

import datetime
import posixpath
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from llmw.models import Page
from llmw.parser import parse_page
from llmw.paths import ProjectPaths

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    type TEXT,
    status TEXT,
    summary TEXT,
    body TEXT NOT NULL,
    hash TEXT NOT NULL,
    mtime REAL NOT NULL,
    created_at TEXT,
    updated_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    title, summary, body, path UNINDEXED
);

CREATE TABLE IF NOT EXISTS aliases (
    page_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    UNIQUE(page_id, alias)
);

CREATE TABLE IF NOT EXISTS tags (
    page_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    UNIQUE(page_id, tag)
);

CREATE TABLE IF NOT EXISTS headings (
    page_id INTEGER NOT NULL,
    heading TEXT NOT NULL,
    level INTEGER NOT NULL,
    slug TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    source_page_id INTEGER NOT NULL,
    target_raw TEXT NOT NULL,
    target_page_id INTEGER,
    target_heading TEXT,
    link_text TEXT,
    kind TEXT NOT NULL,
    exists_flag INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS external_links (
    id INTEGER PRIMARY KEY,
    source_page_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    text TEXT
);

CREATE TABLE IF NOT EXISTS log_entries (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    action TEXT NOT NULL,
    path TEXT,
    reason TEXT,
    detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_page_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_page_id);
CREATE INDEX IF NOT EXISTS idx_aliases_page ON aliases(page_id);
CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);
"""


@dataclass
class SyncStats:
    files_scanned: int = 0
    pages_indexed: int = 0
    pages_removed: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)


def connect(paths: ProjectPaths) -> sqlite3.Connection:
    paths.llmw_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(paths.index_db)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_SQL)
    conn.execute(
        "INSERT INTO meta(key, value) VALUES ('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def iter_wiki_files(paths: ProjectPaths) -> list[Path]:
    if not paths.wiki.exists():
        return []
    return sorted(paths.wiki.rglob("*.md"))


def _delete_page(conn: sqlite3.Connection, page_id: int) -> None:
    conn.execute("DELETE FROM pages_fts WHERE rowid = ?", (page_id,))
    conn.execute("DELETE FROM aliases WHERE page_id = ?", (page_id,))
    conn.execute("DELETE FROM tags WHERE page_id = ?", (page_id,))
    conn.execute("DELETE FROM headings WHERE page_id = ?", (page_id,))
    conn.execute("DELETE FROM links WHERE source_page_id = ?", (page_id,))
    conn.execute("DELETE FROM external_links WHERE source_page_id = ?", (page_id,))
    conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))


def _insert_page(conn: sqlite3.Connection, page: Page) -> int:
    cur = conn.execute(
        """
        INSERT INTO pages (path, title, type, status, summary, body, hash, mtime,
                            created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            page.path,
            page.title,
            page.type,
            page.status,
            page.summary,
            page.body,
            page.content_hash,
            page.mtime,
            page.created,
            page.updated,
        ),
    )
    page_id = cur.lastrowid

    conn.execute(
        "INSERT INTO pages_fts(rowid, title, summary, body, path) VALUES (?, ?, ?, ?, ?)",
        (page_id, page.title, page.summary or "", page.body, page.path),
    )
    for alias in page.aliases:
        conn.execute(
            "INSERT OR IGNORE INTO aliases(page_id, alias) VALUES (?, ?)",
            (page_id, alias),
        )
    for tag in page.tags:
        conn.execute(
            "INSERT OR IGNORE INTO tags(page_id, tag) VALUES (?, ?)", (page_id, tag)
        )
    for heading in page.headings:
        conn.execute(
            "INSERT INTO headings(page_id, heading, level, slug) VALUES (?, ?, ?, ?)",
            (page_id, heading.text, heading.level, heading.slug),
        )
    for link in page.links:
        conn.execute(
            """
            INSERT INTO links(source_page_id, target_raw, target_page_id,
                               target_heading, link_text, kind, exists_flag)
            VALUES (?, ?, NULL, ?, ?, ?, 0)
            """,
            (page_id, link.target_raw, link.target_heading, link.link_text, link.kind),
        )
    for ext in page.external_links:
        conn.execute(
            "INSERT INTO external_links(source_page_id, url, text) VALUES (?, ?, ?)",
            (page_id, ext.url, ext.text),
        )
    return page_id


def _parse_file(fs_path: Path, rel_path: str) -> Page:
    text = fs_path.read_text(encoding="utf-8")
    page = parse_page(text, rel_path)
    page.mtime = fs_path.stat().st_mtime
    return page


def _resolve_links(conn: sqlite3.Connection) -> None:
    by_path: dict[str, int] = {}
    by_title: dict[str, int] = {}
    by_alias: dict[str, int] = {}

    for row in conn.execute("SELECT id, path, title FROM pages"):
        path_key = row["path"].lower()
        by_path.setdefault(path_key, row["id"])
        stem_key = Path(row["path"]).stem.lower()
        by_path.setdefault(stem_key, row["id"])
        by_title.setdefault(row["title"].lower(), row["id"])

    for row in conn.execute("SELECT page_id, alias FROM aliases"):
        by_alias.setdefault(row["alias"].lower(), row["page_id"])

    for row in conn.execute("SELECT id, source_page_id, target_raw, kind FROM links"):
        target_raw = row["target_raw"].strip()
        kind = row["kind"]

        if target_raw == "":
            target_id = row["source_page_id"]
        elif kind == "mdlink":
            src_row = conn.execute(
                "SELECT path FROM pages WHERE id = ?", (row["source_page_id"],)
            ).fetchone()
            source_dir = posixpath.dirname(src_row["path"]) if src_row else ""
            candidate = posixpath.normpath(posixpath.join(source_dir, target_raw))
            target_id = by_path.get(candidate.lower()) or by_path.get(target_raw.lower())
        else:
            lk = target_raw.lower()
            target_id = by_path.get(lk) or by_title.get(lk) or by_alias.get(lk)

        conn.execute(
            "UPDATE links SET target_page_id = ?, exists_flag = ? WHERE id = ?",
            (target_id, 1 if target_id is not None else 0, row["id"]),
        )


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def _sync(conn: sqlite3.Connection, paths: ProjectPaths, force: bool) -> SyncStats:
    stats = SyncStats()
    files = iter_wiki_files(paths)
    seen_paths: set[str] = set()

    existing = {
        row["path"]: (row["id"], row["hash"], row["mtime"])
        for row in conn.execute("SELECT id, path, hash, mtime FROM pages")
    }

    for fs_path in files:
        rel_path = paths.rel(fs_path)
        seen_paths.add(rel_path)
        stats.files_scanned += 1

        prior = existing.get(rel_path)
        mtime = fs_path.stat().st_mtime
        if not force and prior is not None and prior[2] == mtime:
            continue

        try:
            page = _parse_file(fs_path, rel_path)
        except Exception as exc:  # noqa: BLE001 - one bad file must not abort the rebuild
            stats.errors.append((rel_path, str(exc)))
            continue

        if prior is not None:
            _delete_page(conn, prior[0])
        _insert_page(conn, page)
        stats.pages_indexed += 1

    for rel_path, (page_id, _hash, _mtime) in existing.items():
        if rel_path not in seen_paths:
            _delete_page(conn, page_id)
            stats.pages_removed += 1

    _resolve_links(conn)
    _set_meta(conn, "last_indexed", datetime.datetime.now().isoformat(timespec="seconds"))
    conn.commit()
    return stats


def rebuild(paths: ProjectPaths) -> SyncStats:
    if paths.index_db.exists():
        paths.index_db.unlink()
    conn = connect(paths)
    try:
        return _sync(conn, paths, force=True)
    finally:
        conn.close()


def index_changed(paths: ProjectPaths) -> SyncStats:
    conn = connect(paths)
    try:
        return _sync(conn, paths, force=False)
    finally:
        conn.close()
