# Keeping notes from quietly going out of date

**English** · [한국어](../ko/staleness.md) · [日本語](../ja/staleness.md) · [简体中文](../zh-Hans/staleness.md) · [Español](../es/staleness.md) · [Français](../fr/staleness.md)

The most useful notes are the ones that say how something actually works —
which file calls which function, in what order. Those are also the first
notes to go wrong, because the code keeps moving and the note doesn't.

The problem isn't that a note gets old. It's that an old note looks
exactly like a fresh one, so the AI reads it, believes it, and makes a
decision on information that stopped being true weeks ago. That's worse
than having no note at all.

`llmw` doesn't try to guess which notes have gone stale — see
[Why it doesn't just check the code](#why-it-doesnt-just-check-the-code)
at the end. Instead it does three simpler things.

## 1. Search and read tell you how old a note's claims are

Results now show the note's title and when it was last brought up to date:

```
1. wiki/decisions/retry-budget.md
   title: Retry budget moves into the uploader (v0.1.18)
   updated: 2026-07-13 (49d ago)
   summary: ...
```

If `llmw` has seen the note's body change since the date the note claims,
you'll see both:

```
   updated: 2026-07-13 (49d ago, body changed 2026-08-31)
```

That gap means somebody rewrote what the note says and didn't update its
date — so the note may describe something newer than it claims. Showing
both numbers is deliberate: picking one would quietly turn "when someone
last changed this" into "when someone last checked this was still true",
and those are not the same thing.

**The body, not the file.** Marking a note replaced, adding a `code:`
list, or fixing a tag rewrites the file without changing a word of what
the note says — and you're told *not* to touch the date for those. An
earlier version of this compared file timestamps instead, and one
housekeeping pass across this project's own wiki left a permanent "this
changed" warning on 21 of its 31 notes, none of which had. A warning that
is usually wrong is one you stop reading.

`llmw read <path> --full` is left alone — it prints the note and nothing
else, because that exact text is what gets used to make careful edits.

## 2. Replacing an old decision marks it, in one step

When a new note overturns an older one, write it with `--supersedes`:

```bash
llmw write wiki/decisions/retry-in-the-uploader.md \
  --reason "the uploader owns retries now" \
  --supersedes wiki/decisions/retry-in-the-client.md --stdin
```

The old note is marked `status: superseded` with a pointer to the new
one, and searches show it right next to the path:

```
1. wiki/decisions/retry-in-the-client.md [superseded -> wiki/decisions/retry-in-the-uploader.md]
```

Both notes are backed up and logged, and if the note you named doesn't
exist, nothing is written at all.

The reason this is one command rather than two: writing the new note is
the part people remember, and going back to mark the old one is the part
they forget. A note still marked "active" months after it was reversed is
exactly what causes a wrong decision later.

The old note keeps its body. A reversed decision still explains *why* it
was made, and that reasoning usually outlives the decision itself — so
superseded notes are marked, not hidden or pushed down the results.

## 3. Notes can say which files they describe

Add a `code:` list to a note's frontmatter:

```yaml
---
title: Retry budget moves into the uploader
type: decision
status: active
created: 2026-08-31
updated: 2026-08-31
code:
  - src/uploader.py
  - src/retry.py
---
```

Then, when the AI finishes a turn in which it edited one of those files,
the end-of-turn reminder names the note:

```
Source changed: record durable knowledge with `llmw write`/`edit`/`patch`...
Pages describing what changed: wiki/decisions/retry-budget.md
```

This is the difference between "remember to update the wiki" and "this
specific note is about the file you just changed." The AI still has the
change fresh in mind at that moment, which is the only time updating the
note is cheap.

These paths are relative to your project folder. They are not links — a
note listing `src/uploader.py` won't be reported as having a broken link,
and `llmw lint` won't complain about them.

## Small reminders while you write

`llmw write`, `edit`, and `patch` print a short note (to the error
stream, so it never mixes into output something else is reading) when:

- a note is missing frontmatter fields your project requires, or
- you changed a note's body but left its `updated` date alone.

Neither stops the write. They're reminders, not rules — you may well be
fixing a typo, in which case there is nothing to restate. The second one
stays quiet if the note was already brought up to date today.

**`updated` is never changed for you.** If it were, fixing a typo would
make a stale note look freshly verified — and a note that looks fresher
than it is causes exactly the wrong decision this whole feature exists to
prevent. A note that looks *older* than it is only costs you a quick look
at the code. When in doubt, the display should make you trust a note
less, not more.

## Why it doesn't just check the code

The obvious idea is to compare each note against its files in version
control and flag the ones whose code changed more recently. That was
built and measured on this project's own wiki, and it doesn't work: **17
of 24 notes were flagged**, almost all of them by a single refactor that
moved some imports around and changed the meaning of nothing.

Narrowing it to individual functions doesn't help either — that same
refactor genuinely edited the insides of the functions the notes named.
The underlying reason is simple: a file changing is not evidence that a
sentence about it became false. Renaming things, splitting a function,
tidying imports — all of them trip the check, none of them make a note
wrong.

A check that's wrong two times out of three gets ignored, and once it's
ignored it's worse than nothing, because it makes the wiki look supervised
when it isn't. So `llmw` shows you the dates and lets you judge, marks
what someone explicitly said was replaced, and points at the notes that
say they're about the file you just touched. All three are things it can
actually know.
