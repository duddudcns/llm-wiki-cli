"""Console-script entry point for `llmw`.

`pyproject.toml` points the `llmw` script here rather than straight at the
Typer app, so that `llmw hook <event>` can answer without importing Typer
and Rich (~230ms on Windows) for a decision that never renders anything.
hooks.json spawns that command on every matched tool call, so the import
chain is the dominant cost, not the work.

Everything else — including `llmw hook --help`, an unrecognised event, or
any invocation carrying flags — falls through to the real CLI. This is an
optimisation, not a second argument parser.
"""

from __future__ import annotations

import sys


def main() -> None:
    argv = sys.argv[1:]
    if len(argv) == 2 and argv[0] == "hook":
        from llmw.hook_entry import EVENTS, run_event

        if argv[1] in EVENTS:
            run_event(argv[1])
            return

    from llmw.cli import app

    app()
