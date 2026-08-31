"""Make coverage see the subprocesses the suite spends most of its time in.

A large share of these tests run the real command —
`subprocess.run([sys.executable, "-m", "llmw.cli", ...])` — because that
is how a CLI is actually used, and mistakes in argument wiring, stdout
framing, and exit codes only show up there. Coverage cannot attribute a
separate process to the parent run on its own, so `llmw/cli.py` and
`llmw/_entry.py` reported **0%** while being the most-exercised modules
in the project. That is not a gap; it is an unread meter, and reading it
as "under standard" invites someone to write in-process tests
duplicating what the subprocess tests already cover.

Two things have to be true for the subprocesses to record anything:

1. `COVERAGE_PROCESS_START` names a readable config file. `coverage`
   installs a `.pth` that calls `process_startup()` in every new
   interpreter, and that function does nothing unless this is set.
2. Every process writes its data to the *same* place. Nearly all of these
   subprocesses run with `cwd=tmp_path`, so a relative `data_file` puts
   each one's data in its own throwaway directory where nothing ever
   combines it — which was the actual reason the first attempt still
   reported zero. `COVERAGE_FILE` pins an absolute path; `parallel = true`
   in `[tool.coverage.run]` keeps the processes from clobbering it.

Both are set here rather than in a config file so the paths are computed
at run time and the repository stays machine-independent, and only when
coverage is actually running, so an ordinary `pytest` does not pay for
importing coverage in every subprocess it spawns.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config) -> None:
    if not getattr(config.option, "cov_source", None):
        return
    os.environ.setdefault("COVERAGE_PROCESS_START", str(ROOT / "pyproject.toml"))
    os.environ.setdefault("COVERAGE_FILE", str(ROOT / ".coverage"))
