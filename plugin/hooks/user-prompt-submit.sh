#!/usr/bin/env bash
# UserPromptSubmit hook: on every user message, nudges the agent to check
# the llmw wiki before proceeding — searches the prompt text itself so the
# reminder names specific related notes instead of just "a wiki exists"
# (which SessionStart already says once, and gets forgotten many turns
# into a session). Always exits 0 — never blocks or delays the turn.

llmw hook userpromptsubmit 2>/dev/null || true
exit 0
