# Safety nets built into the plugin

**English** · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · [Français](../fr/hooks.md)

Installing the Claude Code plugin (see [installation.md](installation.md))
turns on four automatic safety features. None of them are required to use
`llmw` — they're just extra convenience on top of a tool that already
protects itself either way.

## Feature 1: stopping the AI from editing notes the wrong way

Nothing technically stops an AI assistant from ignoring this tool and just
editing a wiki note directly, the same way it edits any other file. If
that happens, you lose the automatic backup, the required "why did I
change this" note, and the check that the note is still written
correctly — and in practice, it does happen whenever some other
instruction is in charge and never mentions this tool.

When installed as the Claude Code plugin, a safety check catches this: if
the AI tries to directly edit a wiki note using its normal file-editing
tools, that edit is blocked (or, if you prefer, it just asks for
confirmation first), and it's told exactly which `llmw` command to use
instead — so it can immediately try again the right way instead of
getting stuck.

This check only ever looks at edits aimed at wiki notes (and at the
`raw/` folder, the untouched source material notes are built from) in a
project that uses this tool — everything else is left alone completely,
including just reading files.

You can turn this off or change how strict it is, per project, in
`.llmw/config.toml` — the same setting controls both the wiki notes and
the `raw/` folder:

```toml
[hooks]
wiki_guard = "deny"  # default: block the edit, and explain the right way to do it
# wiki_guard = "ask"   # ask for confirmation instead of blocking
# wiki_guard = "off"   # turn this check off for this project
```

On Windows, this check needs "Git Bash" installed to work. If it's
missing, the check just won't run — `llmw`'s own built-in safety rules
(a reason is required for every change, backups before edits, etc.) still
apply regardless.

## Feature 2: reminding the AI to check the wiki before every request

A wiki full of past decisions and mistakes is only useful if the AI
actually looks at it before starting new work — and left to its own
judgment, it won't always remember to. (This is the same problem people
run into with a hand-kept wiki in a note-taking app: you write things
down diligently, and the AI still goes and repeats a mistake you already
wrote down, because nothing reminded it to look.)

There's a small reminder shown at the start of every session too: "this
project has a wiki with N notes" if one already exists, or a one-line
"you should run `llmw init`" hint if it doesn't — so the AI knows about
this tool from the very first message, even in a brand-new project.

To help with that further, most messages you send also get a short
reminder attached: "this project has a wiki — search it first." This is
deliberately simple, on purpose: it doesn't try to guess whether your
message is actually related to something in the wiki by matching
keywords, since that kind of automatic guess can easily miss a note
that's just worded differently than your message. Instead, it just asks
the AI to go check, every time, and leaves the actual judgment (and the
actual searching) to the AI itself. (A very short message, like "ok" or
"thanks", skips the reminder — there's no real work starting there to
check the wiki against.)

On its own, that reminder is only a nudge — it never blocks or slows down
your request, and it can't stop the AI from proceeding either way. In
practice, seeing the identical line every turn also makes it easy to
tune out.

So there's a second, stronger layer underneath it: the first time in a
session the AI tries to edit an actual project file (not a wiki note
itself) without having searched yet, that edit is paused once and it's
asked to either search first or explicitly decide the task doesn't need
it. This fires at most once per session — the moment a search runs (even
a one-off one), or right after this single check, normal editing
resumes. It's still not a hard lock: the AI can confirm and proceed
without ever actually searching. What it buys you is a forced moment of
judgment instead of a reminder that's easy to scroll past.

```toml
[hooks]
search_gate = "ask"  # default: pause the first real edit of a session until searched or confirmed
# search_gate = "off"  # turn this check off for this project
```

## Feature 3: reminding the AI to update the wiki once the work is done

A wiki only stays useful if it keeps up with what actually happened —
and the same way an AI can forget to check the wiki before starting,
it can just as easily finish real work and never write any of it down,
even with the best intentions going in.

To catch that, `llmw` keeps track, per session, of whether project files
changed since the wiki was last touched (via `llmw write`/`edit`/
`patch`/`archive`). If the AI tries to end its turn with that still true,
it's stopped once and asked to either record what changed and why, or
explicitly decide this particular change doesn't warrant a wiki update.
Like the search check above, this fires at most once per turn — Claude
Code's own loop protection guarantees it can never turn into a stuck
retry loop — so it nudges again at the end of the *next* turn if the
wiki still hasn't caught up, rather than nagging on every single message.

```toml
[hooks]
update_gate = "ask"  # default: pause once per turn when source changed but the wiki didn't
# update_gate = "off"  # turn this check off for this project
```

## Feature 4: keeping the command-line tool itself up to date

The plugin includes a small helper program, but the real work is done by
a separate copy of `llmw` installed on your computer. Updating the plugin
through the marketplace does **not** automatically update that separate
copy — left alone, you could end up running an outdated version without
realizing it.

To prevent that, a quick check runs at the start of every session: it
compares the version of `llmw` installed on your computer to the version
the plugin expects. If they don't match — including if `llmw` isn't
installed at all yet — it automatically reinstalls the correct version
for you. So updating the plugin also keeps the command-line tool in sync,
with nothing extra for you to do.

When the versions already match, this check is just a quick, local check
with no internet connection needed — the actual reinstall only happens
on the rare occasion something is out of sync.
