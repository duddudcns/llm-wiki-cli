import datetime
import io

import pytest
from typer.testing import CliRunner

from llmw.archive import archive_page, PageNotFoundForArchiveError
from llmw.bootstrap import init_project
from llmw.cli import app, _read_stdin_content
from llmw.frontmatter import split_frontmatter
from llmw.lint import LintReport, run_lint
from llmw.read import read_page, PageNotFoundError
from llmw.safety import PathNotAllowedError
from llmw.search import search
from llmw.writer import write_page, FileExistsConflictError


def test_pipe_slug_defaults_and_search(tmp_path, monkeypatch):
    paths = init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["write", "wiki/no-extension-test", "--reason", "test"], input="extension validation token\n")
    assert result.exit_code == 0, result.output
    assert "wrote wiki/no-extension-test.md" in result.output
    assert not (paths.wiki / "no-extension-test").exists()
    page = read_page(paths, "no-extension-test", full=True)
    fm, body = split_frontmatter(page.full_text)
    today = datetime.date.today().isoformat()
    assert fm == dict(title="no-extension-test", type="note", status="active", created=today, updated=today)
    assert body == "extension validation token\n"
    assert any(r.path == page.path for r in search(paths, "extension validation token").results)
    assert not run_lint(paths).missing_frontmatter
    with pytest.raises(FileExistsConflictError):
        write_page(paths, "wiki/no-extension-test", "other", reason="test")


@pytest.mark.parametrize("path", ["wiki/bad.txt", "wiki/bad.MD", "wiki", "raw/no-extension", "../escape"])
def test_write_invalid_path_has_example(tmp_path, monkeypatch, path):
    init_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["write", path, "--reason", "test"], input="body")
    assert result.exit_code != 0
    assert 'llmw write --reason "save page" --stdin "wiki/my-page.md"' in result.output


def test_missing_reason_has_complete_example():
    result = CliRunner().invoke(app, ["write", "wiki/x.md"], input="body")
    assert result.exit_code != 0
    assert "--reason" in result.output
    assert 'cat file.md | llmw write' in result.output


def test_interactive_stdin_does_not_block(monkeypatch):
    class Terminal(io.StringIO):
        def isatty(self):
            return True

        def read(self):
            pytest.fail("Must not read an interactive terminal implicitly")

    monkeypatch.setattr("sys.stdin", Terminal())
    import typer
    with pytest.raises(typer.Exit):
        _read_stdin_content(False, auto=True)


def test_force_preserves_created_and_refreshes_updated(tmp_path):
    paths = init_project(tmp_path)
    path = paths.wiki / "old.md"
    path.write_text("---\ncreated: '2001-01-01'\nupdated: '2001-01-01'\n---\nold", encoding="utf-8")
    write_page(paths, "wiki/old", "---\ntitle: Custom\ntype: decision\nstatus: draft\n---\nnew", reason="test", force=True)
    fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["created"] == "2001-01-01"
    assert fm["updated"] == datetime.date.today().isoformat()
    assert (fm["title"], fm["type"], fm["status"], body) == ("Custom", "decision", "draft", "new")
    assert len(list(paths.backups_dir.rglob("old.md"))) == 1


@pytest.mark.parametrize("tombstone", [False, True])
def test_archive_repeated_original_never_duplicates(tmp_path, tombstone):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/old.md", "body", reason="seed")
    dest = archive_page(paths, "wiki/old.md", reason="test", tombstone=tombstone)
    for _ in range(3):
        with pytest.raises((PathNotAllowedError, PageNotFoundForArchiveError)):
            archive_page(paths, "wiki/old.md", reason="again", tombstone=tombstone)
    assert list(paths.wiki_archived.rglob("*.md")) == [dest]
    assert (paths.wiki / "old.md").exists() == tombstone


def test_archive_default_removes_original(tmp_path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/old.md", "body", reason="seed")
    archive_page(paths, "wiki/old.md", reason="test")
    assert not (paths.wiki / "old.md").exists()


def test_read_filename_exact_partial_and_ambiguous_without_index(tmp_path):
    paths = init_project(tmp_path)
    for folder in ("one", "two"):
        parent = paths.wiki / folder
        parent.mkdir()
        (parent / "mlx_prompt_cache.md").write_text("# Other title\nbody", encoding="utf-8")
    for target in ("mlx_prompt_cache", "mlx_prompt_cache.md", "prompt_cache"):
        with pytest.raises(PageNotFoundError) as exc:
            read_page(paths, target)
        assert "wiki/one/mlx_prompt_cache.md" in str(exc.value)
        assert "wiki/two/mlx_prompt_cache.md" in str(exc.value)
    (paths.wiki / "two/mlx_prompt_cache.md").unlink()
    assert read_page(paths, "prompt_cache").path == "wiki/one/mlx_prompt_cache.md"


def test_missing_summary_is_advisory():
    report = LintReport(pages_without_summary=["wiki/a.md"])
    assert report.is_clean()
    assert report.counts()["pages_without_summary"] == 1
    report.broken_links.append({"source": "wiki/a.md"})
    assert not report.is_clean()


def test_read_title_alias_precedence_and_ambiguity(tmp_path):
    paths = init_project(tmp_path)
    write_page(paths, "wiki/target.md", "body", reason="seed")
    write_page(paths, "wiki/other.md", "---\ntitle: target\naliases: [shortcut]\n---\nbody", reason="seed")
    with pytest.raises(PageNotFoundError, match="Ambiguous"):
        read_page(paths, "target")
    assert read_page(paths, "wiki/target.md").path == "wiki/target.md"
    assert read_page(paths, "shortcut").path == "wiki/other.md"


def test_archive_unlink_failure_removes_destination(tmp_path, monkeypatch):
    paths = init_project(tmp_path)
    original = write_page(paths, "wiki/old.md", "body", reason="seed")
    before = original.read_bytes()
    from pathlib import Path
    real_unlink = Path.unlink

    def fail_original(path, *args, **kwargs):
        if path == original:
            raise OSError("cannot remove original")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_original)
    with pytest.raises(OSError, match="cannot remove"):
        archive_page(paths, "wiki/old.md", reason="archive")
    assert original.read_bytes() == before
    assert not list(paths.wiki_archived.rglob("*.md"))
