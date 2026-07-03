---
name: llm-wiki
description: Use the local LLM Wiki CLI (`llmw`) when project history, prior decisions, source documents, wiki search, backlinks, graph relationships, or persistent knowledge are needed.
---

# LLM Wiki Skill

Use `llmw` instead of reading the whole wiki manually.

## When to use

Use this skill when:

- Starting non-trivial work in this project
- The user references prior decisions, setup, failures, documents, requirements, or project history
- You need to ingest a source document
- You need to answer from persistent project knowledge
- You are about to make or revise an architectural/design decision
- You finish a task that creates stable knowledge worth remembering

## Core workflow

1. Run `llmw status --brief`.
2. Search first: `llmw search "<query>" --limit 5`.
3. Read only relevant pages: `llmw read <path> --brief`.
4. Use `--full` only when brief output is insufficient.
5. Update wiki pages when stable knowledge changes.
6. Prefer `llmw patch` over rewriting a full page.
7. Prefer `llmw archive` over deleting a page.
8. Run `llmw lint --brief` after major wiki changes.

## Output discipline

Keep CLI outputs brief. Do not dump the full wiki into context. Use
`--json` only when you need to parse fields programmatically.

## Important

- Do not modify files under `raw/` — `llmw write`/`patch`/`archive` will
  refuse and so should you.
- The `wiki/` layer is agent-maintained; you are expected to write to it.
- All destructive or structural changes need a `--reason`.
- Full command reference: see `reference.md` in this skill folder.
- Worked examples: see `examples.md` in this skill folder.
