#!/usr/bin/env bash
# UserPromptSubmit hook: on every non-trivial user message, reminds the
# agent to search the llmw wiki before proceeding. Deliberately does not
# keyword-match the prompt against the wiki itself — a mechanical match can
# miss a note phrased differently, and a false "no related notes" signal is
# worse than a generic reminder. The actual relevance judgment and search
# are left entirely to the agent. Always exits 0 — never blocks or delays
# the turn.

llmw hook userpromptsubmit 2>/dev/null || true
exit 0
