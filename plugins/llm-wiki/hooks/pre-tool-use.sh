#!/usr/bin/env bash
# PreToolUse hook: forwards the tool-call payload (via stdin) to `llmw
# hook codex-pretooluse` and prints whatever it returns. Matching to
# apply_patch/llmw_search/llmw_write is already done by hooks.json's
# matcher, so no branching on tool_name is needed here (unlike
# plugin/hooks/pre-tool-use.sh on the Claude Code side, which also has to
# watch Bash calls for a literal "llmw" substring since Claude has no
# equivalent per-tool matcher granularity for that case).
#
# `|| true` plus the trailing `exit 0` matter even though
# `llmw hook codex-pretooluse` itself never raises (cli.py catches
# everything internally): if `llmw` isn't on PATH yet — e.g. the first
# session before SessionStart's self-install has finished, or the install
# failed — the shell fails to spawn it at all (exit 127), outside that
# internal guarantee. Without this wrapper that failure was unguarded,
# unlike every other hook in this plugin.

llmw hook codex-pretooluse 2>/dev/null || true
exit 0
