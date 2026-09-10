"""`llmw archive` — move a page to wiki/archived/YYYY/MM/, never delete."""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml

from llmw.config import load_config
from llmw.frontmatter import InvalidFrontmatterError, set_fields, split_frontmatter
from llmw.indexer import index_changed
from llmw.locks import acquire_lock
from llmw.log import append_log
from llmw.paths import ProjectPaths
from llmw.safety import PathNotAllowedError, require_reason, resolve_wiki_target


class PageNotFoundForArchiveError(RuntimeError):
    pass


def _dump_frontmatter_block(frontmatter: dict) -> str:
    return yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()


def _stamp_archive_frontmatter(text: str, reason: str, archived_at: str) -> str:
    # Through `set_fields` rather than a second copy of the same
    # dump-and-splice: that is the one place that knows how to split a
    # frontmatter block whose YAML doesn't parse. Done by hand here, the
    # unreadable block was re-emitted below the new one and left the page
    # carrying two — silently, on a page being retired.
    return set_fields(
        text,
        {
            "status": "archived",
            "archived": True,
            "archived_at": archived_at,
            "archive_reason": reason,
        },
    )


def _unique_destination(dest_dir: Path, name: str) -> Path:
    candidate = dest_dir / name
    if not candidate.exists():
        return candidate
    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def archive_page(
    paths: ProjectPaths, rel_path: str, reason: str, tombstone: bool | None = None
) -> Path:
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)

    if not fs_path.is_file():
        raise PageNotFoundForArchiveError(f"{rel_path} does not exist.")

    if fs_path.resolve().is_relative_to(paths.wiki_archived.resolve()):
        raise PathNotAllowedError(f"{rel_path} is already archived.")

    if tombstone is None:
        tombstone = (
            load_config(paths.config_path).archive_tombstone
            if paths.config_path.exists()
            else False
        )

    now = datetime.datetime.now()
    dest_dir = paths.wiki_archived / f"{now.year:04d}" / f"{now.month:02d}"

    with acquire_lock(paths, "write"):
        if not fs_path.is_file():
            raise PageNotFoundForArchiveError(f"{rel_path} does not exist.")
        original_text = fs_path.read_text(encoding="utf-8")
        try:
            frontmatter, _ = split_frontmatter(original_text)
        except InvalidFrontmatterError:
            frontmatter = {}
        if (
            frontmatter.get("status") == "archived"
            or frontmatter.get("archived") is True
            or frontmatter.get("moved_to")
        ):
            raise PathNotAllowedError(f"{rel_path} is already archived.")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = _unique_destination(dest_dir, fs_path.name)

        stamped = _stamp_archive_frontmatter(
            original_text, reason, now.isoformat(timespec="seconds")
        )
        dest_path.write_text(stamped, encoding="utf-8", newline="\n")

        try:
            if tombstone:
                rel_dest = paths.rel(dest_path)
                stub_frontmatter = {
                    "title": fs_path.stem,
                    "status": "archived",
                    "moved_to": rel_dest,
                    "archived_at": now.isoformat(timespec="seconds"),
                }
                yaml_block = _dump_frontmatter_block(stub_frontmatter)
                stub = f"---\n{yaml_block}\n---\n\nThis page was archived. See `{rel_dest}`.\n"
                fs_path.write_text(stub, encoding="utf-8", newline="\n")
            else:
                fs_path.unlink()
        except OSError:
            # The copy at dest_path landed but the original-side mutation
            # didn't — roll the copy back so the original page is left
            # exactly as it was, and a retry doesn't create yet another
            # uniquely-suffixed duplicate copy in wiki/archived/.
            dest_path.unlink(missing_ok=True)
            raise

        append_log(
            paths, "archive", paths.rel(dest_path), reason, detail=f"from {rel_path}"
        )
        index_changed(paths)

    return dest_path
