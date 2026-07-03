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
import hashlib
import posixpath
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from llmw.config import Config, load_config
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


def iter_wiki_files(paths: ProjectPaths, config: Config | None = None) -> list[Path]:
    files: set[Path] = set()
    if paths.wiki.exists():
        files.update(paths.wiki.rglob("*.md"))

    root_resolved = paths.root.resolve()
    for rel in (config.extra_root_pages if config else []):
        candidate = (paths.root / rel).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            continue  # config tried to point outside the project root
        if candidate.is_file():
            files.add(candidate)

    return sorted(files)


def load_project_config(paths: ProjectPaths) -> Config:
    if paths.config_path.exists():
        return load_config(paths.config_path)
    return Config()


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


def _candidate_path_variants(target: str) -> list[str]:
    variants = [target]
    if not target.lower().endswith(".md"):
        variants.append(f"{target}.md")
    return variants


def _resolve_via_known_pages(
    target_raw: str,
    kind: str,
    source_path: str,
    wiki_prefix: str,
    by_path: dict[str, int],
    by_title: dict[str, int],
    by_alias: dict[str, int],
) -> int | None:
    lk = target_raw.lower()
    source_dir = posixpath.dirname(source_path) if source_path else ""

    if kind == "mdlink":
        candidate = posixpath.normpath(posixpath.join(source_dir, target_raw))
        return by_path.get(candidate.lower()) or by_path.get(lk)

    # wikilink / embed / related — title/alias/bare-path lookup first...
    if lk in by_path:
        return by_path[lk]
    if lk in by_title:
        return by_title[lk]
    if lk in by_alias:
        return by_alias[lk]
    if "/" not in target_raw:
        return None
    # ...then, for path-like targets, try two conventions that both show
    # up in the wild: `related:` entries written as full project-relative
    # paths (e.g. "wiki/concepts/foo") resolve relative to the source
    # page's own directory; genuine Obsidian wikilinks written inside the
    # `wiki/` vault (e.g. `[[concepts/foo]]`) are relative to the *vault
    # root* (`wiki/`), not the project root and not the current file.
    source_relative = posixpath.normpath(posixpath.join(source_dir, target_raw))
    if source_relative.lower() in by_path:
        return by_path[source_relative.lower()]
    vault_relative = posixpath.normpath(posixpath.join(wiki_prefix, target_raw))
    if vault_relative.lower() in by_path:
        return by_path[vault_relative.lower()]
    return None


def _resolve_via_filesystem(
    paths: ProjectPaths, source_path: str, wiki_prefix: str, target_raw: str
) -> bool:
    """Fallback for path-like references (relative wikilinks such as
    `[[../authoring]]`, or `related:` entries) that don't resolve to an
    indexed wiki page but do point at a real file elsewhere in the
    project — these should not be reported as broken links."""
    if "/" not in target_raw and "\\" not in target_raw:
        return False

    source_dir = posixpath.dirname(source_path) if source_path else ""
    root_resolved = paths.root.resolve()
    for base_dir in (source_dir, wiki_prefix, ""):
        for variant in _candidate_path_variants(target_raw):
            candidate = posixpath.normpath(posixpath.join(base_dir, variant))
            fs_candidate = (paths.root / candidate).resolve()
            try:
                fs_candidate.relative_to(root_resolved)
            except ValueError:
                continue  # escapes the project root — don't stat arbitrary paths
            if fs_candidate.is_file():
                return True
    return False


def _resolve_links(conn: sqlite3.Connection, paths: ProjectPaths) -> None:
    wiki_prefix = paths.rel(paths.wiki)
    by_path: dict[str, int] = {}
    by_title: dict[str, int] = {}
    by_alias: dict[str, int] = {}
    id_to_path: dict[int, str] = {}

    for row in conn.execute("SELECT id, path, title FROM pages"):
        id_to_path[row["id"]] = row["path"]
        path_key = row["path"].lower()
        by_path.setdefault(path_key, row["id"])
        if path_key.endswith(".md"):
            by_path.setdefault(path_key[:-3], row["id"])
        stem_key = Path(row["path"]).stem.lower()
        by_path.setdefault(stem_key, row["id"])
        by_title.setdefault(row["title"].lower(), row["id"])

    for row in conn.execute("SELECT page_id, alias FROM aliases"):
        by_alias.setdefault(row["alias"].lower(), row["page_id"])

    for row in conn.execute("SELECT id, source_page_id, target_raw, kind FROM links"):
        target_raw = row["target_raw"].strip()
        kind = row["kind"]
        source_path = id_to_path.get(row["source_page_id"], "")

        if target_raw == "":
            target_id = row["source_page_id"]
        else:
            target_id = _resolve_via_known_pages(
                target_raw, kind, source_path, wiki_prefix, by_path, by_title, by_alias
            )

        exists = target_id is not None
        if not exists and target_raw:
            exists = _resolve_via_filesystem(paths, source_path, wiki_prefix, target_raw)

        conn.execute(
            "UPDATE links SET target_page_id = ?, exists_flag = ? WHERE id = ?",
            (target_id, 1 if exists else 0, row["id"]),
        )


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def _sync(conn: sqlite3.Connection, paths: ProjectPaths, force: bool, config: Config) -> SyncStats:
    stats = SyncStats()
    files = iter_wiki_files(paths, config)
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

        text = fs_path.read_text(encoding="utf-8")
        if not force and prior is not None:
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if prior[1] == content_hash:
                # mtime moved without the content changing (a `git
                # checkout`/clone resets mtimes but not hashes) — record
                # the new mtime so this short-circuits on mtime alone
                # next time, without reparsing an unchanged page.
                conn.execute("UPDATE pages SET mtime = ? WHERE id = ?", (mtime, prior[0]))
                continue

        try:
            page = parse_page(text, rel_path)
            page.mtime = mtime
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

    _resolve_links(conn, paths)
    _set_meta(conn, "last_indexed", datetime.datetime.now().isoformat(timespec="seconds"))
    conn.commit()
    return stats


_CONTENT_TABLES = ("pages_fts", "pages", "aliases", "tags", "headings", "links", "external_links")


def _clear_content_tables(conn: sqlite3.Connection) -> None:
    """Wipe everything `rebuild` regenerates from wiki/*.md, but never
    `log_entries` — that table is the queryable half of the wiki's
    append-only history and must survive a rebuild, not just wiki/log.md.
    """
    for table in _CONTENT_TABLES:
        conn.execute(f"DELETE FROM {table}")


def rebuild(paths: ProjectPaths) -> SyncStats:
    conn = connect(paths)
    config = load_project_config(paths)
    try:
        _clear_content_tables(conn)
        conn.commit()
        return _sync(conn, paths, force=True, config=config)
    finally:
        conn.close()


def index_changed(paths: ProjectPaths) -> SyncStats:
    conn = connect(paths)
    config = load_project_config(paths)
    try:
        return _sync(conn, paths, force=False, config=config)
    finally:
        conn.close()
