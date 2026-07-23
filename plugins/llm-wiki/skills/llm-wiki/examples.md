# LLM Wiki MCP — Worked Examples (Codex)

These call the `llm-wiki` MCP server's tools directly — there is no `llmw`
CLI surface on the Codex side (see reference.md). `llmw_search` and the
four mutation tools (`llmw_write`, `llmw_edit`, `llmw_patch`,
`llmw_archive`) are visible to this plugin's search/update soft gates;
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

Prefer `llmw_edit` over rewriting the whole page — no need to read the
full body back first if you already know the exact text to replace:

```
llmw_edit(
    path="wiki/decisions/auth-redesign.md",
    old="Session tokens move out of the auth middleware for compliance reasons.",
    new="Session tokens move out of the auth middleware for compliance reasons (policy v2).",
    reason="add policy version reference",
)
```

For a structural, multi-line change, `llmw_patch` takes a unified diff
instead — read the page first with `llmw_read(..., full=true)` so the
diff's context lines match exactly.

`llmw_write(force=true)` with the full new content is still the fallback
when the change touches most of the page (e.g. a rewrite) rather than a
targeted fix.

## Retiring a page

There's no delete — `llmw_archive(path=..., reason=...)` moves the page
to `wiki/archived/YYYY/MM/`, stamps archive frontmatter, and by default
leaves a `moved_to:` stub at the original path so inbound links still
resolve somewhere.

## Checking your work

`llmw_status()` again shows updated page counts and whether anything is
still flagged dirty. `llmw_lint()` catches broken links, orphan pages,
and missing frontmatter across the whole wiki; `llmw_related(target=...)`
surfaces pages worth cross-linking from the one you just touched.
