#!/usr/bin/env bash
# PreToolUse hook: redirects native Edit/Write/NotebookEdit calls aimed at
# wiki/*.md or raw/** back to llmw's own write/edit/patch/archive commands,
# and soft-gates the first real source-file edit of a session behind an
# `llmw search` check if none has run yet. For Bash calls, only watches
# for `llmw search`/`llmw write|edit|patch|archive` to update per-session
# state (never gates Bash itself) — cheaply skipped unless the command
# string contains "llmw" at all. Always exits 0 — never blocks a tool call
# by crashing.

payload=$(cat)
case "$payload" in
  *'"tool_name":"Bash"'*|*'"tool_name": "Bash"'*)
    case "$payload" in
      *llmw*) printf '%s' "$payload" | llmw hook pretooluse 2>/dev/null || true ;;
    esac
    ;;
  *)
    printf '%s' "$payload" | llmw hook pretooluse 2>/dev/null || true
    ;;
esac
exit 0
