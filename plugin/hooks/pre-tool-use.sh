#!/usr/bin/env bash
# PreToolUse hook: redirects native Edit/Write/NotebookEdit calls aimed at
# wiki/*.md or raw/** back to llmw's own write/edit/patch/archive commands,
# and soft-gates the first real source-file edit of a session behind an
# `llmw search` check if none has run yet. For Bash/PowerShell calls,
# watches for `llmw search`/`llmw write|edit|patch|archive` to update
# per-session state, and blocks a raw shell write into wiki/ or raw/
# — cheaply skipped unless the payload mentions "llmw", or names a
# wiki/raw path *and* a file-mutating command (either alone is common in
# a normal command; together is rare, so the Python process is only spawned
# when there is something to decide). `sed` counts as file-mutating only
# in its `-i`/`--in-place` form: plain `sed -n '1,5p' wiki/x.md` is a read,
# and `sed ... > wiki/x.md` is already caught by the `>`. Direct calls
# to this plugin's own mcp__llm-wiki__llmw_* MCP tools (if a project has
# that server registered) get the same per-session bookkeeping, keyed off
# the tool name instead of a command string. Always exits 0 — never blocks
# a tool call by crashing.

payload=$(cat)
run_hook() { printf '%s' "$payload" | llmw hook pretooluse 2>/dev/null || true; }

case "$payload" in
  *'"tool_name":"Bash"'*|*'"tool_name": "Bash"'*|*'"tool_name":"PowerShell"'*|*'"tool_name": "PowerShell"'*)
    case "$payload" in
      *llmw*) run_hook ;;
      *wiki/*|*raw/*|*'wiki\\'*|*'raw\\'*)
        case "$payload" in
          *'>'*|*Set-Content*|*Add-Content*|*Clear-Content*|*Out-File*|*New-Item*|*Remove-Item*|*Move-Item*|*Copy-Item*|*' rm '*|*' mv '*|*' cp '*|*' tee '*|*'sed -i'*|*'sed --in-place'*|*truncate*) run_hook ;;
        esac
        ;;
    esac
    ;;
  *)
    run_hook
    ;;
esac
exit 0
