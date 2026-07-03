"""`llmw status` — quick health/summary snapshot of the project."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from llmw.paths import ProjectPaths


@dataclass
class StatusReport:
    wiki_page_count: int
    raw_source_count: int
    indexed_page_count: int | None
    broken_links_count: int | None
    orphan_pages_count: int | None
    dirty_pages_count: int | None
    last_indexed: str | None
    index_exists: bool

    def as_dict(self) -> dict:
        return {
            "wiki_page_count": self.wiki_page_count,
            "raw_source_count": self.raw_source_count,
            "indexed_page_count": self.indexed_page_count,
            "broken_links_count": self.broken_links_count,
            "orphan_pages_count": self.orphan_pages_count,
            "dirty_pages_count": self.dirty_pages_count,
            "last_indexed": self.last_indexed,
            "index_exists": self.index_exists,
        }


def _count_wiki_pages(paths: ProjectPaths) -> int:
    if not paths.wiki.exists():
        return 0
    archived = paths.wiki_archived.resolve()
    return sum(
        1
        for p in paths.wiki.rglob("*.md")
        if not p.resolve().is_relative_to(archived)
    )


def _count_raw_sources(paths: ProjectPaths) -> int:
    if not paths.raw.exists():
        return 0
    return sum(1 for p in paths.raw.rglob("*") if p.is_file() and p.name != "README.md")


def build_status(paths: ProjectPaths) -> StatusReport:
    wiki_page_count = _count_wiki_pages(paths)
    raw_source_count = _count_raw_sources(paths)

    if not paths.index_db.exists():
        return StatusReport(
            wiki_page_count=wiki_page_count,
            raw_source_count=raw_source_count,
            indexed_page_count=None,
            broken_links_count=None,
            orphan_pages_count=None,
            dirty_pages_count=None,
            last_indexed=None,
            index_exists=False,
        )

    conn = sqlite3.connect(paths.index_db)
    try:
        indexed_page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        broken_links_count = conn.execute(
            "SELECT COUNT(*) FROM links WHERE kind != 'external' AND exists_flag = 0"
        ).fetchone()[0]
        orphan_pages_count = conn.execute(
            """
            SELECT COUNT(*) FROM pages p
            WHERE NOT EXISTS (
                SELECT 1 FROM links l
                WHERE l.target_page_id = p.id AND l.source_page_id != p.id
            )
            """
        ).fetchone()[0]
        last_indexed_row = conn.execute(
            "SELECT value FROM meta WHERE key = 'last_indexed'"
        ).fetchone()
        last_indexed = last_indexed_row[0] if last_indexed_row else None

        dirty_pages_count = 0
        for path_str, hash_in_db, mtime_in_db in conn.execute(
            "SELECT path, hash, mtime FROM pages"
        ).fetchall():
            fs_path = paths.root / path_str
            if not fs_path.exists():
                dirty_pages_count += 1
                continue
            if fs_path.stat().st_mtime != mtime_in_db:
                dirty_pages_count += 1
    finally:
        conn.close()

    return StatusReport(
        wiki_page_count=wiki_page_count,
        raw_source_count=raw_source_count,
        indexed_page_count=indexed_page_count,
        broken_links_count=broken_links_count,
        orphan_pages_count=orphan_pages_count,
        dirty_pages_count=dirty_pages_count,
        last_indexed=last_indexed,
        index_exists=True,
    )
