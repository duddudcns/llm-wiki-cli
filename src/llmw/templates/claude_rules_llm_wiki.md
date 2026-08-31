# llm-wiki

`${wiki_rel}/` is this project's persistent knowledge base.

## Work rules

- Before substantial work, run `llmw search "<topic>"` when prior context may matter; explicitly judge a task wiki-irrelevant when it does not.
- After source changes, decide whether durable knowledge changed. Record decisions, non-obvious fixes, and workarounds with `llmw write`/`edit`/`patch` and a meaningful `--reason`.
- When a new entry *wholly* replaces an earlier one, write it with `--supersedes <old path>` rather than leaving the old page reading `status: active`. A partial overturn keeps the old page active — mark the superseded claim inline instead, since `status: superseded` says the whole page is no longer current.
- Bump `updated` when you re-checked a page's claims against current code. Adding a link, fixing a typo, or appending a dated section restates nothing, and stamping today's date on unverified claims is the error that causes wrong decisions.
- Never edit `wiki/*.md` with native file tools; mutate it only through `llmw`. `raw/` is immutable.

## Entry quality

- **Mechanism, not narrative.** Record the relevant file/function call chain and order, not merely the outcome, and list those files under `code:` in the frontmatter — the turn-end reminder uses it to name this page when they change.
- **Mechanism claims are dated.** When a page's `updated` predates the code you are changing, treat its file/function detail as a hypothesis to verify in source; the recorded *why* still holds.
- Name the exact component or behavior; extend an existing subsystem page when appropriate.

## Capturing preferences

Record a stated preference, convention, or correction without asking first: put small always-apply rules in this file; put decisions with a why in the wiki. Briefly report what was recorded.

See the `llm-wiki` skill's reference and examples for command syntax.
