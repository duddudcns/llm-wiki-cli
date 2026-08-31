---
name: llm-wiki
description: Search, read, and maintain this project's llmw wiki. Use for prior decisions, project history, source documents, backlinks, persistent knowledge, and before work the wiki may inform. Change wiki/*.md only through llmw; raw/ is immutable.
---

# LLM Wiki

Use `llmw`; do not load the whole wiki manually.

## Workflow

1. Run `llmw status --brief`, then `llmw search "<topic>" --limit 5` before non-trivial work when relevant.
2. Read only relevant results with `llmw read <path> --brief`; use `--full` only when needed. Mechanism claims are dated: when `updated` predates the code you are changing, verify the file/function detail in source — the recorded *why* still holds.
3. Record durable knowledge after work. **Mechanism, not narrative:** name the file/function call chain and order, and list those files under a `code:` frontmatter key so a later turn editing them is told this page exists. Prefer `llmw edit` for exact changes, `patch` for diffs, `write --force` for intended replacement, and `archive` over deletion; provide `--reason`. When a new page replaces an earlier decision *wholly*, pass `--supersedes <old path>` so the old one is marked in the same write; when it overturns only part of one, leave that page active and add an inline "Superseded in vX — see Y" at the claim itself. Bump `updated` when you re-checked a page's claims against current code, not merely because you touched the file.
4. Capture stated preferences or conventions without waiting to be asked: edit rules for small always-apply rules, or write a wiki entry for a decision with a why. Briefly report it.
5. Run `llmw lint --brief` after major wiki changes.

## Safety

- Never modify `raw/` or use native file-edit tools on `wiki/*.md`; use `llmw edit`/`write`/`patch`/`archive`.
- Keep output brief; use `--json` only for programmatic parsing.

See `reference.md` and `examples.md` for syntax and workflows.
