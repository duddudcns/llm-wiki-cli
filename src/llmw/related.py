"""`llmw related` — deterministic related-page candidates (no model calls).

Weights (see skill reference.md / project spec):
    +5 direct link      (this page links to the candidate)
    +4 backlink         (the candidate links to this page)
    +3 per shared tag
    +2 title mention    (either page's title appears in the other's body)
    +1 term overlap     (FTS match on this page's title terms)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llmw.search import build_match_query
from llmw.paths import ProjectPaths
from llmw.queries import IndexNotBuiltError, find_page_row, open_ro

DEFAULT_CATEGORIES = ("links", "tags", "terms")


class PageNotIndexedError(RuntimeError):
    pass


@dataclass
class RelatedResult:
    path: str
    title: str
    score: int
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"path": self.path, "title": self.title, "score": self.score, "reasons": self.reasons}


def related(
    paths: ProjectPaths,
    target: str,
    limit: int = 10,
    by: tuple[str, ...] = DEFAULT_CATEGORIES,
) -> list[RelatedResult]:
    conn = open_ro(paths)
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")

    limit = max(1, limit)

    try:
        page_row = find_page_row(conn, target)
        if page_row is None:
            raise PageNotIndexedError(f'Page not found or not indexed: "{target}"')
        page_id = page_row["id"]

        scores: dict[int, int] = {}
        reasons: dict[int, list[str]] = {}

        def _add(pid: int, points: int, reason: str) -> None:
            if pid == page_id:
                return
            scores[pid] = scores.get(pid, 0) + points
            reasons.setdefault(pid, []).append(reason)

        if "links" in by:
            for row in conn.execute(
                "SELECT DISTINCT target_page_id FROM links "
                "WHERE source_page_id = ? AND target_page_id IS NOT NULL",
                (page_id,),
            ):
                _add(row["target_page_id"], 5, "direct-link")

            for row in conn.execute(
                "SELECT DISTINCT source_page_id FROM links WHERE target_page_id = ?",
                (page_id,),
            ):
                _add(row["source_page_id"], 4, "backlink")

        if "tags" in by:
            for tag_row in conn.execute("SELECT tag FROM tags WHERE page_id = ?", (page_id,)):
                tag = tag_row["tag"]
                for row in conn.execute(
                    "SELECT page_id FROM tags WHERE tag = ? AND page_id != ?",
                    (tag, page_id),
                ):
                    _add(row["page_id"], 3, f"shared-tag:{tag}")

        if "terms" in by:
            title = page_row["title"]
            lowered_title = title.lower()
            for row in conn.execute("SELECT id, title, body FROM pages WHERE id != ?", (page_id,)):
                if lowered_title and lowered_title in (row["body"] or "").lower():
                    _add(row["id"], 2, "title-mention")
                if row["title"] and row["title"].lower() in (page_row["body"] or "").lower():
                    _add(row["id"], 2, "title-mention")

            match_query = build_match_query(title)
            if match_query:
                for row in conn.execute(
                    "SELECT pages_fts.rowid AS id FROM pages_fts "
                    "WHERE pages_fts MATCH ? AND pages_fts.rowid != ?",
                    (match_query, page_id),
                ):
                    _add(row["id"], 1, "term-overlap")

        id_to_page = {
            row["id"]: row
            for row in conn.execute(
                f"SELECT id, path, title FROM pages WHERE id IN "
                f"({','.join('?' * len(scores))})",
                tuple(scores.keys()),
            )
        } if scores else {}

        results = [
            RelatedResult(
                path=id_to_page[pid]["path"],
                title=id_to_page[pid]["title"],
                score=score,
                reasons=reasons[pid],
            )
            for pid, score in scores.items()
        ]
        results.sort(key=lambda r: (-r.score, r.path))
        return results[:limit]
    finally:
        conn.close()
