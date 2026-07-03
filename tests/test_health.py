from pathlib import Path

from llmw.bootstrap import init_project
from llmw.health import check_health
from llmw.indexer import rebuild


def test_health_before_rebuild_reports_unhealthy(tmp_path: Path):
    paths = init_project(tmp_path)
    report = check_health(paths)
    assert report.checks["wiki_dir_exists"] is True
    assert report.checks["index_readable"] is False
    assert report.is_healthy() is False


def test_health_after_rebuild_is_healthy(tmp_path: Path):
    paths = init_project(tmp_path)
    rebuild(paths)
    report = check_health(paths)
    assert report.is_healthy() is True
