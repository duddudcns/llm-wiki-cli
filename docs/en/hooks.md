# Safety nets built into the plugin

**English** · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · [Français](../fr/hooks.md)

Installing the Claude Code plugin (see [installation.md](installation.md))
turns on three automatic safety features. None of them are required to use
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

This is only a reminder — it never blocks or slows down your request,
and it can't stop the AI from proceeding either way. It's a nudge, not a
gate.

## Feature 3: keeping the command-line tool itself up to date

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
