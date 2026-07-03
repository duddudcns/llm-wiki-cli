"""`llmw write` / `llmw patch` — the only sanctioned way to mutate wiki/*.md.

Both go through the same safety gate: reason required, path confined to
wiki/, backup before overwrite/patch, log entry recorded, index refreshed.
"""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path

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


def patch_page(paths: ProjectPaths, rel_path: str, diff_text: str, reason: str) -> Path:
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)

    with acquire_lock(paths, "write"):
        if not fs_path.is_file():
            raise FileNotFoundForPatchError(
                f"{rel_path} does not exist; use `llmw write` instead."
            )

        original = fs_path.read_text(encoding="utf-8")
        _backup(paths, fs_path)
        new_content = apply_unified_diff(original, diff_text)

        fs_path.write_text(new_content, encoding="utf-8", newline="\n")
        append_log(paths, "patch", paths.rel(fs_path), reason)
        index_changed(paths)

    return fs_path
