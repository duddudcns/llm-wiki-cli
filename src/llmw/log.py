"""Append-only history: wiki/log.md (human-readable) + log_entries (queryable)."""

from __future__ import annotations

import datetime

from llmw.paths import ProjectPaths


def append_log(
    paths: ProjectPaths, action: str, path: str | None, reason: str, detail: str = ""
) -> None:
    now = datetime.datetime.now()
    _append_markdown(paths, now, action, path, reason, detail)
    _append_db(paths, now, action, path, reason, detail)


_LOG_TITLE = "llmw Activity Log"


def _seed_frontmatter(now: datetime.datetime) -> str:
    # Under `init --adopt`, bootstrap skips scaffolding wiki/log.md, so this
    # is the first write it ever gets. Without frontmatter here, the title
    # falls back to the filename stem ("log"), which collides with any
    # adopted project's own root-level log.md sharing that name/title.
    # `_LOG_TITLE` is deliberately distinct from a generic "Log" to avoid
    # that collision (see wiki/decisions/ai-wiki-nested-layout.md).
    created = now.date().isoformat()
    return (
        "---\n"
        f"title: {_LOG_TITLE}\n"
        "type: note\n"
        "status: active\n"
        f"created: {created}\n"
        f"updated: {created}\n"
        "summary: Running history of wiki writes, patches, and archives.\n"
        "---\n\n"
        f"# {_LOG_TITLE}\n\n"
        "This file is appended to automatically by `llmw write`, `llmw patch`, and\n"
        "`llmw archive`. Do not hand-edit past entries; add new context in a new\n"
        "entry instead."
    )


def _append_markdown(
    paths: ProjectPaths,
    now: datetime.datetime,
    action: str,
    path: str | None,
    reason: str,
    detail: str,
) -> None:
    paths.wiki_log.parent.mkdir(parents=True, exist_ok=True)
    if paths.wiki_log.exists():
        text = paths.wiki_log.read_text(encoding="utf-8")
    else:
        text = _seed_frontmatter(now)
    text = text.rstrip("\n")

    date_heading = f"## {now.date().isoformat()}"
    heading_lines = [line for line in text.splitlines() if line.startswith("## ")]
    needs_heading = not heading_lines or heading_lines[-1].strip() != date_heading

    entry = [f"- `{action}`: {path or ''}", f"  - reason: {reason}"]
    if detail:
        entry.append(f"  - detail: {detail}")

    parts = [text] if text else []
    if needs_heading:
        parts.append(date_heading)
    parts.append("\n".join(entry))

    paths.wiki_log.write_text("\n\n".join(parts) + "\n", encoding="utf-8", newline="\n")


def _append_db(
    paths: ProjectPaths,
    now: datetime.datetime,
    action: str,
    path: str | None,
    reason: str,
    detail: str,
) -> None:
    from llmw.indexer import connect  # local import: avoid a module-load cycle

    conn = connect(paths)
    try:
        conn.execute(
            "INSERT INTO log_entries(ts, action, path, reason, detail) VALUES (?, ?, ?, ?, ?)",
            (now.isoformat(timespec="seconds"), action, path, reason, detail),
        )
        conn.commit()
    finally:
        conn.close()
