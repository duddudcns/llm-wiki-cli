"""`llmw init` — scaffold a new llmw project in the current directory."""

from __future__ import annotations

import datetime
import importlib.resources as resources
import string
from pathlib import Path

from llmw.config import Config, save_config
from llmw.paths import AI_WIKI_DIR_NAME, ProjectPaths

TEMPLATES = resources.files("llmw.templates")

LAYOUTS = ("classic", "ai-wiki")


class ProjectAlreadyExistsError(RuntimeError):
    pass


class UnknownLayoutError(ValueError):
    pass


def _render(template_name: str, **subs: str) -> str:
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    return string.Template(text).substitute(**subs)


def init_project(
    root: Path,
    force: bool = False,
    claude_plugin: bool = True,
    layout: str = "classic",
    adopt: bool = False,
) -> ProjectPaths:
    """Scaffold a new llmw project.

    `claude_plugin=False` skips creating the project-local
    `.claude/skills/llm-wiki/` and `.claude-plugin/plugin.json` copies —
    use this when the llm-wiki Claude Code plugin is already installed
    from the marketplace, so a project doesn't end up with two competing
    copies of the same skill.

    `layout="classic"` (default) puts `raw/`, `wiki/`, and `.llmw/`
    directly in `root`. `layout="ai-wiki"` nests them under
    `root/ai-wiki/` instead, keeping `root` itself uncluttered; `.claude/`
    and `.claude-plugin/` still scaffold at `root` either way.

    `adopt=True` is for pointing llmw at a wiki that already has real
    content under its own conventions (e.g. a hand-rolled Karpathy-pattern
    wiki): it still creates `.llmw/` on first run, but never writes the
    default content files (`raw/README.md`, `wiki/index.md`,
    `wiki/overview.md`, `wiki/log.md`) or the default taxonomy
    subfolders (`entities/`, `concepts/`, `decisions/`, `syntheses/`,
    `projects/`, `glossary/`, `archived/`, `sources/`) — not even with
    `--force` — so pre-existing content at those paths is never touched.
    Once `config.toml` exists, `--force` never rewrites it back to
    defaults either, so hand-tuned `extra_root_pages`/
    `lint_required_frontmatter` overrides for the adopted schema survive
    a re-`init --adopt --force` (they would NOT survive a re-`init
    --force` without `--adopt`, which still resets config.toml).
    """
    if layout not in LAYOUTS:
        raise UnknownLayoutError(f"Unknown layout {layout!r}; expected one of {LAYOUTS}.")

    project_root = root.resolve()
    wiki_root = project_root / AI_WIKI_DIR_NAME if layout == "ai-wiki" else project_root
    paths = ProjectPaths(root=wiki_root, project_root=project_root)

    if paths.llmw_dir.exists() and not force:
        raise ProjectAlreadyExistsError(
            f"{paths.llmw_dir} already exists. Use --force to reinitialize."
        )

    today = datetime.date.today().isoformat()

    dirs = [
        paths.raw,
        paths.raw_inbox,
        paths.raw_processed,
        paths.wiki,
        paths.llmw_dir,
        paths.cache_dir,
        paths.backups_dir,
        paths.locks_dir,
    ]
    if not adopt:
        dirs += [
            paths.wiki_archived,
            paths.wiki_sources,
            paths.root / "wiki" / "entities",
            paths.root / "wiki" / "concepts",
            paths.root / "wiki" / "decisions",
            paths.root / "wiki" / "syntheses",
            paths.root / "wiki" / "projects",
            paths.root / "wiki" / "glossary",
        ]
    if claude_plugin:
        dirs += [paths.claude_skill_dir, paths.claude_plugin_dir]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    if not adopt:
        raw_readme = paths.raw / "README.md"
        if not raw_readme.exists() or force:
            raw_readme.write_text(
                "# raw/\n\n"
                "Immutable source material. Neither the AI agent nor the "
                "`llmw` CLI may modify files in this directory. Drop new "
                "material into `inbox/`; converted output (e.g. from PDFs) "
                "goes into `processed/`.\n",
                encoding="utf-8",
                newline="\n",
            )

        if not (paths.wiki / "index.md").exists() or force:
            (paths.wiki / "index.md").write_text(
                _render("wiki_index.md", created=today), encoding="utf-8", newline="\n"
            )
        if not (paths.wiki / "overview.md").exists() or force:
            (paths.wiki / "overview.md").write_text(
                _render("wiki_overview.md", created=today), encoding="utf-8", newline="\n"
            )
        if not paths.wiki_log.exists() or force:
            paths.wiki_log.write_text(
                _render("wiki_log.md", created=today), encoding="utf-8", newline="\n"
            )

    # Under --adopt, config.toml is exactly the kind of pre-existing
    # customization (extra_root_pages, lint_required_frontmatter, ...) that
    # --adopt promises never to clobber — so --force never touches it once
    # it exists, unlike the plain (non-adopt) path below.
    if not paths.config_path.exists() or (force and not adopt):
        save_config(paths.config_path, Config(created=today))

    if claude_plugin:
        skill_dir = paths.claude_skill_dir
        (skill_dir / "SKILL.md").write_text(
            (TEMPLATES / "skill_SKILL.md").read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )
        (skill_dir / "reference.md").write_text(
            (TEMPLATES / "skill_reference.md").read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )
        (skill_dir / "examples.md").write_text(
            (TEMPLATES / "skill_examples.md").read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )

        (paths.claude_plugin_dir / "plugin.json").write_text(
            (TEMPLATES / "plugin.json").read_text(encoding="utf-8"),
            encoding="utf-8",
            newline="\n",
        )

    return paths
