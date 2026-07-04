# Project layout, adopting an existing wiki, and Obsidian compatibility

**English** · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · [Français](../fr/project-layout.md)

## Project layout: classic vs. `ai-wiki/`

By default (`--layout classic`) `raw/`, `wiki/`, and `.llmw/` sit directly
in the project root. Pass `--layout ai-wiki` to nest them one level down
instead, keeping the root uncluttered:

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # same contents as the classic layout, nested
.claude/skills/llm-wiki/       # still scaffolds at the real project root
.claude-plugin/plugin.json     # still scaffolds at the real project root
```

Every command auto-detects which layout a project uses — it checks for
`.llmw/` directly in the project root first, then falls back to
`ai-wiki/.llmw`. Existing classic-layout projects need no migration.

If a project can't be auto-detected from the current directory (e.g. a
script running from elsewhere, or a non-standard checkout), point `llmw`
at it explicitly with `--root <path>` or the `LLMW_ROOT` environment
variable — either one is checked for both layouts, so a single value is
enough (no need to specify `raw/`/`wiki/`/`.llmw/` individually):

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Adopting an existing wiki

If `raw/`/`wiki/` (or an `ai-wiki/`-nested equivalent) already has real
content under its own conventions — e.g. a hand-rolled Karpathy-pattern
wiki that predates `llmw` — use `--adopt` instead of a plain `init`:

```bash
llmw init --adopt                  # or: llmw init --layout ai-wiki --adopt
```

`--adopt` creates `.llmw/` and `config.toml` on first run, but never writes
the default content files (`raw/README.md`, `wiki/index.md`,
`wiki/overview.md`, `wiki/log.md`) or the default taxonomy subfolders
(`entities/`, `concepts/`, `decisions/`, `syntheses/`, `projects/`,
`glossary/`, `archived/`, `sources/`) — **not even with `--force`** — so
pre-existing content at those paths is never touched or overwritten. Once
`config.toml` exists, `--force` never rewrites it back to defaults either,
so hand-tuned overrides for the adopted schema (see below) survive a
re-`init --adopt --force`. A plain `llmw init` (no `--adopt`) always
scaffolds those defaults, overwrites them on `--force`, and resets
`config.toml` to defaults on `--force` too; only use it against an empty
(or already llmw-managed) directory. Existing schema quirks (e.g. a
`last_updated` field instead of `created`/`updated`, or root-level
`index.md`/`log.md` files outside `wiki/`) are handled via
`.llmw/config.toml`'s `lint.required_frontmatter` and
`paths.extra_root_pages` — see below.

## Adapting llmw to an existing wiki

If a wiki already has its own conventions (different frontmatter fields,
top-level files living outside `wiki/`), point `llmw init --adopt` at its
root (see above) and adjust `.llmw/config.toml` rather than reorganizing
the wiki's files:

```toml
[paths]
# Extra individual Markdown files (relative to the project root) to index
# alongside wiki/**/*.md — e.g. a schema/index/log file kept outside wiki/.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Override which frontmatter keys `llmw lint` requires. Default is
# ["type", "status", "created", "updated"]; "updated" also accepts a
# `last_updated` key.
required_frontmatter = ["type", "status", "last_updated"]
```

No existing page needs to change — `llmw rebuild` picks up the new config
on the next run.

## Obsidian compatibility

`wiki/` is plain Markdown with YAML frontmatter and `[[wikilinks]]` — open
it directly as an Obsidian vault to get graph view, backlinks, and search
in a GUI, without giving up any of the CLI-driven agent workflow.

Link resolution specifically handles real-world Obsidian export quirks:

- `[[Page]]`, `[[Page|Alias]]`, `[[Page#Heading|Alias]]`, `[[#Heading]]`,
  `![[Embed]]` — full wikilink grammar.
- Path-like wikilink targets (`[[concepts/foo]]`) resolve relative to the
  **vault root** (`wiki/`), matching how Obsidian resolves them when you
  actually open `wiki/` as a vault — not just relative to the linking
  page's own folder.
- `related:` frontmatter is a first-class link source, same as inline
  wikilinks — both a plain path/title (`related: [wiki/concepts/foo]`, the
  convention some wikis used before adopting `llmw`) and Obsidian's own
  Properties-panel format (`related: ["[[Note]]"]`) resolve correctly.
- Markdown links with URL-encoded targets (`[Profile](Project%20Profile.md)`,
  common when a filename has spaces) are decoded before matching against
  on-disk pages.
- Relative wikilinks that point outside `wiki/` (e.g. `[[../notes/x]]`) are
  checked against the real filesystem — they're only reported as broken by
  `llmw lint` if the target genuinely doesn't exist anywhere in the
  project, not merely because they aren't an indexed wiki page.

**Where the graph deliberately diverges from Obsidian's own**: `related:`
edges and llmw's title-based wikilink resolution (`[[Exact Page Title]]`
resolving even when it doesn't match the filename) are both llmw
extensions with no Obsidian equivalent — Obsidian's own graph view won't
show those edges. Two pages with the same filename stem in different
folders also resolve ambiguously (first match wins) in both tools. Opening
`wiki/` in Obsidian gets you a real, useful graph on the same files, not a
pixel-identical one.
