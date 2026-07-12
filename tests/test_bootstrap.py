import sqlite3
from pathlib import Path

import pytest

from llmw.bootstrap import ProjectAlreadyExistsError, UnknownLayoutError, init_project
from llmw.config import Config, load_config, save_config
from llmw.indexer import rebuild
from llmw.status import build_status


def test_init_creates_expected_structure(tmp_path: Path) -> None:
    paths = init_project(tmp_path)

    assert paths.raw.is_dir()
    assert paths.wiki.is_dir()
    assert paths.llmw_dir.is_dir()
    assert (paths.wiki / "index.md").is_file()
    assert (paths.wiki / "overview.md").is_file()
    assert paths.wiki_log.is_file()
    assert paths.config_path.is_file()
    assert (paths.claude_skill_dir / "SKILL.md").is_file()
    assert (paths.claude_skill_dir / "reference.md").is_file()
    assert (paths.claude_skill_dir / "examples.md").is_file()
    assert (paths.claude_plugin_dir / "plugin.json").is_file()
    assert (paths.claude_rules_dir / "llm-wiki.md").is_file()


def test_init_no_claude_plugin_skips_skill_and_plugin_scaffold(tmp_path: Path) -> None:
    paths = init_project(tmp_path, claude_plugin=False)

    assert not paths.claude_skill_dir.exists()
    assert not paths.claude_plugin_dir.exists()
    # The actual wiki scaffold must still be created.
    assert paths.raw.is_dir()
    assert paths.wiki.is_dir()
    assert paths.llmw_dir.is_dir()
    assert (paths.wiki / "index.md").is_file()
    # Unlike the skill/plugin.json copies, the rules file has no
    # marketplace-plugin equivalent to deduplicate against — a Claude Code
    # plugin manifest cannot ship `.claude/rules/` content at all — so it's
    # always created regardless of `claude_plugin`.
    assert (paths.claude_rules_dir / "llm-wiki.md").is_file()


def test_init_rules_file_mentions_search_and_wiki_path(tmp_path: Path) -> None:
    paths = init_project(tmp_path)

    content = (paths.claude_rules_dir / "llm-wiki.md").read_text(encoding="utf-8")
    assert "llmw search" in content
    assert "llmw write" in content
    assert "wiki/" in content
    # No `paths:` frontmatter — must load unconditionally every session,
    # not only when Claude happens to touch a matching file.
    assert not content.startswith("---")


def test_init_ai_wiki_layout_rules_file_points_at_nested_wiki(tmp_path: Path) -> None:
    paths = init_project(tmp_path, layout="ai-wiki")

    content = (paths.claude_rules_dir / "llm-wiki.md").read_text(encoding="utf-8")
    assert "ai-wiki/wiki/" in content
    # .claude/ (and therefore rules/) stays at the real project root.
    assert paths.claude_rules_dir == tmp_path.resolve() / ".claude" / "rules"


def test_init_adopt_still_creates_rules_file(tmp_path: Path) -> None:
    paths = init_project(tmp_path, adopt=True)

    assert (paths.claude_rules_dir / "llm-wiki.md").is_file()


