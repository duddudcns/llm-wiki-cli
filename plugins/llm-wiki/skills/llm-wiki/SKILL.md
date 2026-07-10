---
name: llm-wiki
description: Check, search, read, or update the project wiki and persistent project knowledge, even when the user never says llmw, MCP, tool, or skill. Trigger on natural requests such as "check the wiki", "update the wiki", "what did we decide?", "project history", "프로젝트 위키 확인", "위키 확인해봐", "위키 업데이트 해", "전에 뭐로 결정했지?", and equivalent wording.
---

# LLM Wiki Skill

Use the native `llm-wiki` MCP tools instead of loading the whole wiki into context. A request about "the wiki" means this project wiki unless context clearly identifies another wiki.

## Workflow

1. Call `llmw_status` to verify the project wiki.
2. For questions or checks, call `llmw_search`, then `llmw_read` for relevant results.
3. For an update, read the existing page first and call `llmw_write` with a concise audit `reason`; set `force` only when replacing an existing page is intended.
4. If no wiki exists and the user explicitly asked to create one, call `llmw_init`. Otherwise explain that initialization is needed.

## Safety

- Never modify `raw/`.
- Do not use generic file-edit tools on `wiki/*.md`; use the MCP tools so validation, locking, backups, and the audit log remain active.
- Every write requires a meaningful `reason`.

See [reference.md](reference.md) for commands and [examples.md](examples.md) for workflows.
