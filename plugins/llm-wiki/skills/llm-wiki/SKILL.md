---
name: llm-wiki
description: Check, search, read, or update the project wiki and persistent project knowledge, even when the user never says llmw, MCP, tool, or skill. Trigger on natural requests such as "check the wiki", "update the wiki", "what did we decide?", "project history", "프로젝트 위키 확인", "위키 확인해봐", "위키 업데이트 해", "전에 뭐로 결정했지?", and equivalent wording.
---

# LLM Wiki Skill

Use the native `llm-wiki` MCP tools instead of loading the whole wiki into context. A request about "the wiki" means this project wiki unless context clearly identifies another wiki.

## Workflow

1. Call `llmw_status` to verify the project wiki.
2. For questions or checks, call `llmw_search`, then `llmw_read` for relevant results.
3. For an update, prefer `llmw_edit` (exact old/new text) or `llmw_patch` (unified diff) for a targeted change over rewriting the whole page; fall back to `llmw_write` with a concise audit `reason` when most of the page is changing, and set `force` only when replacing an existing page is intended. To retire a page, use `llmw_archive` — there is no delete. Mechanism, not narrative: if a result comes from a chain of steps not obvious from any single file (A calls B calls C to produce D), name the actual chain — which file/function, in what order — so a later "check the bug between C and D" can start at the right place instead of re-deriving the flow from scratch.
4. If no wiki exists and the user explicitly asked to create one, call `llmw_init`. Otherwise explain that initialization is needed.
5. Capture a stated preference or convention the moment it comes up, without waiting to be asked — not just a formal decision, a passing correction counts too. A small always-apply rule (comment style, naming, "always use X") goes into `.codex/rules/` as a plain file edit. A decision with a "why," or one-off history, goes into the wiki via `llmw_write`, same as step 3. Mention briefly what got recorded — that's not a request for permission, just context.

## Safety

- Never modify `raw/`.
- Do not use generic file-edit tools on `wiki/*.md`; use the MCP tools so validation, locking, backups, and the audit log remain active.
- Every write requires a meaningful `reason`.

See [reference.md](reference.md) for commands and [examples.md](examples.md) for workflows.
