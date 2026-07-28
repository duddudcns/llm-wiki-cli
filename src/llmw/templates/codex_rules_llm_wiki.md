# llm-wiki

`${wiki_rel}/` is this project's persistent knowledge base.

## Work rules

- Before substantial work, call `llmw_search` when prior context may matter; explicitly judge a task wiki-irrelevant when it does not.
- After source changes, decide whether durable knowledge changed. Record decisions, non-obvious fixes, and workarounds with `llmw_write`/`llmw_edit`/`llmw_patch` and a meaningful `reason`.
- Never use generic file-edit tools on `wiki/*.md`; mutate it only through MCP. `raw/` is immutable.

## Entry quality

- **Mechanism, not narrative.** Record the relevant file/function call chain and order, not merely the outcome.
- Name the exact component or behavior; extend an existing subsystem page when appropriate.

## Capturing preferences

Record a stated preference, convention, or correction without asking first: put small always-apply rules in this file; put decisions with a why in the wiki. Briefly report what was recorded.

See the `llm-wiki` skill's reference and examples for tool details.
