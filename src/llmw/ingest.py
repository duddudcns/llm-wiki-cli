"""`llmw ingest` — register a raw/ source as a wiki/sources/<slug>.md draft.

No summarization happens here (no model calls) — this only computes a
hash, writes a placeholder draft, and leaves "TODO" markers for the AI
agent to fill in later via `llmw patch`.
"""

from __future__ import annotations

import datetime
import hashlib
import re
from pathlib import Path

from llmw.paths import ProjectPaths
from llmw.writer import FileExistsConflictError, write_page

SUPPORTED_SUFFIXES = {".md", ".txt"}
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9-]")


class SourceNotFoundError(RuntimeError):
    pass


class SourceNotInRawError(RuntimeError):
    pass


class UnsupportedSourceTypeError(RuntimeError):
    pass


class SourceAlreadyIngestedError(RuntimeError):
    pass


def _slugify(stem: str) -> str:
    s = stem.strip().lower().replace("_", "-").replace(" ", "-")
    s = _SLUG_STRIP_RE.sub("", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "source"


def ingest_source(paths: ProjectPaths, source_path: str) -> Path:
    normalized = source_path.replace("\\", "/")
    fs_source = (paths.root / normalized).resolve()

    if not fs_source.is_file():
        raise SourceNotFoundError(f"{source_path} does not exist.")

    try:
        fs_source.relative_to(paths.raw.resolve())
    except ValueError as exc:
        raise SourceNotInRawError(f"{source_path} is not under raw/.") from exc

    if fs_source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise UnsupportedSourceTypeError(
            f"{source_path}: unsupported source type {fs_source.suffix!r}; "
            "convert to .md or .txt first (MVP only supports these)."
        )

    source_hash = hashlib.sha256(fs_source.read_bytes()).hexdigest()
    now = datetime.datetime.now()
    rel_source = paths.rel(fs_source)
    dest_rel = f"wiki/sources/{_slugify(fs_source.stem)}.md"

    draft = (
        "---\n"
        f"title: Source - {fs_source.stem}\n"
        "type: source\n"
        "status: draft\n"
        f"source_path: {rel_source}\n"
        f"source_hash: {source_hash}\n"
        f"created: {now.date().isoformat()}\n"
        f"updated: {now.date().isoformat()}\n"
        "tags:\n"
        "  - source\n"
        "---\n\n"
        f"# Source - {fs_source.stem}\n\n"
        "## Source metadata\n\n"
        f"- Path: `{rel_source}`\n"
        f"- Hash: `{source_hash}`\n\n"
        "## Agent summary\n\n"
        "TODO: The agent should read the source and summarize it.\n\n"
        "## Extracted concepts\n\n"
        "TODO\n\n"
        "## Related pages\n\n"
        "TODO\n"
    )

    try:
        return write_page(paths, dest_rel, draft, reason=f"ingest {rel_source}")
    except FileExistsConflictError as exc:
        raise SourceAlreadyIngestedError(
            f"{dest_rel} already exists (already ingested?). Use `llmw patch` to update it."
        ) from exc
