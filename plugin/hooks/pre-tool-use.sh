#!/usr/bin/env bash
# PreToolUse hook: redirects native Edit/Write/NotebookEdit calls aimed at
# wiki/*.md or raw/** back to llmw's own write/edit/patch/archive commands,
# soft-gates the first real source-file edit of a session behind an
# `llmw search` check, and denies raw shell writes into wiki/ or raw/.
# All of that decision logic lives in `llmw hook pretooluse`.
#
# hooks.json no longer routes PreToolUse through this file — it calls
# `llmw hook pretooluse || exit 0` directly, because on Windows a hook
# host that resolves a bare `.sh` path through ShellExecute launches the
# file's associated application instead of running it, and the launched
# app never inherits the hook's stdin/stdout pipe. This wrapper is kept
# as a manual entry point and as a fallback for hosts that can only take
# a script path.
#
# It used to carry a shell prefilter that skipped the Python process for
# Bash/PowerShell payloads with no wiki/raw path and no file-mutating
# token. That saved ~350ms per shell tool call but silently missed a
# command *starting* with `rm`/`mv`/`cp`/`tee` (the patterns required a
# leading space), so `rm raw/note.md` bypassed the immutability guard
# entirely. The filter is gone; startup cost belongs in llmw's import
# chain, not in a second copy of the decision rules.

llmw hook pretooluse 2>/dev/null || true
exit 0
