"""`llmw search` — SQLite FTS5 keyword search over title/summary/body.

Search runs in up to three tiers, only escalating to the next when the
previous one returns nothing — so a full match can never be outranked by a
partial one:

1. ``strict``  — AND of every (particle-stemmed) query term.
2. ``relaxed`` — AND of only the terms that match at least one page in the
   index; terms that can't possibly match anything (typos, verb
   conjugations `llmw` doesn't stem) are dropped instead of failing the
   whole query.
3. ``any``     — OR of all terms, bm25-ranked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from llmw.korean import strip_josa
from llmw.paths import ProjectPaths
from llmw.queries import IndexNotBuiltError, open_ro, outgoing_links, page_tags

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

# A natural-language sentence query can tokenize into a dozen+ words; cap it
# so a long query still runs a handful of tiny FTS5 probes, not dozens.
MAX_QUERY_TOKENS = 12

# pages_fts column order is (title, summary, body, path UNINDEXED) — a title
# hit is a much stronger signal than one incidental body mention, so it
# outweighs bm25's default of treating every column equally.
_RANK_SQL = "bm25(pages_fts, 5.0, 3.0, 1.0)"

__all__ = [
    "IndexNotBuiltError",
    "SearchResult",
    "SearchResponse",
    "build_match_query",
    "search",
]


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


@dataclass
class SearchResponse:
    results: list[SearchResult]
    mode: str = "strict"
    dropped_tokens: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "dropped_tokens": self.dropped_tokens,
            "results": [r.as_dict() for r in self.results],
        }


def _extract_terms(query: str) -> list[str]:
    tokens = _TOKEN_RE.findall(query)[:MAX_QUERY_TOKENS]
    terms: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        stem = strip_josa(tok) or tok
        if stem not in seen:
            seen.add(stem)
            terms.append(stem)
    return terms


def _fts5_prefix_term(term: str) -> str:
    """Render a term as an FTS5 string-literal prefix query.

    Quoting is required, not cosmetic: an unquoted bare term that happens to
    collide with an FTS5 operator keyword (AND, OR, NOT, NEAR — case
    sensitive) raises `sqlite3.OperationalError: fts5: syntax error`
    instead of matching literally. A query like "find AND fix", or a page
    *title* containing one of those words (reached via `related()`), would
    otherwise crash the search/related commands and the MCP search tool.
    """
    escaped = term.replace('"', '""')
    return f'"{escaped}"*'


def build_match_query(query: str) -> str | None:
    terms = _extract_terms(query)
    if not terms:
        return None
    return " ".join(_fts5_prefix_term(t) for t in terms)


def _rows_for(conn, match_query: str, type_filter: str | None, limit: int):
    sql = (
        "SELECT p.id, p.path, p.title, p.type, p.status, p.summary, "
        f"{_RANK_SQL} AS rank "
        "FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid "
        "WHERE pages_fts MATCH ?"
    )
    params: list = [match_query]
    if type_filter:
        sql += " AND p.type = ?"
        params.append(type_filter)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def _term_matches_any_page(conn, term: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM pages_fts WHERE pages_fts MATCH ? LIMIT 1",
        (_fts5_prefix_term(term),),
    ).fetchone()
    return row is not None


def _rows_to_results(conn, rows) -> list[SearchResult]:
    results = []
    for row in rows:
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


def search(
    paths: ProjectPaths,
    query: str,
    limit: int = 5,
    type_filter: str | None = None,
    strict: bool = False,
) -> SearchResponse:
    conn = open_ro(paths)
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")

    try:
        terms = _extract_terms(query)
        if not terms:
            return SearchResponse(results=[], mode="strict")

        and_query = " ".join(_fts5_prefix_term(t) for t in terms)
        rows = _rows_for(conn, and_query, type_filter, limit)
        mode = "strict"
        dropped: list[str] = []

        if not rows and not strict:
            survivors = [t for t in terms if _term_matches_any_page(conn, t)]
            if survivors and len(survivors) < len(terms):
                relaxed_query = " ".join(_fts5_prefix_term(t) for t in survivors)
                relaxed_rows = _rows_for(conn, relaxed_query, type_filter, limit)
                if relaxed_rows:
                    rows = relaxed_rows
                    mode = "relaxed"
                    dropped = [t for t in terms if t not in survivors]

        if not rows and not strict:
            or_query = " OR ".join(_fts5_prefix_term(t) for t in terms)
            or_rows = _rows_for(conn, or_query, type_filter, limit)
            if or_rows:
                rows = or_rows
                mode = "any"
                dropped = []

        return SearchResponse(
            results=_rows_to_results(conn, rows), mode=mode, dropped_tokens=dropped
        )
    finally:
        conn.close()
