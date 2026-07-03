---
title: Auth Redesign
type: decision
status: active
created: 2026-07-03
updated: 2026-07-03
summary: Session tokens move out of the auth middleware for compliance reasons.
tags:
  - auth
  - compliance
sources:
  - wiki/sources/meeting-notes-2026-07-03.md
---

# Auth Redesign

## Summary

Session tokens move out of the auth middleware for compliance reasons.

## Key points

- The old auth middleware stored session tokens in a way that failed the
  new token-handling policy.
- Session storage moves to a dedicated component instead.

## Related

- [[Meeting Notes 2026-07-03]]
