"""`llmw lint` — deterministic wiki health checks. Reports only; never
auto-fixes (that is left to the AI agent via `write`/`patch`/`archive`).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from llmw.frontmatter import InvalidFrontmatterError, split_frontmatter
from llmw.indexer import iter_wiki_files
from llmw.paths import ProjectPaths
from llmw.queries import IndexNotBuiltError, open_ro

REQUIRED_FRONTMATTER_FIELDS = ("type", "status", "created", "updated")


@dataclass
class LintReport:
    broken_links: list[dict] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)
    isolated_pages: list[str] = field(default_factory=list)
    duplicate_titles: dict = field(default_factory=dict)
    duplicate_aliases: dict = field(default_factory=dict)
    missing_frontmatter: list[dict] = field(default_factory=list)
    invalid_frontmatter: list[dict] = field(default_factory=list)
    pages_without_summary: list[str] = field(default_factory=list)
    pages_without_type: list[str] = field(default_factory=list)
    missing_raw_references: list[dict] = field(default_factory=list)
    archived_links_from_active: list[dict] = field(default_factory=list)

    def counts(self) -> dict:
        return {
            "broken_links": len(self.broken_links),
            "orphan_pages": len(self.orphan_pages),
            "isolated_pages": len(self.isolated_pages),
            "duplicate_titles": len(self.duplicate_titles),
            "duplicate_aliases": len(self.duplicate_aliases),
            "missing_frontmatter": len(self.missing_frontmatter),
            "invalid_frontmatter": len(self.invalid_frontmatter),
            "pages_without_summary": len(self.pages_without_summary),
            "pages_without_type": len(self.pages_without_type),
            "missing_raw_references": len(self.missing_raw_references),
            "archived_links_from_active": len(self.archived_links_from_active),
        }

    def is_clean(self) -> bool:
        return all(v == 0 for v in self.counts().values())

    def as_dict(self) -> dict:
        return {
            "broken_links": self.broken_links,
            "orphan_pages": self.orphan_pages,
            "isolated_pages": self.isolated_pages,
            "duplicate_titles": self.duplicate_titles,
            "duplicate_aliases": self.duplicate_aliases,
            "missing_frontmatter": self.missing_frontmatter,
            "invalid_frontmatter": self.invalid_frontmatter,
            "pages_without_summary": self.pages_without_summary,
            "pages_without_type": self.pages_without_type,
            "missing_raw_references": self.missing_raw_references,
            "archived_links_from_active": self.archived_links_from_active,
        }


def _iter_raw_path_strings(value, out: list[str]) -> None:
    if isinstance(value, str):
        if value.startswith("raw/") or value.startswith("raw\\"):
            out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            _iter_raw_path_strings(v, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _iter_raw_path_strings(v, out)


def _lint_frontmatter(paths: ProjectPaths, report: LintReport) -> None:
    """Fresh on-disk pass: YAML validity, required fields, dangling raw refs.

    Independent of the SQLite index so it stays correct even for files that
    failed to index at all (invalid frontmatter).
    """
    for fs_path in iter_wiki_files(paths):
        rel_path = paths.rel(fs_path)
        text = fs_path.read_text(encoding="utf-8")
        try:
            frontmatter, _body = split_frontmatter(text)
        except InvalidFrontmatterError as exc:
            report.invalid_frontmatter.append({"path": rel_path, "error": str(exc)})
            continue

        missing = [f for f in REQUIRED_FRONTMATTER_FIELDS if not frontmatter.get(f)]
        if missing:
            report.missing_frontmatter.append({"path": rel_path, "missing": missing})

        raw_refs: list[str] = []
        _iter_raw_path_strings(frontmatter, raw_refs)
        for ref in raw_refs:
            if not (paths.root / ref).exists():
                report.missing_raw_references.append({"path": rel_path, "raw_ref": ref})


def run_lint(paths: ProjectPaths) -> LintReport:
    report = LintReport()
    _lint_frontmatter(paths, report)

    conn = open_ro(paths)
    if conn is None:
        raise IndexNotBuiltError("Index not built yet. Run `llmw rebuild` first.")

    try:
        for row in conn.execute(
            """
            SELECT sp.path AS source, l.target_raw AS target
            FROM links l JOIN pages sp ON sp.id = l.source_page_id
            WHERE l.exists_flag = 0 AND l.target_raw != ''
            """
        ):
            report.broken_links.append({"source": row["source"], "target": row["target"]})

        for row in conn.execute(
            """
            SELECT path FROM pages p
            WHERE NOT EXISTS (
                SELECT 1 FROM links l
                WHERE l.target_page_id = p.id AND l.source_page_id != p.id
            )
            """
        ):
            report.orphan_pages.append(row["path"])

        for row in conn.execute(
            """
            SELECT path FROM pages p
            WHERE NOT EXISTS (
                SELECT 1 FROM links l
                WHERE l.target_page_id = p.id AND l.source_page_id != p.id
            )
            AND NOT EXISTS (
                SELECT 1 FROM links l2
                WHERE l2.source_page_id = p.id AND l2.target_page_id IS NOT NULL
                      AND l2.target_page_id != p.id
            )
            """
        ):
            report.isolated_pages.append(row["path"])

        title_groups: dict[str, list[str]] = defaultdict(list)
        for row in conn.execute("SELECT path, title FROM pages"):
            title_groups[row["title"].lower()].append(row["path"])
        report.duplicate_titles = {
            title: paths_ for title, paths_ in title_groups.items() if len(paths_) > 1
        }

        alias_groups: dict[str, list[str]] = defaultdict(list)
        for row in conn.execute(
            "SELECT a.alias AS alias, p.path AS path FROM aliases a JOIN pages p ON p.id = a.page_id"
        ):
            alias_groups[row["alias"].lower()].append(row["path"])
        report.duplicate_aliases = {
            alias: paths_ for alias, paths_ in alias_groups.items() if len(paths_) > 1
        }

        for row in conn.execute("SELECT path FROM pages WHERE summary IS NULL"):
            report.pages_without_summary.append(row["path"])
        for row in conn.execute("SELECT path FROM pages WHERE type IS NULL"):
            report.pages_without_type.append(row["path"])

        for row in conn.execute(
            """
            SELECT sp.path AS source, tp.path AS target
            FROM links l
            JOIN pages sp ON sp.id = l.source_page_id
            JOIN pages tp ON tp.id = l.target_page_id
            WHERE tp.path LIKE 'wiki/archived/%' AND sp.path NOT LIKE 'wiki/archived/%'
            """
        ):
            report.archived_links_from_active.append(
                {"source": row["source"], "target": row["target"]}
            )
    finally:
        conn.close()

    return report
