from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.indexer import rebuild
from llmw.read import PageNotFoundError, read_page


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_read_by_path(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/foo.md",
        "---\ntitle: Foo\nsummary: A short summary.\n---\n# Foo\n\nbody\n",
    )
    rebuild(paths)

    result = read_page(paths, "wiki/concepts/foo.md")
    assert result.title == "Foo"
    assert result.summary == "A short summary."
    assert result.full_text is None


def test_read_path_traversal_outside_root_is_not_found_not_a_crash(tmp_path: Path):
    # A real file existing just outside the project root used to raise an
    # uncaught ValueError from paths.rel()'s relative_to() instead of the
    # normal PageNotFoundError.
    paths = init_project(tmp_path)
    rebuild(paths)
    outside = tmp_path.parent / "secret.md"
    outside.write_text("top secret\n", encoding="utf-8")

    with pytest.raises(PageNotFoundError):
        read_page(paths, "../secret.md")


def test_read_refuses_files_outside_wiki_but_inside_project_root(tmp_path: Path):
    # A file that exists on disk inside the project root but outside
    # wiki/ (e.g. .env, raw/ originals, pyproject.toml) must not be
    # readable through llmw read / the MCP llmw_read tool as if it were
    # a wiki page.
    paths = init_project(tmp_path)
    rebuild(paths)
    _write(tmp_path, ".env", "SECRET_KEY=topsecret\n")
    _write(tmp_path, "raw/private.md", "raw original, not a wiki page\n")

    with pytest.raises(PageNotFoundError):
        read_page(paths, ".env")
    with pytest.raises(PageNotFoundError):
        read_page(paths, "raw/private.md")


def test_read_non_utf8_page_raises_clear_error_not_a_crash(tmp_path: Path):
    paths = init_project(tmp_path)
    bad = tmp_path / "wiki" / "concepts" / "bad.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes("\xc1\xd1\xb8\xa9".encode("latin-1"))
    rebuild(paths)

    with pytest.raises(PageNotFoundError):
        read_page(paths, "wiki/concepts/bad.md")


def test_read_by_title(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/foo.md", "---\ntitle: Foo Bar\n---\nbody\n")
    rebuild(paths)

    result = read_page(paths, "Foo Bar")
    assert result.path == "wiki/concepts/foo.md"


def test_read_by_alias(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(
        tmp_path,
        "wiki/concepts/foo.md",
        "---\ntitle: Foo\naliases:\n  - FooAlias\n---\nbody\n",
    )
    rebuild(paths)

    result = read_page(paths, "FooAlias")
    assert result.path == "wiki/concepts/foo.md"


def test_read_full_includes_raw_text(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/foo.md", "---\ntitle: Foo\n---\nraw body text\n")
    rebuild(paths)

    result = read_page(paths, "wiki/concepts/foo.md", full=True)
    assert result.full_text is not None
    assert "raw body text" in result.full_text


def test_read_missing_page_raises_with_hint(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    with pytest.raises(PageNotFoundError) as exc_info:
        read_page(paths, "Does Not Exist")
    assert "Does Not Exist" in str(exc_info.value)


def test_read_reports_backlinks_count(tmp_path: Path):
    paths = init_project(tmp_path)
    _write(tmp_path, "wiki/concepts/a.md", "---\ntitle: A\n---\nSee [[B]].\n")
    _write(tmp_path, "wiki/concepts/b.md", "---\ntitle: B\n---\nbody\n")
    rebuild(paths)

    result = read_page(paths, "B")
    assert result.backlinks_count == 1
    assert result.backlink_paths == ["wiki/concepts/a.md"]
