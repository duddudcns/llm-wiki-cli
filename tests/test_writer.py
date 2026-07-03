from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.patching import PatchApplyError, apply_unified_diff
from llmw.safety import PathNotAllowedError, ReasonRequiredError
from llmw.writer import FileExistsConflictError, FileNotFoundForPatchError, patch_page, write_page


def test_write_requires_reason(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(ReasonRequiredError):
        write_page(paths, "wiki/concepts/new.md", "content\n", reason="")


def test_write_refuses_raw_path(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(PathNotAllowedError):
        write_page(paths, "raw/test.md", "content\n", reason="bad")


def test_write_refuses_path_outside_project(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(PathNotAllowedError):
        write_page(paths, "../outside.md", "content\n", reason="bad")


def test_write_creates_new_page_and_updates_index(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)

    fs_path = write_page(
        paths, "wiki/concepts/new.md", "---\ntitle: New\n---\nbody\n", reason="added new concept"
    )
    assert fs_path.is_file()
    assert "duddudcnsgns" not in paths.wiki_log.read_text(encoding="utf-8")  # sanity: no secrets
    assert "added new concept" in paths.wiki_log.read_text(encoding="utf-8")


def test_write_existing_file_without_force_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(FileExistsConflictError):
        write_page(paths, "wiki/index.md", "overwritten\n", reason="oops")


def test_write_existing_file_with_force_backs_up_and_overwrites(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/index.md", "overwritten\n", reason="force overwrite", force=True)
    assert (paths.root / "wiki/index.md").read_text(encoding="utf-8") == "overwritten\n"
    backups = list(paths.backups_dir.rglob("index.md"))
    assert len(backups) == 1


def test_patch_requires_existing_file(tmp_path: Path):
    paths = init_project(tmp_path)
    diff = "@@ -1,1 +1,1 @@\n-old\n+new\n"
    with pytest.raises(FileNotFoundForPatchError):
        patch_page(paths, "wiki/concepts/nope.md", diff, reason="x")


def test_patch_applies_and_backs_up(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "line1\nline2\nline3\n", reason="seed")

    diff = "@@ -1,3 +1,3 @@\n line1\n-line2\n+line2 changed\n line3\n"
    patch_page(paths, "wiki/concepts/a.md", diff, reason="update line2")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "line1\nline2 changed\nline3\n"
    assert list(paths.backups_dir.rglob("a.md"))


def test_patch_context_mismatch_leaves_file_untouched(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "line1\nline2\nline3\n", reason="seed")

    bad_diff = "@@ -1,3 +1,3 @@\n line1\n-WRONG CONTEXT\n+line2 changed\n line3\n"
    with pytest.raises(PatchApplyError):
        patch_page(paths, "wiki/concepts/a.md", bad_diff, reason="update line2")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "line1\nline2\nline3\n"


def test_apply_unified_diff_basic():
    original = "a\nb\nc\n"
    diff = "@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n"
    assert apply_unified_diff(original, diff) == "a\nB\nc\n"


def test_apply_unified_diff_insert_lines():
    original = "a\nc\n"
    diff = "@@ -1,2 +1,3 @@\n a\n+b\n c\n"
    assert apply_unified_diff(original, diff) == "a\nb\nc\n"


def test_write_and_patch_never_introduce_crlf(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "line1\nline2\nline3\n", reason="seed")
    diff = "@@ -1,3 +1,3 @@\n line1\n-line2\n+line2 changed\n line3\n"
    patch_page(paths, "wiki/concepts/a.md", diff, reason="edit")

    raw = (paths.root / "wiki/concepts/a.md").read_bytes()
    assert b"\r\n" not in raw
