"""`llmw search` — SQLite FTS5 keyword search over title/summary/body."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from llmw.paths import ProjectPaths
from llmw.queries import IndexNotBuiltError, open_ro, outgoing_links, page_tags

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

__all__ = ["IndexNotBuiltError", "SearchResult", "build_match_query", "search"]


@dataclass
class SearchResult:
    path: str
    title: str
    type: str | None
    status: str | None
    score: float
    summary: str | None
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "type": self.type,
            "status": self.status,
            "score": self.score,
            "summary": self.summary,
            "tags": self.tags,
            "links": self.links,
        }


def build_match_query(query: str) -> str | None:
    tokens = _TOKEN_RE.findall(query)
    if not tokens:
        return None
    return " ".join(f'{tok}*' for tok in tokens)


def search(
    paths: ProjectPaths,
    query: str,
    limit: int = 5,
    type_filter: str | None = None,
) -> list[SearchResult]:
    conn = open_ro(paths)
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")

    try:
        match_query = build_match_query(query)
        if match_query is None:
            return []

        sql = (
            "SELECT p.id, p.path, p.title, p.type, p.status, p.summary, "
            "bm25(pages_fts) AS rank "
            "FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid "
            "WHERE pages_fts MATCH ?"
        )
        params: list = [match_query]
        if type_filter:
            sql += " AND p.type = ?"
            params.append(type_filter)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        results = []
        for row in conn.execute(sql, params).fetchall():
            links = outgoing_links(conn, row["id"])
            link_titles = [
                (l["target_title"] or l["target_raw"]) for l in links if l["target_raw"]
            ]
            results.append(
                SearchResult(
                    path=row["path"],
                    title=row["title"],
                    type=row["type"],
                    status=row["status"],
                    score=round(-row["rank"], 4),
                    summary=row["summary"],
                    tags=page_tags(conn, row["id"]),
                    links=link_titles,
                )
            )
        return results
    finally:
        conn.close()
