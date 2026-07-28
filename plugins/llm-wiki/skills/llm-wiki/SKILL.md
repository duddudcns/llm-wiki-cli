---
name: llm-wiki
description: Check, search, read, or update the project wiki and persistent project knowledge. Trigger on "check the wiki", "update the wiki", "what did we decide?", "project history", "프로젝트 위키", "위키 확인", "위키 업데이트", "전에 뭐로 결정했지?", and equivalents.
---

# LLM Wiki

Use native `llm-wiki` MCP tools; do not load the whole wiki manually. “Wiki” means this project unless context says otherwise.

## Workflow

1. Call `llmw_status`; before relevant substantial work or questions, call `llmw_search`, then `llmw_read` for matching pages.
2. Record durable knowledge after work. **Mechanism, not narrative:** name the file/function call chain and order. Use `llmw_edit` for exact changes, `llmw_patch` for diffs, `llmw_write` for new or replacement pages, and `llmw_archive` instead of delete; every mutation needs a meaningful `reason`.
3. If no wiki exists, call `llmw_init` only when the user explicitly asks to create one; otherwise say initialization is needed.
4. Capture stated preferences or conventions without waiting to be asked: edit `.codex/rules/` for small always-apply rules, or write a wiki entry for a decision with a why. Briefly report it.

## Safety

- Never modify `raw/` or use generic file-edit tools on `wiki/*.md`; use MCP tools.

See [reference.md](reference.md) and [examples.md](examples.md).
