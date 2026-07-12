# llm-wiki — this project's persistent knowledge base

This project keeps a searchable wiki at `${wiki_rel}/` — prior decisions,
known mistakes, project context — through the `llm-wiki` MCP tools. It
only pays off if it's actually consulted before work starts and kept
current after work finishes; both are judgment calls this file exists to
guide.

## Before starting real work

Call `llmw_search` whenever a request could touch prior context: a past
decision, a known mistake, existing docs on the area about to change. If
the plugin's hooks are installed, the first real file edit of a session
that hasn't searched yet pauses once to ask for exactly this — searching
(or explicitly judging the task wiki-irrelevant) clears it for the rest
of the session.

## After finishing real work

Before ending a turn that changed something worth remembering — a
decision, a workaround, a fix for a subtle bug — record it with
`llmw_write` and a meaningful `reason` (never edit `wiki/*.md` with
generic file-edit tools; `raw/` is immutable). If the hooks are
installed, a turn that changed source without a matching wiki update
pauses once with the same reminder. Not every change needs an entry —
routine edits with nothing surprising don't — but making that call is
the point, not skipping it.

## Capturing preferences and conventions as they come up

Treat a coding convention, style preference, or correction the user
states during ordinary work — even briefly, without "remember this" or
"update the wiki" — as worth recording, not as a one-off instruction to
forget after this turn:

- **Small, always-apply conventions** (comment style, naming, "always
  use X for Y") — add or update a line directly in this file, a plain
  file edit, so every future session picks it up automatically.
- **Decisions with a "why," or one-off history** — write it to the wiki
  via `llmw_write`, same as above.

Do this without asking first. Asking turns a two-second update into a
round-trip the user has to approve, and the point is that this project
keeps organizing itself as it's used, not that someone has to remember
to say "add this to rules" every time. A brief one-line mention
afterward is context, not a permission request.

## Tools

`llmw_status`, `llmw_search`, `llmw_read`, `llmw_write`, `llmw_init`. See
the `llm-wiki` skill for the full workflow.
