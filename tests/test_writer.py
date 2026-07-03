from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.frontmatter import InvalidFrontmatterError
from llmw.indexer import rebuild
from llmw.patching import PatchApplyError, apply_unified_diff
from llmw.safety import PathNotAllowedError, ReasonRequiredError
from llmw.search import search
from llmw.writer import (
    FileExistsConflictError,
    FileNotFoundForPatchError,
    OldStringNotFoundError,
    OldStringNotUniqueError,
    edit_page,
    patch_page,
    write_page,
)


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


def test_apply_unified_diff_pure_insertion_hunk_mid_file():
    # `git diff -U0` / `difflib.unified_diff(n=0)` style: old_len == 0
    # means "insert after old line 2", not "insert before old line 2".
    original = "line1\nline2\nline3\n"
    diff = "@@ -2,0 +3 @@\n+NEW\n"
    assert apply_unified_diff(original, diff) == "line1\nline2\nNEW\nline3\n"


def test_apply_unified_diff_pure_insertion_hunk_at_start():
    original = "line1\nline2\n"
    diff = "@@ -0,0 +1 @@\n+NEW\n"
    assert apply_unified_diff(original, diff) == "NEW\nline1\nline2\n"


def test_write_rejects_invalid_frontmatter_and_creates_no_file(tmp_path: Path):
    paths = init_project(tmp_path)
    broken = '---\ntitle: Broken\nsummary: "unterminated and: bad\n---\nbody\n'

    with pytest.raises(InvalidFrontmatterError):
        write_page(paths, "wiki/concepts/broken.md", broken, reason="bad frontmatter")

    assert not (paths.root / "wiki/concepts/broken.md").exists()


def test_patch_rejects_result_with_invalid_frontmatter_and_leaves_original(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(
        paths,
        "wiki/concepts/a.md",
        "---\ntitle: A\n---\nbody line\n",
        reason="seed",
    )

    # Patch replaces the frontmatter with something that isn't valid YAML.
    diff = (
        "@@ -1,3 +1,3 @@\n"
        " ---\n"
        '-title: A\n'
        '+title: "unterminated\n'
        " ---\n"
    )
    with pytest.raises(InvalidFrontmatterError):
        patch_page(paths, "wiki/concepts/a.md", diff, reason="break it")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "---\ntitle: A\n---\nbody line\n"
    assert not list(paths.backups_dir.rglob("a.md"))


def test_edit_replaces_unique_occurrence_and_logs(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "---\ntitle: A\n---\nold text here\n", reason="seed")
    rebuild(paths)

    edit_page(paths, "wiki/concepts/a.md", "old text", "new text", reason="fix wording")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "---\ntitle: A\n---\nnew text here\n"
    assert "fix wording" in paths.wiki_log.read_text(encoding="utf-8")
    assert list(paths.backups_dir.rglob("a.md"))
    assert search(paths, "new text").results


def test_edit_old_string_not_found_leaves_file_untouched(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "---\ntitle: A\n---\nbody\n", reason="seed")

    with pytest.raises(OldStringNotFoundError):
        edit_page(paths, "wiki/concepts/a.md", "nonexistent", "x", reason="attempt")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "---\ntitle: A\n---\nbody\n"
    assert not list(paths.backups_dir.rglob("a.md"))


def test_edit_ambiguous_old_string_requires_all(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "---\ntitle: A\n---\nfoo foo foo\n", reason="seed")

    with pytest.raises(OldStringNotUniqueError):
        edit_page(paths, "wiki/concepts/a.md", "foo", "bar", reason="attempt")

    edit_page(paths, "wiki/concepts/a.md", "foo", "bar", reason="replace all", replace_all=True)
    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "---\ntitle: A\n---\nbar bar bar\n"


def test_edit_refuses_raw_path(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(PathNotAllowedError):
        edit_page(paths, "raw/README.md", "a", "b", reason="bad")


def test_edit_requires_reason(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "---\ntitle: A\n---\nbody\n", reason="seed")
    with pytest.raises(ReasonRequiredError):
        edit_page(paths, "wiki/concepts/a.md", "body", "new body", reason="")


def test_edit_requires_existing_file(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(FileNotFoundForPatchError):
        edit_page(paths, "wiki/concepts/nope.md", "a", "b", reason="attempt")


def test_edit_rejects_result_with_invalid_frontmatter_and_leaves_original(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "---\ntitle: A\n---\nbody\n", reason="seed")

    with pytest.raises(InvalidFrontmatterError):
        edit_page(paths, "wiki/concepts/a.md", "title: A", 'title: "unterminated', reason="break it")

    content = (paths.root / "wiki/concepts/a.md").read_text(encoding="utf-8")
    assert content == "---\ntitle: A\n---\nbody\n"
    assert not list(paths.backups_dir.rglob("a.md"))


def test_write_and_patch_never_introduce_crlf(tmp_path: Path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/concepts/a.md", "line1\nline2\nline3\n", reason="seed")
    diff = "@@ -1,3 +1,3 @@\n line1\n-line2\n+line2 changed\n line3\n"
    patch_page(paths, "wiki/concepts/a.md", diff, reason="edit")

    raw = (paths.root / "wiki/concepts/a.md").read_bytes()
    assert b"\r\n" not in raw
