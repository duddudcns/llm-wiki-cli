"""Project root discovery and path layout for an llmw project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# When raw/wiki/.llmw don't live directly at the project root, llmw looks
# for them nested one level down in a folder with this name.
AI_WIKI_DIR_NAME = "ai-wiki"


class ProjectNotFoundError(RuntimeError):
    """Raised when no .llmw directory can be found from the given start path."""


@dataclass(frozen=True)
class ProjectPaths:
    # Directory that directly holds raw/, wiki/, .llmw/ — either the
    # project root itself (classic layout) or `<project_root>/ai-wiki`
    # (nested layout).
    root: Path
    # Outer project directory (e.g. where .claude/ and .git/ live). Equal
    # to `root` in the classic layout; set explicitly when `root` is
    # nested under `ai-wiki/`.
    project_root: Path | None = None

    def __post_init__(self) -> None:
        if self.project_root is None:
            object.__setattr__(self, "project_root", self.root)

    @classmethod
    def for_project_root(cls, project_root: Path) -> "ProjectPaths":
        """Detect the wiki layout under `project_root`.

        Prefers the classic layout (`.llmw` directly in `project_root`);
        falls back to the nested `ai-wiki/` layout if that's what's there.
        """
        project_root = project_root.resolve()
        nested = project_root / AI_WIKI_DIR_NAME
        if not (project_root / ".llmw").is_dir() and (nested / ".llmw").is_dir():
            return cls(root=nested, project_root=project_root)
        return cls(root=project_root, project_root=project_root)

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
        return self.project_root / ".claude" / "skills" / "llm-wiki"

    @property
    def claude_plugin_dir(self) -> Path:
        return self.project_root / ".claude-plugin"

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
    """Walk upward from `start` looking for a `.llmw` directory, either
    directly in a candidate directory or nested under `ai-wiki/`."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".llmw").is_dir() or (candidate / AI_WIKI_DIR_NAME / ".llmw").is_dir():
            return candidate
    raise ProjectNotFoundError(
        f"No .llmw project found starting from {current} (checked '.llmw/' "
        f"and '{AI_WIKI_DIR_NAME}/.llmw/' at each level up). Run `llmw init` first."
    )


def resolve_paths(start: Path | None = None, root_override: Path | None = None) -> ProjectPaths:
    """Resolve project paths.

    `root_override`, when given, is used directly as the project root
    instead of walking upward from `start`/cwd — a manual escape hatch for
    non-standard setups (e.g. running from outside the project tree).
    """
    if root_override is not None:
        project_root = root_override.resolve()
        nested = project_root / AI_WIKI_DIR_NAME
        if not (project_root / ".llmw").is_dir() and not (nested / ".llmw").is_dir():
            raise ProjectNotFoundError(
                f"No .llmw project found at {project_root} (checked '.llmw/' "
                f"and '{AI_WIKI_DIR_NAME}/.llmw/'). Run `llmw init` first."
            )
        return ProjectPaths.for_project_root(project_root)
    return ProjectPaths.for_project_root(find_project_root(start))
