"""Minimal config.toml read/write for an llmw project.

The config schema is intentionally tiny (a handful of scalar keys), so we
hand-roll serialization instead of pulling in a TOML-writer dependency.
Reading uses the stdlib `tomllib` (Python 3.11+).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Config:
    schema_version: int = SCHEMA_VERSION
    created: str = ""
    raw_dir: str = "raw"
    wiki_dir: str = "wiki"
    default_search_limit: int = 5
    default_related_limit: int = 10
    archive_tombstone: bool = True
    tags: list[str] = field(default_factory=list)

    def to_toml(self) -> str:
        return (
            "[llmw]\n"
            f"schema_version = {self.schema_version}\n"
            f'created = "{self.created}"\n'
            "\n"
            "[paths]\n"
            f'raw = "{self.raw_dir}"\n'
            f'wiki = "{self.wiki_dir}"\n'
            "\n"
            "[defaults]\n"
            f"search_limit = {self.default_search_limit}\n"
            f"related_limit = {self.default_related_limit}\n"
            f"archive_tombstone = {str(self.archive_tombstone).lower()}\n"
        )


def load_config(config_path: Path) -> Config:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    llmw = data.get("llmw", {})
    paths = data.get("paths", {})
    defaults = data.get("defaults", {})
    return Config(
        schema_version=llmw.get("schema_version", SCHEMA_VERSION),
        created=llmw.get("created", ""),
        raw_dir=paths.get("raw", "raw"),
        wiki_dir=paths.get("wiki", "wiki"),
        default_search_limit=defaults.get("search_limit", 5),
        default_related_limit=defaults.get("related_limit", 10),
        archive_tombstone=defaults.get("archive_tombstone", True),
    )


def save_config(config_path: Path, config: Config) -> None:
    config_path.write_text(config.to_toml(), encoding="utf-8", newline="\n")
