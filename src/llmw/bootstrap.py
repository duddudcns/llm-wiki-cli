"""`llmw init` — scaffold a new llmw project in the current directory."""

from __future__ import annotations

import datetime
import importlib.resources as resources
import string
from pathlib import Path

from llmw.config import Config, save_config
from llmw.paths import ProjectPaths

TEMPLATES = resources.files("llmw.templates")


class ProjectAlreadyExistsError(RuntimeError):
    pass


def _render(template_name: str, **subs: str) -> str:
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    return string.Template(text).substitute(**subs)


def init_project(root: Path, force: bool = False) -> ProjectPaths:
    paths = ProjectPaths(root=root.resolve())

    if paths.llmw_dir.exists() and not force:
        raise ProjectAlreadyExistsError(
            f"{paths.llmw_dir} already exists. Use --force to reinitialize."
        )

    today = datetime.date.today().isoformat()

    for d in [
        paths.raw,
        paths.raw_inbox,
        paths.raw_processed,
        paths.wiki,
        paths.wiki_archived,
        paths.wiki_sources,
        paths.root / "wiki" / "entities",
        paths.root / "wiki" / "concepts",
        paths.root / "wiki" / "decisions",
        paths.root / "wiki" / "syntheses",
        paths.root / "wiki" / "projects",
        paths.root / "wiki" / "glossary",
        paths.llmw_dir,
        paths.cache_dir,
        paths.backups_dir,
        paths.locks_dir,
        paths.claude_skill_dir,
        paths.claude_plugin_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

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

    if not paths.config_path.exists() or force:
        save_config(paths.config_path, Config(created=today))

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
