# How search works

**English** · [한국어](../ko/commands.md) · [日本語](../ja/commands.md) · [简体中文](../zh-Hans/commands.md) · [Español](../es/commands.md) · [Français](../fr/commands.md)

See the README's command table for the full list of commands. This page
just explains one thing in more detail: how `llmw search` decides what
counts as a match.

## Search tries three ways, from strictest to loosest

You can type a search the same way you'd ask a question — full sentences
are fine, you don't need to guess special keywords. Behind the scenes, it
tries up to three approaches, moving to the next one only if the previous
one found nothing at all — so a note that matches your search exactly will
never get pushed down the list by a note that only sort-of matches:

1. **Strict** — every word in your search has to appear somewhere in the note.
2. **Relaxed** — words that don't appear anywhere in any note (typos, or a
   slightly different form of a word) get quietly dropped; the rest of the
   words still have to match.
3. **Any match** — every word becomes optional, and results are just
   ranked by how well they match.

If you ask for `--json` output, it tells you which of the three ways
found the result: `{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Add `--strict` if you only ever want the first, strictest kind of match.

For Korean text: a search word that's a single Korean noun with a small
grammatical ending attached (like `스탯창을` or `포탈에서`) gets that ending
trimmed off before matching (to `스탯창`, `포탈`), so it can still find a
note that just uses the plain noun by itself. This only handles a small,
common list of endings, not every possible form of every word — it's
designed to never cause a note to be missed, just occasionally rank
things slightly differently than expected.
