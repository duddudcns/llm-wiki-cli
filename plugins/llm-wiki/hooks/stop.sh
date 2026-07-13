#!/usr/bin/env bash
# Stop hook: forwards the turn payload (via stdin) to `llmw hook
# codex-stop` and prints whatever it returns. Mirrors
# plugin/hooks/stop.sh on the Claude Code side, including the reason this
# wrapper exists at all: if `llmw` isn't on PATH yet (first session
# before SessionStart's self-install completes, or the install failed),
# the shell fails to spawn it (exit 127) before cli.py's own
# never-crash-a-turn guarantee ever gets a chance to run. `|| true` plus
# the trailing `exit 0` catch that case; a bare `llmw hook codex-stop` in
# hooks.json (the previous setup) did not.

llmw hook codex-stop 2>/dev/null || true
exit 0
