# llm-wiki

`${wiki_rel}/` is this project's persistent knowledge base.

## Work rules

- Before substantial work, run `llmw search "<topic>"` when prior context may matter; explicitly judge a task wiki-irrelevant when it does not.
- After source changes, decide whether durable knowledge changed. Record decisions, non-obvious fixes, and workarounds with `llmw write`/`edit`/`patch` and a meaningful `--reason`.
- Never edit `wiki/*.md` with native file tools; mutate it only through `llmw`. `raw/` is immutable.

## Entry quality

- **Mechanism, not narrative.** Record the relevant file/function call chain and order, not merely the outcome.
- Name the exact component or behavior; extend an existing subsystem page when appropriate.

## Capturing preferences

Record a stated preference, convention, or correction without asking first: put small always-apply rules in this file; put decisions with a why in the wiki. Briefly report what was recorded.

See the `llm-wiki` skill's reference and examples for command syntax.
