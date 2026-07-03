"""Minimal config.toml read/write for an llmw project.

The config schema is intentionally tiny (a handful of scalar keys plus a
couple of string-list overrides), so we hand-roll serialization instead of
pulling in a TOML-writer dependency. Reading uses the stdlib `tomllib`
(Python 3.11+).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1

DEFAULT_LINT_REQUIRED_FRONTMATTER = ["type", "status", "created", "updated"]


@dataclass(frozen=True)
class Config:
    schema_version: int = SCHEMA_VERSION
    created: str = ""
    default_search_limit: int = 5
    default_related_limit: int = 10
    archive_tombstone: bool = True
    # Frontmatter keys `llmw lint` treats as required. Override this for
    # wikis with a different schema (e.g. only `type`/`status`, or a
    # `last_updated` field instead of separate `created`/`updated`).
    lint_required_frontmatter: list[str] = field(
        default_factory=lambda: list(DEFAULT_LINT_REQUIRED_FRONTMATTER)
    )
    # Extra individual Markdown files, relative to the project root, to
    # index alongside `wiki/**/*.md` — for wikis that keep top-level files
    # like `index.md`/`log.md`/`schema.md` outside the `wiki/` directory.
    extra_root_pages: list[str] = field(default_factory=list)

    def to_toml(self) -> str:
        return (
            "[llmw]\n"
            f"schema_version = {self.schema_version}\n"
            f'created = "{self.created}"\n'
            "\n"
            "[paths]\n"
            f"extra_root_pages = {_toml_string_array(self.extra_root_pages)}\n"
            "\n"
            "[defaults]\n"
            f"search_limit = {self.default_search_limit}\n"
            f"related_limit = {self.default_related_limit}\n"
            f"archive_tombstone = {str(self.archive_tombstone).lower()}\n"
            "\n"
            "[lint]\n"
            f"required_frontmatter = {_toml_string_array(self.lint_required_frontmatter)}\n"
        )


def _toml_string_array(values: list[str]) -> str:
    escaped = ", ".join('"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"' for v in values)
    return f"[{escaped}]"


def load_config(config_path: Path) -> Config:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    llmw = data.get("llmw", {})
    paths = data.get("paths", {})
    defaults = data.get("defaults", {})
    lint = data.get("lint", {})
    return Config(
        schema_version=llmw.get("schema_version", SCHEMA_VERSION),
        created=llmw.get("created", ""),
        extra_root_pages=list(paths.get("extra_root_pages", [])),
        default_search_limit=defaults.get("search_limit", 5),
        default_related_limit=defaults.get("related_limit", 10),
        archive_tombstone=defaults.get("archive_tombstone", True),
        lint_required_frontmatter=list(
            lint.get("required_frontmatter", DEFAULT_LINT_REQUIRED_FRONTMATTER)
        ),
    )


def save_config(config_path: Path, config: Config) -> None:
    config_path.write_text(config.to_toml(), encoding="utf-8", newline="\n")
