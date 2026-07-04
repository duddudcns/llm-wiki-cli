from pathlib import Path

import pytest

from llmw.bootstrap import init_project
from llmw.paths import ProjectNotFoundError, find_project_root, resolve_paths


def test_find_project_root_detects_classic_layout(tmp_path: Path) -> None:
    init_project(tmp_path)
    assert find_project_root(tmp_path) == tmp_path.resolve()


def test_find_project_root_detects_nested_ai_wiki_layout(tmp_path: Path) -> None:
    init_project(tmp_path, layout="ai-wiki")
    assert find_project_root(tmp_path) == tmp_path.resolve()


def test_resolve_paths_auto_detects_ai_wiki_from_project_root(tmp_path: Path) -> None:
    paths = init_project(tmp_path, layout="ai-wiki")

    resolved = resolve_paths(start=tmp_path)
    assert resolved.root == paths.root
    assert resolved.project_root == paths.project_root


def test_resolve_paths_from_cwd_inside_ai_wiki_treats_it_as_self_contained(tmp_path: Path) -> None:
    # Walking up from INSIDE ai-wiki/ itself hits ai-wiki/.llmw as the
    # nearest match and treats ai-wiki/ as a project of its own — the same
    # "nearest .llmw wins" rule that governs any other nested llmw project.
    paths = init_project(tmp_path, layout="ai-wiki")
    nested_cwd = paths.wiki / "concepts"
    nested_cwd.mkdir(parents=True, exist_ok=True)

    resolved = resolve_paths(start=nested_cwd)
    assert resolved.root == paths.root
    assert resolved.project_root == paths.root


def test_resolve_paths_prefers_classic_layout_when_both_present(tmp_path: Path) -> None:
    # A directory that happens to have both a top-level .llmw AND a nested
    # ai-wiki/.llmw should resolve to the classic (outer) one — it's the
    # nearer, more specific match.
    init_project(tmp_path)
    init_project(tmp_path / "ai-wiki")

    resolved = resolve_paths(start=tmp_path)
    assert resolved.root == tmp_path.resolve()


def test_resolve_paths_root_override_targets_ai_wiki_project(tmp_path: Path) -> None:
    init_project(tmp_path, layout="ai-wiki")

    resolved = resolve_paths(root_override=tmp_path)
    assert resolved.root == (tmp_path / "ai-wiki").resolve()
    assert resolved.project_root == tmp_path.resolve()


def test_resolve_paths_root_override_targets_classic_project(tmp_path: Path) -> None:
    init_project(tmp_path)

    resolved = resolve_paths(root_override=tmp_path)
    assert resolved.root == tmp_path.resolve()


def test_resolve_paths_root_override_missing_project_raises(tmp_path: Path) -> None:
    with pytest.raises(ProjectNotFoundError):
        resolve_paths(root_override=tmp_path)
