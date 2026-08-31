#!/usr/bin/env bash
# Stop hook: at the end of each agent turn, if source files changed this
# session without a corresponding llmw write/edit/patch/archive call since,
# blocks the stop once with a reminder to update the wiki. Claude Code's
# stop_hook_active flag (passed in the payload on the forced-continuation
# retry) keeps this to at most one nudge per turn — never an infinite
# loop. Always exits 0 — never crashes a turn.
#
# hooks.json no longer routes this event through this file - it calls
# `llmw hook <event> || exit 0` directly, so a Windows hook host cannot
# resolve a bare `.sh` path through ShellExecute and launch the file's
# associated application instead of running it (the launched app never
# inherits the hook's stdin/stdout pipe). Kept as a manual entry point
# and as a fallback for hosts that can only take a script path; the
# `|| true` plus trailing `exit 0` still cover `llmw` missing from PATH.

llmw hook stop 2>/dev/null || true
exit 0
