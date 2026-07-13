# Contributing to `llmw`

**English** · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

See [installation.md](installation.md)'s "Working on `llmw`'s own code"
section to set up a dev environment; run `pytest` from there to run the
test suite.

## How the Claude Code skill works

`llmw init` writes a few files into `.claude/skills/llm-wiki/` in your
project. Claude Code picks these up automatically — there's no separate
install step needed. These files teach the AI when it should use `llmw`
and how, without needing to load all the detail every single time.

If you've already installed the Claude Code plugin from the marketplace,
add `--no-claude-plugin` when running `llmw init` to skip creating this
extra copy — otherwise you'd end up with two copies of the same
instructions, which is redundant and can confuse things.

`llmw init` also always writes `.claude/rules/llm-wiki.md`, regardless
of `--no-claude-plugin`. A Claude Code plugin manifest can ship hooks
and skills but has no way to ship `.claude/rules/` content, so this is
the only path that gets the search-before/update-after guidance loaded
into every session automatically, with no marketplace-plugin
alternative to deduplicate against.

`llmw init` writes the same guidance to `.codex/rules/llm-wiki.md` too,
every time, regardless of which plugin (or neither) you're actually
using — a Codex plugin manifest has the same "hooks and skills yes,
rules no" gap as Claude Code's. It's written unconditionally rather than
gated behind a Codex-specific flag: an unused rules file for a platform
nobody's using on this project is inert, while a team mixing Claude Code
and Codex gets both ready without extra setup.

## What this tool intentionally doesn't do (yet)

By design, this stays out of scope for now: connecting to AI models
directly, watching files for changes automatically, AI-powered semantic
search, reading PDF/Word files directly, a graphical app, or any
automatic merging/deleting/conflict-resolving of notes.
