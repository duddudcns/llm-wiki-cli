#!/usr/bin/env bash
# SessionStart hook: install `llmw` if it's missing, or reinstall it
# (pinned to this exact plugin release) if the installed CLI has drifted
# out of lockstep with the plugin. Never fails the session — every step
# that can fail is guarded so this always falls through to the final
# `llmw hook session-start` call (or exits 0 if that's unavailable too).
#
# Why this exists: llmw ships through three independent install paths at
# once (standalone pip/uv/pipx, this plugin, and this hook's self-install)
# with no single source of truth, so updating the plugin via the
# marketplace does NOT by itself update the standalone `llmw` binary a
# session actually shells out to. See the dogfood wiki's
# multi-location-version-sync.md / ai-wiki-nested-layout.md for history.

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
plugin_version_file="$plugin_root/.claude-plugin/plugin.json"

plugin_version="unknown"
if [ -f "$plugin_version_file" ]; then
  for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
      plugin_version=$("$py" -c \
        "import json,sys; print(json.load(open(sys.argv[1]))['version'])" \
        "$plugin_version_file" 2>/dev/null) || plugin_version="unknown"
      break
    fi
  done
fi

installed_version=$(llmw --version 2>/dev/null) || installed_version="none"

# Only act when we know what version the plugin expects and it disagrees
# with what's installed — covers both "not installed at all"
# (installed_version stays "none") and "installed but stale/ahead" in one
# check.
if [ "$plugin_version" != "unknown" ] && [ "$installed_version" != "$plugin_version" ]; then
  repo_ref="git+https://github.com/duddudcns/llm-wiki-cli.git@v${plugin_version}"
  if command -v uv >/dev/null 2>&1; then
    uv tool install -q --force "$repo_ref" 2>/dev/null || true
  else
    pip install -q --user --force-reinstall "$repo_ref" 2>/dev/null || true
  fi
fi

llmw hook session-start 2>/dev/null || true
exit 0
