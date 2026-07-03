---
title: Overview
type: note
status: active
created: 2026-07-03
updated: 2026-07-03
summary: How this wiki is organized and maintained.
---

# Overview

## Summary

This wiki follows the Karpathy LLM Wiki pattern: `raw/` holds immutable
source material, `wiki/` is a persistent knowledge layer written and
maintained by an AI agent, and the `llmw` CLI provides deterministic
search, backlinks, graph, and lint over that layer without calling any
model itself.

## Key points

- Raw sources under `raw/` are never modified.
- Pages under `wiki/` are owned by the AI agent, using double-bracket
  wikilinks to connect related pages.
- `llmw` indexes, searches, and validates the wiki; it does not summarize
  or write content itself.
- Prefer `llmw patch` over rewriting a whole page, and `llmw archive`
  over deleting a page.

## Related

- [[Index]]
