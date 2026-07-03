"""Shared guardrails for anything that mutates wiki/*.md.

`raw/` is immutable; every mutation needs a `--reason`; paths may never
escape the project root. Both `writer.py` and `archive.py` build on this.
"""

from __future__ import annotations

from pathlib import Path

from llmw.paths import ProjectPaths


class PathNotAllowedError(RuntimeError):
    pass


class ReasonRequiredError(RuntimeError):
    pass


def require_reason(reason: str) -> None:
    if not reason or not reason.strip():
        raise ReasonRequiredError("A --reason is required for this operation.")


def resolve_wiki_target(paths: ProjectPaths, rel_path: str) -> Path:
    """Validate `rel_path` resolves inside wiki/ (never raw/, never outside
    the project root, no `..` escapes). Returns the absolute filesystem Path.
    """
    normalized = rel_path.replace("\\", "/").lstrip("/")
    candidate = (paths.root / normalized).resolve()

    root_resolved = paths.root.resolve()
    wiki_resolved = paths.wiki.resolve()
    raw_resolved = paths.raw.resolve()

    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise PathNotAllowedError(f"Path escapes the project root: {rel_path}") from exc

    if candidate.is_relative_to(raw_resolved):
        raise PathNotAllowedError(f"raw/ is immutable; refusing to write {rel_path}")
    if not candidate.is_relative_to(wiki_resolved):
        raise PathNotAllowedError(f"Writes are only allowed under wiki/: {rel_path}")

    return candidate
