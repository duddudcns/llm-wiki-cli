# LLM Wiki MCP — Worked Examples (Codex)

These call the `llm-wiki` MCP server's tools directly — there is no `llmw`
CLI surface on the Codex side (see reference.md). Only the search and
write calls are visible to this plugin's search/update soft gates;
`apply_patch` on non-wiki source files is what triggers the "you haven't
searched yet" reminder.

## Starting a work session

1. `llmw_status()` — confirm the wiki exists and see dirty/orphan counts.
2. `llmw_search(query="authentication redesign", limit=5)` — check for
   prior context before starting non-trivial work.
3. `llmw_read(target="wiki/decisions/auth-redesign.md")` — read anything
   relevant the search turned up.

## Recording a decision

Call `llmw_write` with the full page content and a concise `reason`:

```
llmw_write(
    path="wiki/decisions/auth-redesign.md",
    reason="capture decision from 2026-07-03 meeting",
    content="""---
title: Auth Redesign
type: decision
status: active
created: 2026-07-03
updated: 2026-07-03
tags:
  - auth
  - compliance
sources:
  - wiki/sources/meeting-notes-2026-07-03.md
---

# Auth Redesign

## Summary

Session tokens move out of the auth middleware for compliance reasons.

## Related

- [[Meeting Notes 2026-07-03]]
"""
)
```

## Fixing a small mistake

There's no exact-string `edit` or diff-based `patch` tool over MCP —
`llmw_write` always replaces the whole page. Read the page first, make
the change in the full content, then write it back with `force=true`:

1. `llmw_read(target="wiki/decisions/auth-redesign.md", full=true)` —
   get the current content.
2. `llmw_write(path="wiki/decisions/auth-redesign.md", force=true,
   reason="add policy version reference", content=<full page with the
   one line changed>)`.

## Checking your work

`llmw_status()` again shows updated page counts and whether anything is
still flagged dirty. There's no `lint`/`graph`/`related` MCP tool to
follow up with (see reference.md) — a search for the page's title/topic
is the practical way to spot-check that it's discoverable.
