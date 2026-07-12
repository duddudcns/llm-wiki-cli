# llm-wiki (`llmw`) — this project's persistent knowledge base

This project keeps a searchable wiki at `${wiki_rel}/` — prior decisions,
known mistakes, project context — maintained through the `llmw` CLI. It
only pays off if it's actually consulted before work starts and kept
current after work finishes; both are judgment calls this file exists to
guide.

## Before starting real work

Run `llmw search "<topic>"` whenever a request could touch prior
context: a past decision, a known mistake, existing docs on the area
about to change. If the plugin's hooks are installed, the first real
source-file edit of a session that hasn't searched yet pauses once to
ask for exactly this — searching (or explicitly judging the task
wiki-irrelevant) clears it for the rest of the session.

## After finishing real work

Before ending a turn that changed something worth remembering — a
decision, a workaround, a fix for a subtle bug — record it with `llmw
write`/`edit`/`patch` (never edit `wiki/*.md` with native file-editing
tools; `raw/` is immutable). If the hooks are installed, a turn that
changed source without a matching wiki update pauses once with the same
reminder. Not every change needs an entry — routine edits with nothing
surprising don't — but making that call is the point, not skipping it.

## Commands

`llmw search "<query>"`, `llmw read <page>`, `llmw related <page>`,
`llmw write <page> --reason ... --stdin`, `llmw edit <page> --reason
... --old ... --new ...`, `llmw patch`, `llmw archive <page> --reason
...`. See the `llm-wiki` skill for the full reference.
