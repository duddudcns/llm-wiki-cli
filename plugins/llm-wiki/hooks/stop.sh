#!/usr/bin/env bash
# Stop hook: forwards the turn payload (via stdin) to `llmw hook
# codex-stop` and prints whatever it returns. Mirrors
# plugin/hooks/stop.sh on the Claude Code side, including the reason this
# wrapper exists at all: if `llmw` isn't on PATH yet (first session
# before SessionStart's self-install completes, or the install failed),
# the shell fails to spawn it (exit 127) before cli.py's own
# never-crash-a-turn guarantee ever gets a chance to run. `|| true` plus
# the trailing `exit 0` catch that case; a bare `llmw hook codex-stop` in
# hooks.json — with no `||` clause, as an even earlier setup had it — did
# not.
#
# hooks.json no longer routes this event through this file - it calls
# `llmw hook <event> || exit 0` directly, so a Windows hook host cannot
# resolve a bare `.sh` path through ShellExecute and launch the file's
# associated application instead of running it (the launched app never
# inherits the hook's stdin/stdout pipe). Kept as a manual entry point
# and as a fallback for hosts that can only take a script path; the
# `|| true` plus trailing `exit 0` still cover `llmw` missing from PATH.

llmw hook codex-stop 2>/dev/null || true
exit 0
