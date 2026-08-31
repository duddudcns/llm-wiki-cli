#!/usr/bin/env bash
# UserPromptSubmit hook: on every non-trivial user message, reminds the
# agent to search the llmw wiki before proceeding. Deliberately does not
# keyword-match the prompt against the wiki itself — a mechanical match can
# miss a note phrased differently, and a false "no related notes" signal is
# worse than a generic reminder. The actual relevance judgment and search
# are left entirely to the agent. Always exits 0 — never blocks or delays
# the turn.
#
# hooks.json no longer routes this event through this file - it calls
# `llmw hook <event> || exit 0` directly, so a Windows hook host cannot
# resolve a bare `.sh` path through ShellExecute and launch the file's
# associated application instead of running it (the launched app never
# inherits the hook's stdin/stdout pipe). Kept as a manual entry point
# and as a fallback for hosts that can only take a script path; the
# `|| true` plus trailing `exit 0` still cover `llmw` missing from PATH.

llmw hook userpromptsubmit 2>/dev/null || true
exit 0
