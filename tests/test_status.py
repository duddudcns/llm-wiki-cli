from pathlib import Path

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.lint import run_lint
from llmw.status import build_status


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_orphan_pages_count_matches_lint_orphan_definition(tmp_path: Path):
    """A page with only outgoing links (nobody links back to it) is an
    orphan, not an isolated page — status and lint must agree on that.
    """
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/isolated.md",
        "---\ntitle: Isolated\n---\nNo links in or out.\n",
    )
    _write(
        tmp_path,
        "wiki/concepts/outgoing-only.md",
        "---\ntitle: Outgoing Only\n---\nLinks to [[Linked Target]] but nothing links back to this page.\n",
    )
    _write(
        tmp_path,
        "wiki/concepts/linked-target.md",
        "---\ntitle: Linked Target\n---\nReferenced by Outgoing Only.\n",
    )
    rebuild(paths)

    status = build_status(paths)
    lint_report = run_lint(paths)

    assert status.orphan_pages_count == len(lint_report.orphan_pages)
    assert set(lint_report.orphan_pages) == {
        "wiki/concepts/isolated.md",
        "wiki/concepts/outgoing-only.md",
    }


def test_orphan_pages_count_zero_when_all_pages_are_linked(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[B]].\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\n---\nSee [[A]].\n")
    rebuild(paths)

    status = build_status(paths)
    assert status.orphan_pages_count == 0
