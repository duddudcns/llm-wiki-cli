"""Typer-free dispatch for `llmw hook <event>`.

Every hook command has the same shape: read a JSON payload from stdin,
hand it to an `evaluate_*` function, print the result (or nothing), and
exit 0 no matter what. Keeping that shape in one place means the fast
console-script path in `llmw._entry` and the Typer commands in
`llmw.cli` cannot drift apart — `cli.py` delegates here rather than
holding a second copy.

Nothing here imports Typer, and the `evaluate_*` module is imported
inside `run_event` rather than at module scope, so `llmw hook pretooluse`
pays only for the decision it actually makes. That matters because
hooks.json spawns this on every matched tool call.
"""

from __future__ import annotations

import json
import sys

_JSON = "json"
_TEXT = "text"

# event name -> (module, evaluate function, output mode, argument shape)
EVENTS: dict[str, tuple[str, str, str, str]] = {
    "pretooluse": ("llmw.hook", "evaluate_pretooluse", _JSON, "payload"),
    "session-start": ("llmw.hook", "evaluate_sessionstart", _TEXT, "cwd"),
    "userpromptsubmit": ("llmw.hook", "evaluate_userpromptsubmit", _TEXT, "payload"),
    "stop": ("llmw.hook", "evaluate_stop", _JSON, "payload"),
    "codex-pretooluse": (
        "llmw.codex_hook",
        "evaluate_codex_pretooluse",
        _JSON,
        "payload",
    ),
    "codex-stop": ("llmw.codex_hook", "evaluate_codex_stop", _JSON, "payload"),
}


def run_event(event: str) -> None:
    """Run one hook event end to end. Never raises: a hook must not crash a
    tool call, a turn, or session start."""
    module_name, func_name, mode, arg_shape = EVENTS[event]
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        from importlib import import_module

        evaluate = getattr(import_module(module_name), func_name)
        argument = (payload.get("cwd") or ".") if arg_shape == "cwd" else payload
        result = evaluate(argument)
    except Exception:  # noqa: BLE001 - a hook must never crash its caller
        return

    if mode == _JSON:
        if result is not None:
            print(json.dumps(result))
    elif result:
        print(result)
