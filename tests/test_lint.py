from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.config import Config, save_config
from llmw.indexer import rebuild
from llmw.lint import run_lint
from llmw.queries import IndexNotBuiltError


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_lint_before_rebuild_raises(tmp_path: Path):
    paths = init_project(tmp_path)
    with pytest.raises(IndexNotBuiltError):
        run_lint(paths)


def test_lint_clean_scaffold_has_no_issues(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    report = run_lint(paths)
    assert report.invalid_frontmatter == []
    assert report.missing_raw_references == []


def test_lint_detects_broken_link(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[Missing]].\n")
    rebuild(paths)

    report = run_lint(paths)
    assert {"source": "wiki/concepts/a.md", "target": "Missing"} in report.broken_links


def test_lint_detects_orphan_page(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/lonely.md", "---\ntitle: Lonely\n---\nno links here\n")
    rebuild(paths)

    report = run_lint(paths)
    assert "wiki/concepts/lonely.md" in report.orphan_pages
    assert "wiki/concepts/lonely.md" in report.isolated_pages


def test_lint_detects_duplicate_titles(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: Same\n---\nbody\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: Same\n---\nbody\n")
    rebuild(paths)

    report = run_lint(paths)
    assert sorted(report.duplicate_titles["same"]) == [
        "wiki/concepts/a.md",
        "wiki/concepts/b.md",
    ]


def test_lint_detects_invalid_frontmatter_without_needing_index(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/bad.md", "---\ntitle: [unterminated\n---\nbody\n")
    rebuild(paths)  # bad.md fails to parse and is skipped by the indexer

    report = run_lint(paths)
    assert any(item["path"] == "wiki/concepts/bad.md" for item in report.invalid_frontmatter)


def test_lint_detects_missing_frontmatter_fields(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/bare.md", "# Bare\n\nno frontmatter at all\n")
    rebuild(paths)

    report = run_lint(paths)
    entry = next(m for m in report.missing_frontmatter if m["path"] == "wiki/concepts/bare.md")
    assert "type" in entry["missing"]


def test_lint_detects_missing_raw_reference(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/sources/foo.md",
        "---\ntitle: Foo\ntype: source\nsource_path: raw/inbox/does-not-exist.md\n---\nbody\n",
    )
    rebuild(paths)

    report = run_lint(paths)
    assert any(
        item["raw_ref"] == "raw/inbox/does-not-exist.md"
        for item in report.missing_raw_references
    )


def test_lint_detects_archived_link_from_active(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[Old]].\n")
    _write(
        tmp_path,
        "wiki/archived/2026/07/old.md",
        "---\ntitle: Old\nstatus: archived\n---\nbody\n",
    )
    rebuild(paths)

    report = run_lint(paths)
    assert {"source": "wiki/concepts/a.md", "target": "wiki/archived/2026/07/old.md"} in (
        report.archived_links_from_active
    )


def test_lint_counts_and_is_clean(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    report = run_lint(paths)
    counts = report.counts()
    assert counts["broken_links"] == 0
    assert report.is_clean() is True


def test_lint_accepts_last_updated_as_updated_synonym(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/a.md",
        "---\ntitle: A\ntype: concept\nstatus: active\ncreated: 2026-07-01\n"
        "last_updated: 2026-07-01\n---\nbody\n",
    )
    rebuild(paths)

    report = run_lint(paths)
    assert not any(m["path"] == "wiki/concepts/a.md" for m in report.missing_frontmatter)


def test_lint_required_frontmatter_is_configurable(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/a.md",
        "---\ntitle: A\ntype: concept\nstatus: active\nimportance: high\n"
        "last_updated: 2026-07-01\n---\nbody\n",
    )
    save_config(
        paths.config_path,
        Config(lint_required_frontmatter=["type", "status"]),
    )
    rebuild(paths)

    report = run_lint(paths)
    assert not any(m["path"] == "wiki/concepts/a.md" for m in report.missing_frontmatter)
