---
name: llmw-init
description: Explicit, user-invoked setup for this project's wiki. Use when asked to create, initialize, or set up a project wiki, including "create a project wiki", "프로젝트 위키 만들어", and equivalent wording, even without the names llmw, MCP, tool, or skill.
disable-model-invocation: false
---

# llmw init

User-invoked only. Do not initialize a wiki on your own initiative.

## What to do

1. Check whether a wiki already exists (`raw/`, `wiki/`, `.llmw/`, or under `ai-wiki/`).
2. If one exists, ask whether to use `--force`, `--adopt`, or a different `--layout`.
3. Call the native `llmw_init` MCP tool with the user's requested path and layout.
4. Call `llmw_status`, then report what was created.

The main `llm-wiki` skill handles ongoing wiki work after setup.
