---
name: llmw-init
description: Explicit, user-invoked setup for this project's llmw wiki (raw/, wiki/, search index). Never triggers automatically — only runs when the user directly asks for it or types /llm-wiki:llmw-init.
disable-model-invocation: true
---

# llmw init

User-invoked only. Do not run `llmw init` on your own initiative elsewhere —
before a wiki exists there's nothing for the main `llm-wiki` skill to search
or read, so this is the one action a human needs to trigger explicitly
instead of leaving it to model judgment.

## What to do

1. Check whether a wiki already exists (`raw/`, `wiki/`, `.llmw/` at the
   project root, or nested under `ai-wiki/`).
2. If one already exists, don't silently re-run — ask whether the user
   wants `--force` (reset), `--adopt` (bring an existing non-llmw wiki
   under llmw without scaffolding over its content), or a different
   `--layout` (`classic` vs `ai-wiki`).
3. Run `llmw init` with whatever flags apply (`$ARGUMENTS` if the user
   passed any after the command).
4. Report briefly what was created, then point to `llmw status --brief`
   as the next step.

Once the wiki exists, ongoing search/read/write work is handled by the
main `llm-wiki` skill — this skill's job ends after setup.
