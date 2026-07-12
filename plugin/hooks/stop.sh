#!/usr/bin/env bash
# Stop hook: at the end of each agent turn, if source files changed this
# session without a corresponding llmw write/edit/patch/archive call since,
# blocks the stop once with a reminder to update the wiki. Claude Code's
# stop_hook_active flag (passed in the payload on the forced-continuation
# retry) keeps this to at most one nudge per turn — never an infinite
# loop. Always exits 0 — never crashes a turn.

llmw hook stop 2>/dev/null || true
exit 0
