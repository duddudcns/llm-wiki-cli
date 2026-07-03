# LLM Wiki CLI — Worked Examples

## Starting a work session

```bash
llmw status --brief
llmw search "authentication redesign" --limit 5
llmw read wiki/decisions/auth-redesign.md --brief
```

## Ingesting a new source and writing a page

```bash
llmw ingest raw/inbox/meeting-notes-2026-07-03.md
llmw read wiki/sources/meeting-notes-2026-07-03.md --full
# agent reads the source, then fills in the draft:
cat <<'EOF' | llmw patch wiki/sources/meeting-notes-2026-07-03.md \
  --reason "summarized after reading raw source" --stdin
--- a/wiki/sources/meeting-notes-2026-07-03.md
+++ b/wiki/sources/meeting-notes-2026-07-03.md
@@ -10,4 +10,7 @@
 ## Agent summary

-TODO: The agent should read the source and summarize it.
+The team decided to move session storage out of the auth middleware to
+comply with the new token-handling policy. See [[Auth Redesign]].
EOF
```

## Recording a decision

```bash
cat <<'EOF' | llmw write wiki/decisions/auth-redesign.md \
  --reason "capture decision from 2026-07-03 meeting" --stdin
---
title: Auth Redesign
type: decision
status: active
created: 2026-07-03
updated: 2026-07-03
tags:
  - auth
  - compliance
sources:
  - wiki/sources/meeting-notes-2026-07-03.md
---

# Auth Redesign

## Summary

Session tokens move out of the auth middleware for compliance reasons.

## Related

- [[Meeting Notes 2026-07-03]]
EOF
```

## Fixing a small mistake with llmw edit

```bash
# A native Edit/Write on this file would be denied by the PreToolUse guard —
# use llmw edit instead of hand-writing a diff for a one-line fix.
llmw edit wiki/decisions/auth-redesign.md \
  --old "Session tokens move out of the auth middleware for compliance reasons." \
  --new "Session tokens move out of the auth middleware for compliance reasons (see policy v2)." \
  --reason "add policy version reference"
```

## Cleaning up after a merge

```bash
llmw archive wiki/concepts/old-auth-notes.md \
  --reason "merged into [[Auth Redesign]]"
llmw lint --brief
```

## Checking the knowledge graph

```bash
llmw graph build
llmw related "Auth Redesign" --limit 10
```