def test_init_force_refreshes_rules_file(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    rules_file = paths.claude_rules_dir / "llm-wiki.md"
    rules_file.write_text("hand-edited\n", encoding="utf-8")

    init_project(tmp_path, force=True)

    assert "llmw search" in rules_file.read_text(encoding="utf-8")


def test_init_twice_without_force_raises(tmp_path: Path) -> None:
    init_project(tmp_path)
    with pytest.raises(ProjectAlreadyExistsError):
        init_project(tmp_path)


def test_init_twice_with_force_succeeds(tmp_path: Path) -> None:
    init_project(tmp_path)
    init_project(tmp_path, force=True)


def test_status_before_rebuild_reports_no_index(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    report = build_status(paths)

    assert report.index_exists is False
    assert report.wiki_page_count == 3
    assert report.raw_source_count == 0


def test_default_scaffolded_pages_have_no_broken_links(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    rebuild(paths)

    conn = sqlite3.connect(paths.index_db)
    try:
        broken = conn.execute(
            "SELECT target_raw FROM links WHERE exists_flag = 0"
        ).fetchall()
    finally:
        conn.close()
    assert broken == []


def test_init_writes_lf_only_even_on_windows(tmp_path: Path) -> None:
    paths = init_project(tmp_path)
    for fs_path in paths.wiki.rglob("*.md"):
        raw = fs_path.read_bytes()
        assert b"\r\n" not in raw, f"{fs_path} contains CRLF"
    assert b"\r\n" not in paths.config_path.read_bytes()
    assert b"\r\n" not in (paths.claude_skill_dir / "SKILL.md").read_bytes()
    assert b"\r\n" not in (paths.claude_rules_dir / "llm-wiki.md").read_bytes()


def test_init_ai_wiki_layout_nests_wiki_data_under_ai_wiki(tmp_path: Path) -> None:
    paths = init_project(tmp_path, layout="ai-wiki")

    assert paths.project_root == tmp_path.resolve()
    assert paths.root == tmp_path.resolve() / "ai-wiki"
    assert paths.raw.is_dir()
    assert paths.wiki.is_dir()
    assert paths.llmw_dir.is_dir()
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "wiki").exists()
    assert not (tmp_path / ".llmw").exists()

    # .claude/ stays at the real project root, never nested under ai-wiki/.
    assert paths.claude_skill_dir == tmp_path.resolve() / ".claude" / "skills" / "llm-wiki"
    assert (paths.claude_skill_dir / "SKILL.md").is_file()
    assert not (tmp_path / "ai-wiki" / ".claude").exists()


def test_init_unknown_layout_raises(tmp_path: Path) -> None:
    with pytest.raises(UnknownLayoutError):
        init_project(tmp_path, layout="bogus")


def test_init_adopt_preserves_preexisting_content_files(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir(parents=True)
    (tmp_path / "wiki" / "index.md").write_text("# My existing index\n", encoding="utf-8")
    (tmp_path / "raw").mkdir(parents=True)

    paths = init_project(tmp_path, adopt=True)

    assert paths.llmw_dir.is_dir()
    assert paths.config_path.is_file()
    assert (
        tmp_path / "wiki" / "index.md"
    ).read_text(encoding="utf-8") == "# My existing index\n"
    assert not (tmp_path / "wiki" / "overview.md").exists()
    assert not paths.wiki_log.exists()
    assert not (tmp_path / "raw" / "README.md").exists()


def test_init_adopt_skips_default_taxonomy_dirs(tmp_path: Path) -> None:
    paths = init_project(tmp_path, adopt=True)

    for name in ("entities", "concepts", "decisions", "syntheses", "projects", "glossary",
                 "archived", "sources"):
        assert not (tmp_path / "wiki" / name).exists(), name

    # Structural dirs llmw actually needs still get created.
    assert paths.raw.is_dir()
    assert paths.raw_inbox.is_dir()
    assert paths.raw_processed.is_dir()
    assert paths.wiki.is_dir()
    assert paths.llmw_dir.is_dir()


def test_init_adopt_never_overwrites_even_with_force(tmp_path: Path) -> None:
    (tmp_path / "wiki").mkdir(parents=True)
    (tmp_path / "wiki" / "index.md").write_text("mine\n", encoding="utf-8")

    init_project(tmp_path, adopt=True)
    init_project(tmp_path, adopt=True, force=True)

    assert (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8") == "mine\n"


def test_init_adopt_still_scaffolds_claude_plugin_by_default(tmp_path: Path) -> None:
    paths = init_project(tmp_path, adopt=True)

    assert (paths.claude_skill_dir / "SKILL.md").is_file()
    assert (paths.claude_plugin_dir / "plugin.json").is_file()


def test_init_adopt_force_preserves_config_overrides(tmp_path: Path) -> None:
    paths = init_project(tmp_path, adopt=True)
    save_config(
        paths.config_path,
        Config(
            extra_root_pages=["index.md", "log.md", "schema.md"],
            lint_required_frontmatter=["type", "status", "last_updated"],
        ),
    )

    init_project(tmp_path, adopt=True, force=True)

    reloaded = load_config(paths.config_path)
    assert reloaded.extra_root_pages == ["index.md", "log.md", "schema.md"]
    assert reloaded.lint_required_frontmatter == ["type", "status", "last_updated"]


def test_init_force_without_adopt_still_resets_config(tmp_path: Path) -> None:
    # Only --adopt protects config.toml from a --force reinit; the plain
    # (non-adopt) path keeps its existing "force resets everything" behavior.
    paths = init_project(tmp_path)
    save_config(paths.config_path, Config(extra_root_pages=["custom.md"]))

    init_project(tmp_path, force=True)

    assert load_config(paths.config_path).extra_root_pages == []
