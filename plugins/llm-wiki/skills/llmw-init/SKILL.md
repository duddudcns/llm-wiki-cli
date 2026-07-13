---
name: llmw-init
description: Explicit, user-invoked setup for this project's wiki. Use when asked to create, initialize, or set up a project wiki, including "create a project wiki", "프로젝트 위키 만들어", and equivalent wording, even without the names llmw, MCP, tool, or skill.
disable-model-invocation: false
---

# llmw init

Trigger only when the user's own message asks to create, initialize, or
set up a wiki (the phrasing this skill's `description` matches on) —
never as a side effect of other work, and never on your own initiative.
Unlike the Claude Code plugin, Codex has no hard technical gate here
(`disable-model-invocation: false`, since natural-language discovery is
how every skill in this plugin is reached, not slash commands); the
constraint is "did this message ask for wiki setup," not "was an exact
command typed."

## What to do

1. Check whether a wiki already exists (`raw/`, `wiki/`, `.llmw/`, or
   under `ai-wiki/`).
2. If one already exists, don't try to re-initialize it — `llmw_init`
   has no `--force`/`--adopt` override to offer over MCP (see
   reference.md's "not available over MCP yet" section). Tell the user
   it's already set up and ask what they actually want instead of
   retrying with different arguments.
3. Otherwise call the native `llmw_init` MCP tool with the user's
   requested path and `layout` (`classic` or `ai-wiki`).
4. Call `llmw_status`, then report what was created.

The main `llm-wiki` skill handles ongoing wiki work after setup.
