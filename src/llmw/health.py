"""`llmw health` — system-level checks distinct from `lint`'s content checks."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from llmw.config import load_config
from llmw.indexer import SCHEMA_VERSION
from llmw.paths import ProjectPaths


@dataclass
class HealthReport:
    checks: dict[str, bool] = field(default_factory=dict)
    details: dict[str, str] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        return all(self.checks.values())

    def as_dict(self) -> dict:
        return {"healthy": self.is_healthy(), "checks": self.checks, "details": self.details}


def _check(report: HealthReport, name: str, ok: bool, detail: str = "") -> None:
    report.checks[name] = ok
    if detail:
        report.details[name] = detail


def check_health(paths: ProjectPaths) -> HealthReport:
    report = HealthReport()

    _check(report, "wiki_dir_exists", paths.wiki.is_dir())
    _check(report, "raw_dir_exists", paths.raw.is_dir())

    if paths.config_path.is_file():
        try:
            load_config(paths.config_path)
            _check(report, "config_readable", True)
        except Exception as exc:  # noqa: BLE001
            _check(report, "config_readable", False, str(exc))
    else:
        _check(report, "config_readable", False, "config.toml missing")

    if paths.index_db.is_file():
        try:
            conn = sqlite3.connect(paths.index_db)
            try:
                conn.execute("SELECT COUNT(*) FROM pages").fetchone()
                _check(report, "index_readable", True)
                row = conn.execute(
                    "SELECT value FROM meta WHERE key = 'schema_version'"
                ).fetchone()
                if row and int(row[0]) == SCHEMA_VERSION:
                    _check(report, "schema_version_ok", True)
                else:
                    got = row[0] if row else "missing"
                    _check(
                        report,
                        "schema_version_ok",
                        False,
                        f"expected {SCHEMA_VERSION}, got {got}",
                    )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            _check(report, "index_readable", False, str(exc))
            _check(report, "schema_version_ok", False, "index unreadable")
    else:
        _check(report, "index_readable", False, "index.sqlite not built yet")
        _check(report, "schema_version_ok", False, "index.sqlite not built yet")

    stale_locks = []
    if paths.locks_dir.is_dir():
        stale_locks = [p.name for p in paths.locks_dir.glob("*.lock")]
    _check(
        report,
        "no_stale_locks",
        len(stale_locks) == 0,
        f"stale locks: {stale_locks}" if stale_locks else "",
    )

    return report
