# Development

**English** · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

See [installation.md](installation.md)'s "Local clone, editable install"
section to set up a dev environment; `pytest` runs the test suite from
there.

## Claude Code skill

`llmw init` writes `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}`
into the project. Claude Code auto-discovers this as a plain skill — no
install step. It tells the agent when to reach for `llmw`, the core
search-first workflow, and points to `reference.md`/`examples.md` for full
detail so the always-loaded `SKILL.md` stays short.

If the llm-wiki Claude Code plugin is already installed from the
marketplace, pass `--no-claude-plugin` to skip this project-local copy —
otherwise the project ends up with two copies of the same skill (the
marketplace plugin's, and this one), which is redundant and can be
confusing when Claude Code loads both.

## MVP scope

Deliberately excludes: an MCP server, daemon/watch mode, embedding/vector
search, direct PDF/DOCX parsing, an Obsidian plugin, a web UI, and any
auto-merge/auto-delete/contradiction-detection logic.
