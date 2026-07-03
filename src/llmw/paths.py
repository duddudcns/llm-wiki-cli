"""Project root discovery and path layout for an llmw project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ProjectNotFoundError(RuntimeError):
    """Raised when no .llmw directory can be found from the given start path."""


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def raw_inbox(self) -> Path:
        return self.raw / "inbox"

    @property
    def raw_processed(self) -> Path:
        return self.raw / "processed"

    @property
    def wiki(self) -> Path:
        return self.root / "wiki"

    @property
    def wiki_archived(self) -> Path:
        return self.wiki / "archived"

    @property
    def wiki_sources(self) -> Path:
        return self.wiki / "sources"

    @property
    def wiki_log(self) -> Path:
        return self.wiki / "log.md"

    @property
    def llmw_dir(self) -> Path:
        return self.root / ".llmw"

    @property
    def config_path(self) -> Path:
        return self.llmw_dir / "config.toml"

    @property
    def index_db(self) -> Path:
        return self.llmw_dir / "index.sqlite"

    @property
    def graph_json(self) -> Path:
        return self.llmw_dir / "graph.json"

    @property
    def graph_html(self) -> Path:
        return self.llmw_dir / "graph.html"

    @property
    def cache_dir(self) -> Path:
        return self.llmw_dir / "cache"

    @property
    def backups_dir(self) -> Path:
        return self.llmw_dir / "backups"

    @property
    def locks_dir(self) -> Path:
        return self.llmw_dir / "locks"

    @property
    def claude_skill_dir(self) -> Path:
        return self.root / ".claude" / "skills" / "llm-wiki"

    @property
    def claude_plugin_dir(self) -> Path:
        return self.root / ".claude-plugin"

    def rel(self, path: Path) -> str:
        """Return a POSIX-style path relative to the project root."""
        return path.resolve().relative_to(self.root.resolve()).as_posix()

    def is_inside_raw(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.raw.resolve())
            return True
        except ValueError:
            return False

    def is_inside_wiki(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.wiki.resolve())
            return True
        except ValueError:
            return False

    def is_inside_llmw(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.llmw_dir.resolve())
            return True
        except ValueError:
            return False


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from `start` looking for a `.llmw` directory."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".llmw").is_dir():
            return candidate
    raise ProjectNotFoundError(
        f"No .llmw project found starting from {current}. Run `llmw init` first."
    )


def resolve_paths(start: Path | None = None) -> ProjectPaths:
    return ProjectPaths(root=find_project_root(start))
