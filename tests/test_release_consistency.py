"""Guardrails against release-process drift: the version string is
duplicated across 5 files (no single source of truth yet), and the
plugin's shipped skill docs are duplicated from the `llmw init` templates
(one copy is what a marketplace install gets, the other is what a fresh
`llmw init` scaffolds) — both must be bumped/edited in lockstep by hand.
These tests turn "forgot to bump one" into a red test instead of a silent
version-skew bug discovered after a release.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERSION_FILES = (
    ROOT / "pyproject.toml",
    ROOT / "src" / "llmw" / "__init__.py",
    ROOT / "plugin" / ".claude-plugin" / "plugin.json",
    ROOT / "src" / "llmw" / "templates" / "plugin.json",
    ROOT / "examples" / "sample-project" / ".claude-plugin" / "plugin.json",
)


def _extract_version(path: Path) -> str:
    if path.suffix == ".toml":
        return tomllib.loads(path.read_text(encoding="utf-8"))["project"]["version"]
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))["version"]
    if path.suffix == ".py":
        match = re.search(r'__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
        assert match, f"no __version__ assignment found in {path}"
        return match.group(1)
    raise AssertionError(f"unrecognized version file type: {path}")


def test_version_lockstep():
    versions = {str(p.relative_to(ROOT)): _extract_version(p) for p in VERSION_FILES}
    distinct = set(versions.values())
    assert len(distinct) == 1, f"version mismatch across files: {versions}"


def test_plugin_skill_matches_templates():
    plugin_dir = ROOT / "plugin" / "skills" / "llm-wiki"
    template_dir = ROOT / "src" / "llmw" / "templates"
    pairs = (
        (plugin_dir / "SKILL.md", template_dir / "skill_SKILL.md"),
        (plugin_dir / "reference.md", template_dir / "skill_reference.md"),
        (plugin_dir / "examples.md", template_dir / "skill_examples.md"),
    )
    for plugin_file, template_file in pairs:
        assert plugin_file.read_bytes() == template_file.read_bytes(), (
            f"{plugin_file.relative_to(ROOT)} and {template_file.relative_to(ROOT)} drifted apart"
        )
