"""Backups are a safety net with no bottom, so pruning them is delicate.

Every `edit`, `patch`, `archive`, and `write --force` copies the file it
is about to change into `.llmw/backups/<timestamp>/<page path>`, and
nothing ever removed one. Two months of ordinary work on this project's
own wiki left 115 snapshot directories; the bytes are trivial (1.1 MB)
and the unbounded directory count is not.

What a backup here is *for* decides the policy: undoing the mutation you
just made, or recovering a page you broke recently. That is a recency
need — after a month, the wiki log and version control are the record,
and an old snapshot answers a question nobody asks. So this prunes by
age, not by count: a count cap would throw away this morning's snapshots
after a busy afternoon, which is exactly backwards.

Pruning deletes user data, so the tests here are mostly about what it
must *not* remove.
"""

from __future__ import annotations

import datetime
import os
import time
from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.config import Config, save_config
from llmw.paths import ProjectPaths
from llmw.writer import edit_page, write_page

PAGE = (
    "---\ntitle: T\ntype: note\nstatus: active\ncreated: 2026-06-01\n"
    "updated: 2026-06-01\nsummary: s.\n---\n\n# T\n\nBody one.\n"
)


def _project(tmp_path: Path) -> ProjectPaths:
    init_project(tmp_path)
    paths = ProjectPaths.for_project_root(tmp_path)
    write_page(paths, "wiki/decisions/t.md", PAGE, reason="seed")
    return paths


def _snapshot(paths: ProjectPaths, stamp: str, age_days: float) -> Path:
    """A backup directory that looks `age_days` old."""
    snap = paths.backups_dir / stamp / "wiki" / "decisions" / "old.md"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text("archived content\n", encoding="utf-8")
    when = time.time() - age_days * 86400
    os.utime(snap, (when, when))
    os.utime(paths.backups_dir / stamp, (when, when))
    return paths.backups_dir / stamp


def _stamps(paths: ProjectPaths) -> set[str]:
    if not paths.backups_dir.exists():
        return set()
    return {p.name for p in paths.backups_dir.iterdir() if p.is_dir()}


def test_an_old_snapshot_is_removed_by_a_later_write(tmp_path: Path) -> None:
    paths = _project(tmp_path)
    _snapshot(paths, "20250101T000000000000", age_days=400)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert "20250101T000000000000" not in _stamps(paths)


def test_a_recent_snapshot_is_kept(tmp_path: Path) -> None:
    # The whole point of the thing. A snapshot from this week answers the
    # question backups exist for.
    paths = _project(tmp_path)
    _snapshot(paths, "20260101T000000000000", age_days=3)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert "20260101T000000000000" in _stamps(paths)


def test_the_snapshot_this_very_write_just_made_is_kept(tmp_path: Path) -> None:
    # Pruning runs on the same call that writes a backup; taking its own
    # out would make the feature actively harmful.
    paths = _project(tmp_path)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    kept = _stamps(paths)
    assert kept, "the backup this edit made was pruned"
    content = next(paths.backups_dir.rglob("t.md")).read_text(encoding="utf-8")
    assert "Body one." in content, "the kept snapshot is not the pre-edit version"


def test_a_busy_day_never_loses_the_morning(tmp_path: Path) -> None:
    # Why age and not a count cap: fifty edits this afternoon must not
    # evict the snapshot from before lunch, which is the one you want.
    paths = _project(tmp_path)
    for i in range(40):
        _snapshot(paths, f"20260101T0000000{i:05d}", age_days=0.2)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert len(_stamps(paths)) >= 41


def test_retention_can_be_turned_off(tmp_path: Path) -> None:
    # Deleting a safety net has to be opt-out-able by anyone who wants
    # every snapshot kept forever.
    paths = _project(tmp_path)
    save_config(paths.config_path, Config(backup_retention_days=0))
    _snapshot(paths, "20250101T000000000000", age_days=400)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert "20250101T000000000000" in _stamps(paths)


def test_a_custom_retention_window_is_honoured(tmp_path: Path) -> None:
    paths = _project(tmp_path)
    save_config(paths.config_path, Config(backup_retention_days=2))
    _snapshot(paths, "20260101T000000000000", age_days=5)
    _snapshot(paths, "20260102T000000000000", age_days=1)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    kept = _stamps(paths)
    assert "20260101T000000000000" not in kept
    assert "20260102T000000000000" in kept


def test_pruning_never_reaches_outside_the_backups_directory(
    tmp_path: Path,
) -> None:
    # It deletes directory trees, so the blast radius is the assertion
    # that matters most.
    paths = _project(tmp_path)
    _snapshot(paths, "20250101T000000000000", age_days=400)
    old_page = tmp_path / "wiki" / "decisions" / "ancient.md"
    old_page.write_text(PAGE, encoding="utf-8")
    when = time.time() - 400 * 86400
    os.utime(old_page, (when, when))

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert old_page.exists(), "pruning left the backups directory"
    assert (tmp_path / ".llmw" / "index.sqlite").exists()
    assert (tmp_path / "wiki" / "log.md").exists()


def test_a_stray_file_among_the_snapshots_is_left_alone(tmp_path: Path) -> None:
    # Only timestamp directories are ours to remove.
    paths = _project(tmp_path)
    paths.backups_dir.mkdir(parents=True, exist_ok=True)
    stray = paths.backups_dir / "README.txt"
    stray.write_text("do not delete me\n", encoding="utf-8")
    when = time.time() - 400 * 86400
    os.utime(stray, (when, when))

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert stray.exists()


def test_an_unremovable_snapshot_does_not_fail_the_write(tmp_path: Path) -> None:
    # A locked file or a permissions problem in a *backup* must never
    # take down the mutation the user actually asked for.
    from unittest.mock import patch

    paths = _project(tmp_path)
    _snapshot(paths, "20250101T000000000000", age_days=400)

    with patch("shutil.rmtree", side_effect=OSError("in use")):
        edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert (tmp_path / "wiki" / "decisions" / "t.md").read_text(
        encoding="utf-8"
    ).endswith("Body two.\n")


@pytest.mark.parametrize(
    "literal",
    ["-1", '"thirty"', "0.5", "true", "[30]", "1979-05-27"],
)
def test_a_nonsense_retention_value_keeps_everything(
    literal: str, tmp_path: Path
) -> None:
    # Valid TOML, wrong type or wrong range. Misreading this setting must
    # fail toward keeping data, never toward deleting more of it. (A file
    # that isn't TOML at all is a different case — it raises before this
    # setting is ever consulted, and the writer treats that as "keep
    # everything" too.)
    paths = _project(tmp_path)
    paths.config_path.write_text(
        f"[backups]\nretention_days = {literal}\n", encoding="utf-8"
    )
    _snapshot(paths, "20250101T000000000000", age_days=400)

    edit_page(paths, "wiki/decisions/t.md", "Body one.", "Body two.", reason="edit")

    assert "20250101T000000000000" in _stamps(paths)


def test_a_config_that_is_not_toml_at_all_keeps_everything(tmp_path: Path) -> None:
    paths = _project(tmp_path)
    _snapshot(paths, "20250101T000000000000", age_days=400)
    paths.config_path.write_text("this is not toml {{{\n", encoding="utf-8")

    from llmw.writer import _backup

    _backup(paths, tmp_path / "wiki" / "decisions" / "t.md")

    assert "20250101T000000000000" in _stamps(paths)
