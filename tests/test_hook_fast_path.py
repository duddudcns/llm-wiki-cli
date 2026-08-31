"""`llmw hook <event>` must not pay for the full CLI to make its decision.

hooks.json calls `llmw hook pretooluse` on every matched tool call, so the
process spawns constantly. The console script used to point straight at
the Typer app, which pulled in typer + rich (~230ms) and, through
`llmw.hook`, the indexer -> parser -> yaml chain (~50ms) — none of which
the decision needs on the common path where a shell command names no
wiki/raw file.

These tests pin the fast path three ways: the modules it must not import
with no project present, the CLI machinery it must not import even inside
a real project (where config and index loads legitimately happen), and
byte-identical output against the Typer path it replaced.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]

# The CLI machinery, which no hook decision ever needs. This holds
# everywhere — in a project or not — and is the ~230ms the fast path
# actually buys.
ALWAYS_FORBIDDEN = ("typer", "rich", "llmw.cli")

# Additionally absent when there is no llmw project to answer for:
# `find_project_root` fails before the config load, so nothing pulls in
# the indexer -> parser -> yaml chain. *Inside* a project every event
# loads config and these do appear — measured, not assumed. The
# in-project test below pins what is still forbidden there, because
# running only the no-project case would let a new module-scope CLI
# import slip in behind a branch this file never reaches.
FORBIDDEN_ON_FAST_PATH = (*ALWAYS_FORBIDDEN, "llmw.indexer", "yaml")

PAYLOADS = {
    "pretooluse": {"tool_name": "Bash", "tool_input": {"command": "echo ok"}},
    "session-start": {"cwd": "."},
    "userpromptsubmit": {"prompt": "add a retry to the uploader", "cwd": "."},
    "stop": {"session_id": "fast-path-test", "cwd": "."},
    "codex-pretooluse": {"tool_name": "apply_patch", "tool_input": {}},
    "codex-stop": {"session_id": "fast-path-test", "cwd": "."},
}

# session-start reports wiki status, so it legitimately loads the indexer.
# It still has to match the Typer path — and it is the one dispatch entry
# whose argument shape differs (`payload["cwd"]`, not the payload), which
# is exactly where a table-driven rewrite goes wrong.
LEAN_EVENTS = sorted(set(PAYLOADS) - {"session-start"})


def test_every_dispatched_event_is_covered_here() -> None:
    from llmw.hook_entry import EVENTS

    assert sorted(EVENTS) == sorted(PAYLOADS)


def _run_child(script: str, payload: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        input=payload,
        cwd=cwd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("event", LEAN_EVENTS)
def test_fast_path_does_not_import_the_cli_or_the_indexer(
    event: str, tmp_path: Path
) -> None:
    result = _run_child(
        f"""
        import json, sys
        sys.argv = ["llmw", "hook", {event!r}]
        from llmw._entry import main
        main()
        loaded = [m for m in {FORBIDDEN_ON_FAST_PATH!r} if m in sys.modules]
        print(json.dumps(loaded), file=sys.stderr)
        """,
        json.dumps(PAYLOADS[event]),
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stderr.strip().splitlines()[-1])
    assert loaded == [], f"{event} pulled in {loaded} on the fast path"


@pytest.mark.parametrize("event", sorted(PAYLOADS))
def test_the_cli_never_loads_inside_a_real_project_either(
    event: str, tmp_path: Path
) -> None:
    # The branch the no-project test above cannot reach: with a real
    # `.llmw` present, every event loads config and Stop additionally
    # opens the index, so the indexer and yaml legitimately appear. What
    # must never appear is the CLI app — and that is exactly the import
    # a future module-scope convenience would add without any other test
    # noticing.
    from llmw.bootstrap import init_project

    init_project(tmp_path)
    result = _run_child(
        f"""
        import json, sys
        sys.argv = ["llmw", "hook", {event!r}]
        from llmw._entry import main
        main()
        loaded = [m for m in {ALWAYS_FORBIDDEN!r} if m in sys.modules]
        print(json.dumps(loaded), file=sys.stderr)
        """,
        json.dumps(PAYLOADS[event]),
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stderr.strip().splitlines()[-1])
    assert loaded == [], f"{event} pulled in {loaded} inside a project"


@pytest.mark.parametrize("event", sorted(PAYLOADS))
def test_fast_path_output_matches_the_typer_path(event: str, tmp_path: Path) -> None:
    payload = json.dumps(PAYLOADS[event])
    fast = _run_child(
        f"""
        import sys
        sys.argv = ["llmw", "hook", {event!r}]
        from llmw._entry import main
        main()
        """,
        payload,
        tmp_path,
    )
    typer_path = _run_child(
        f"""
        import sys
        sys.argv = ["llmw", "hook", {event!r}]
        from llmw.cli import app
        try:
            app()
        except SystemExit as exc:
            sys.exit(exc.code or 0)
        """,
        payload,
        tmp_path,
    )
    assert fast.returncode == 0, fast.stderr
    assert typer_path.returncode == 0, typer_path.stderr
    assert fast.stdout == typer_path.stdout


def test_unknown_and_flagged_hook_invocations_fall_through_to_typer(
    tmp_path: Path,
) -> None:
    # `--help`, an unknown event, and bare `hook` must still reach the real
    # CLI: the fast path is an optimisation, not a second argument parser.
    for argv in (["hook", "--help"], ["hook", "not-an-event"], ["hook"]):
        result = _run_child(
            f"""
            import sys
            sys.argv = ["llmw", *{argv!r}]
            from llmw._entry import main
            try:
                main()
            except SystemExit:
                pass
            print("typer" in sys.modules, file=sys.stderr)
            """,
            "{}",
            tmp_path,
        )
        assert result.stderr.strip().splitlines()[-1] == "True", (
            f"{argv} did not fall through to typer"
        )


def test_console_script_points_at_the_fast_entry() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'llmw = "llmw._entry:main"' in text
