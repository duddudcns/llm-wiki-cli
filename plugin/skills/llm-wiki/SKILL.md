---
name: llm-wiki
description: Search, read, and maintain this project's llmw wiki. Use for prior decisions, project history, source documents, backlinks, persistent knowledge, and before work the wiki may inform. Change wiki/*.md only through llmw; raw/ is immutable.
---

# LLM Wiki

Use `llmw`; do not load the whole wiki manually.

## Workflow

1. Run `llmw status --brief`, then `llmw search "<topic>" --limit 5` before non-trivial work when relevant.
2. Read only relevant results with `llmw read <path> --brief`; use `--full` only when needed.
3. Record durable knowledge after work. **Mechanism, not narrative:** name the file/function call chain and order. Prefer `llmw edit` for exact changes, `patch` for diffs, `write --force` for intended replacement, and `archive` over deletion; provide `--reason`.
4. Capture stated preferences or conventions without waiting to be asked: edit rules for small always-apply rules, or write a wiki entry for a decision with a why. Briefly report it.
5. Run `llmw lint --brief` after major wiki changes.

## Safety

- Never modify `raw/` or use native file-edit tools on `wiki/*.md`; use `llmw edit`/`write`/`patch`/`archive`.
- Keep output brief; use `--json` only for programmatic parsing.

See `reference.md` and `examples.md` for syntax and workflows.
