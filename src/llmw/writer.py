"""`llmw write` / `llmw patch` — the only sanctioned way to mutate wiki/*.md.

Both go through the same safety gate: reason required, path confined to
wiki/, backup before overwrite/patch, log entry recorded, index refreshed.
"""

from __future__ import annotations

import datetime
import shutil
from pathlib import Path
from typing import Callable

from llmw.frontmatter import (
    InvalidFrontmatterError,
    missing_fields,
    set_fields,
    split_frontmatter,
)
from llmw.indexer import index_changed, load_project_config
from llmw.locks import acquire_lock
from llmw.log import append_log
from llmw.patching import apply_unified_diff
from llmw.paths import ProjectPaths
from llmw.safety import require_reason, resolve_wiki_target


class FileExistsConflictError(RuntimeError):
    pass


class SupersedeTargetError(ValueError):
    """`--supersedes` named a page that cannot be superseded."""


class FileNotFoundForPatchError(RuntimeError):
    pass


class OldStringNotFoundError(RuntimeError):
    pass


class OldStringNotUniqueError(RuntimeError):
    pass


Notice = Callable[[str], None]


def _required_fields(paths: ProjectPaths) -> list[str]:
    return load_project_config(paths).lint_required_frontmatter


def _notice_incomplete_frontmatter(
    paths: ProjectPaths, rel_path: str, text: str, on_notice: Notice | None
) -> None:
    """Name the required keys a just-written page lacks.

    `llmw lint` has always reported this, but nothing invokes lint, so the
    check existed and never fired — a page with no frontmatter at all sat
    in this repo's own wiki until someone ran it by hand. This is not a
    rejection: plenty of sanctioned writes are not pages at all, and
    refusing an edit to an already-nonconforming page would deadlock it
    against the wiki guard. The agent is still in context and can fix it.
    """
    if on_notice is None:
        return
    try:
        frontmatter, _ = split_frontmatter(text)
    except InvalidFrontmatterError:
        return
    missing = missing_fields(frontmatter, _required_fields(paths))
    if missing:
        on_notice(f"{rel_path}: missing frontmatter {', '.join(missing)}")


def _notice_unbumped_updated(
    rel_path: str, before: str, after: str, on_notice: Notice | None
) -> None:
    """Flag a changed body whose `updated` claim stayed put.

    `updated` is what every freshness display keys on, and it is
    maintained by exactly the convention that produced the staleness
    problem. Deliberately a notice and not an automatic bump: stamping it
    here would make a typo fix look like a re-verification, an error in
    the fresh-ward direction, which is the direction that produces wrong
    judgments.
    """
    if on_notice is None:
        return
    try:
        before_fm, before_body = split_frontmatter(before)
        after_fm, after_body = split_frontmatter(after)
    except InvalidFrontmatterError:
        return
    if before_body == after_body:
        return
    claimed = after_fm.get("updated") or after_fm.get("last_updated")
    if claimed is None or claimed != (
        before_fm.get("updated") or before_fm.get("last_updated")
    ):
        return
    # A page restated today has nothing to restate. Found on this
    # notice's first real use, editing a page written earlier the same
    # session: a notice that fires when no action is available is the
    # kind that teaches the reader to ignore it.
    if str(claimed)[:10] == datetime.date.today().isoformat():
        return
    on_notice(
        f"{rel_path}: body changed, 'updated: {claimed}' not bumped — restate it "
        f"if this page now describes current code"
    )


def _backup(paths: ProjectPaths, fs_path: Path) -> Path:
    paths.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    rel = paths.rel(fs_path)
    backup_path = paths.backups_dir / stamp / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fs_path, backup_path)
    return backup_path


def write_page(
    paths: ProjectPaths,
    rel_path: str,
    content: str,
    reason: str,
    force: bool = False,
    supersedes: str | None = None,
    on_notice: Notice | None = None,
) -> Path:
    """Create a page, or replace one with force=True.

    `supersedes` additionally marks an earlier page as replaced by this
    one, in the same locked transaction: the new page gets `supersedes:`,
    the old gets `status: superseded` and `superseded_by:`. That pairing
    exists as one operation because the reverse pointer is the half that
    gets forgotten when it is left to convention — and a page still
    reading `status: active` weeks after it was overturned is exactly what
    makes a later session trust a reversed decision.
    """
    require_reason(reason)
    fs_path = resolve_wiki_target(paths, rel_path)
    split_frontmatter(content)  # raises InvalidFrontmatterError before touching disk

    superseded_fs: Path | None = None
    if supersedes is not None:
        superseded_fs = resolve_wiki_target(paths, supersedes)
        if superseded_fs == fs_path:
            raise SupersedeTargetError("a page cannot supersede itself")
        content = set_fields(content, {"supersedes": paths.rel(superseded_fs)})

    with acquire_lock(paths, "write"):
        # Both existence checks run before either write: half-applied is
        # the state this command exists to make impossible.
        if superseded_fs is not None and not superseded_fs.is_file():
            raise SupersedeTargetError(
                f"{supersedes} does not exist, so there is nothing to supersede."
            )
        if fs_path.exists() and not force:
            raise FileExistsConflictError(
                f"{rel_path} already exists. Use --force to overwrite."
            )
        if fs_path.exists() and force:
            _backup(paths, fs_path)

        fs_path.parent.mkdir(parents=True, exist_ok=True)
        fs_path.write_text(content, encoding="utf-8", newline="\n")
        append_log(paths, "write", paths.rel(fs_path), reason)
        _notice_incomplete_frontmatter(paths, paths.rel(fs_path), content, on_notice)

        if superseded_fs is not None:
            new_rel = paths.rel(fs_path)
            try:
                # The flip is a mutation like any other: backed up and
                # logged, so it can be undone and audited.
                _backup(paths, superseded_fs)
                superseded_fs.write_text(
                    set_fields(
                        superseded_fs.read_text(encoding="utf-8"),
                        {"status": "superseded", "superseded_by": new_rel},
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
            except OSError:
                # The new page landed but the flip did not — a read-only
                # old page, a permissions change, a full disk. Remove the
                # new page rather than leave it claiming to supersede
                # something nothing marks: that is exactly the
                # half-applied state this command exists to prevent, and
                # `archive.py` rolls its copy back for the same reason.
                fs_path.unlink(missing_ok=True)
                raise
            append_log(
                paths,
                "supersede",
                paths.rel(superseded_fs),
                reason,
                detail=f"superseded by {new_rel}",
            )

        index_changed(paths)

    return fs_path


def edit_page(
    paths: ProjectPaths,
    rel_path: str,
    old_string: str,
    new_string: str,
    reason: str,
    replace_all: bool = False,
    on_notice: Notice | None = None,
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
        _notice_unbumped_updated(paths.rel(fs_path), original, new_content, on_notice)
        _notice_incomplete_frontmatter(paths, paths.rel(fs_path), new_content, on_notice)
        index_changed(paths)

    return fs_path


def patch_page(
    paths: ProjectPaths,
    rel_path: str,
    diff_text: str,
    reason: str,
    on_notice: Notice | None = None,
) -> Path:
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
        _notice_unbumped_updated(paths.rel(fs_path), original, new_content, on_notice)
        _notice_incomplete_frontmatter(paths, paths.rel(fs_path), new_content, on_notice)
        index_changed(paths)

    return fs_path
