"""`llmw write` / `llmw patch` — the only sanctioned way to mutate wiki/*.md.

Both go through the same safety gate: reason required, path confined to
wiki/, backup before overwrite/patch, log entry recorded, index refreshed.
"""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

from llmw.frontmatter import split_frontmatter
from llmw.indexer import index_changed
from llmw.locks import acquire_lock
from llmw.log import append_log
from llmw.patching import apply_unified_diff
from llmw.paths import ProjectPaths
from llmw.safety import require_reason, resolve_wiki_target


class FileExistsConflictError(RuntimeError):
    pass


class FileNotFoundForPatchError(RuntimeError):
    pass


class OldStringNotFoundError(RuntimeError):
    pass


class OldStringNotUniqueError(RuntimeError):
    pass


def _backup(paths: ProjectPaths, fs_path: Path) -> Path:
    paths.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    rel = paths.rel(fs_path)
    backup_path = paths.backups_dir / stamp / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fs_path, backup_path)
    return backup_path


def write_page(
    paths: ProjectPaths, rel_path: str, content: str, reason: str, force: bool = False
) -> Path:
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)
    split_frontmatter(content)  # raises InvalidFrontmatterError before touching disk

    with acquire_lock(paths, "write"):
        if fs_path.exists() and not force:
            raise FileExistsConflictError(
                f"{rel_path} already exists. Use --force to overwrite."
            )
        if fs_path.exists() and force:
            _backup(paths, fs_path)

        fs_path.parent.mkdir(parents=True, exist_ok=True)
        fs_path.write_text(content, encoding="utf-8", newline="\n")
        append_log(paths, "write", paths.rel(fs_path), reason)
        index_changed(paths)

    return fs_path


def edit_page(
    paths: ProjectPaths,
    rel_path: str,
    old_string: str,
    new_string: str,
    reason: str,
    replace_all: bool = False,
) -> Path:
    """Exact-string replace, mirroring the semantics of a native file-edit
    tool — through the same safety gate as write_page/patch_page. Exists so
    agents have an ergonomic, sanctioned alternative to hand-writing a
    unified diff for a small change."""
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)

    with acquire_lock(paths, "write"):
        if not fs_path.is_file():
            raise FileNotFoundForPatchError(
                f"{rel_path} does not exist; use `llmw write` instead."
            )

        original = fs_path.read_text(encoding="utf-8")
        count = original.count(old_string)
        if count == 0:
            raise OldStringNotFoundError(f"old string not found in {rel_path}")
        if count > 1 and not replace_all:
            raise OldStringNotUniqueError(
                f"old string appears {count} times in {rel_path}; pass --all to replace every occurrence"
            )

        new_content = original.replace(old_string, new_string, -1 if replace_all else 1)
        split_frontmatter(new_content)  # raises InvalidFrontmatterError; original stays untouched

        _backup(paths, fs_path)
        fs_path.write_text(new_content, encoding="utf-8", newline="\n")
        append_log(paths, "edit", paths.rel(fs_path), reason)
        index_changed(paths)

    return fs_path


def patch_page(paths: ProjectPaths, rel_path: str, diff_text: str, reason: str) -> Path:
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)

    with acquire_lock(paths, "write"):
        if not fs_path.is_file():
            raise FileNotFoundForPatchError(
                f"{rel_path} does not exist; use `llmw write` instead."
            )

        original = fs_path.read_text(encoding="utf-8")
        new_content = apply_unified_diff(original, diff_text)
        split_frontmatter(new_content)  # raises InvalidFrontmatterError; original stays untouched

        _backup(paths, fs_path)
        fs_path.write_text(new_content, encoding="utf-8", newline="\n")
        append_log(paths, "patch", paths.rel(fs_path), reason)
        index_changed(paths)

    return fs_path
