---
name: llm-wiki
description: Search, read, and maintain this project's llmw wiki (raw/ + wiki/ + .llmw/). Use when the task involves project history, prior decisions, source documents, backlinks, or persistent knowledge — and before answering anything the wiki may already answer. All wiki/*.md changes MUST go through llmw write/edit/patch (never native file-edit tools); raw/ is immutable.
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
- You finish a task that creates stable knowledge worth remembering —
  including a preference, convention, or correction the user stated in
  passing, not just a formal decision

## Core workflow

1. Run `llmw status --brief`.
2. Search first: `llmw search "<query>" --limit 5`. Natural-language queries
   are fine — search tries strict match first, then relaxes automatically;
   `mode`/`dropped_tokens` in `--json` output say which tier answered it.
3. Read only relevant pages: `llmw read <path> --brief`.
4. Use `--full` only when brief output is insufficient.
5. Update wiki pages when stable knowledge changes.
   Mechanism, not narrative: if a result comes from a chain of steps not
   obvious from any single file (A calls B calls C to produce D), name
   the actual chain — which file/function, in what order — so a later
   "check the bug between C and D" can start at the right place instead
   of re-deriving the flow from scratch.
6. Prefer `llmw edit` for a small, exact-text change; `llmw patch` for a
   structural (multi-line/context) diff; `llmw write --force` to replace a
   whole page.
7. Prefer `llmw archive` over deleting a page.
8. Run `llmw lint --brief` after major wiki changes.
9. Capture a stated preference or convention the moment it comes up,
   without waiting to be asked: a small always-apply rule (comment
   style, naming, "always use X") goes into `.claude/rules/` as a plain
   file edit — not wiki-guarded, no `llmw` wrapper needed; a decision
   with a "why," or one-off history, goes into the wiki via `llmw
   write`/`edit`, same as step 5. Mention briefly what got recorded —
   that's not a request for permission, just context.

## Output discipline

Keep CLI outputs brief. Do not dump the full wiki into context. Use
`--json` only when you need to parse fields programmatically.

## Important

- ⛔ Never use your built-in Edit/Write/NotebookEdit tools on `wiki/*.md`
  or anything under `raw/` — a PreToolUse guard denies it (unless the
  project opted out via `.llmw/config.toml`). Use `llmw edit`/`write`/
  `patch`/`archive` instead; the denial message names the exact command.
- Do not modify files under `raw/` — `llmw write`/`patch`/`archive` will
  refuse and so should you.
- The `wiki/` layer is agent-maintained; you are expected to write to it.
- All destructive or structural changes need a `--reason`.
- Full command reference: see `reference.md` in this skill folder.
- Worked examples: see `examples.md` in this skill folder.
