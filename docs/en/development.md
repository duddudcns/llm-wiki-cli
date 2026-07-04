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

## What this tool intentionally doesn't do (yet)

By design, this stays out of scope for now: connecting to AI models
directly, watching files for changes automatically, AI-powered semantic
search, reading PDF/Word files directly, a graphical app, or any
automatic merging/deleting/conflict-resolving of notes.
