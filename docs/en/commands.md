# Command details

**English** · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · [Español](../es/commands.md) · [Français](../fr/commands.md)

See the README's command reference table for the full list of commands and
their flags. This page covers the parts too deep for a one-line table entry.

## Search semantics

`llmw search` never requires keyword-only phrasing — a full natural-
language query is fine. It tries up to three tiers, only moving to the next
when the previous one finds nothing, so a full match can never be
outranked by a partial one:

1. **strict** — every query term required (AND).
2. **relaxed** — terms that can't match any indexed page at all (typos,
   verb conjugations) are dropped; the rest are still required.
3. **any** — every term becomes optional (OR), ranked by relevance.

`--json` output reports which tier answered the query:
`{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Pass `--strict` to disable the fallback tiers and only ever run tier 1.

Query terms that are a single Hangul word with a trailing particle (a 조사
— e.g. `스탯창을`, `포탈에서`) are stemmed to the bare noun (`스탯창`, `포탈`)
before matching, since SQLite FTS5's prefix search only matches a query
that is a prefix of the indexed word, not the other way around, so an
inflected query would otherwise miss a bare-noun page. This is a small
curated suffix list, not a full morphological analyzer — it won't stem verb
conjugations (that's what the relaxed tier is for) and will occasionally
strip a coincidental non-particle ending (e.g. `도로` → `도`); this is
always recall-safe (the stem is a prefix of the original word) at worst
adding minor ranking noise, never a missed page.
