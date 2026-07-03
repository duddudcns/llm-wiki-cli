# llmw

Headless Obsidian-like LLM Wiki CLI for AI agents.

## Why

MCP tools are convenient, but tool schemas and long instructions consume
context on every turn. `llmw` takes a different approach: a small,
deterministic CLI plus a Claude Code skill. The agent calls the wiki only
when it needs to, and the CLI itself never calls a model — it only
indexes, searches, and validates.

## Concepts

- **Karpathy LLM Wiki** — `raw/` holds immutable source material; `wiki/`
  is a persistent knowledge layer that an AI agent writes and maintains;
  this is not ordinary RAG, the wiki is a compounding artifact.
- **Obsidian-style wikilinks** — `[[Page]]`, `[[Page|Alias]]`,
  `[[Page#Heading]]`, `![[Embed]]`, backlinks, tags, YAML frontmatter.
  `wiki/` is a valid Obsidian vault; open it there if you want a human
  visual IDE on top of the same files.
- **Markdown as source of truth** — `.llmw/index.sqlite` and
  `.llmw/graph.json` are derived, rebuildable data. `llmw rebuild`
  regenerates both from `wiki/*.md` alone.
- **AI agent writes the wiki; the CLI indexes and validates it** — search
  (SQLite FTS5), backlinks, related-page scoring, and lint are all
  deterministic, rule-based, and model-free. Summarizing sources, writing
  pages, and deciding what to archive is the agent's job.

## Quickstart

```bash
# from a clone of this repo
pip install -e .
# (a PyPI release / `uv tool install llmw` will work the same way once published)

mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` scaffolds:

```text
raw/                          # immutable source material
wiki/                         # agent-maintained knowledge layer
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # derived index/cache/backups/locks (rebuildable)
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # optional plugin metadata for this project
```

## Agent workflow

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## Command reference

All commands accept `--json` for machine-parseable output; most reads
default to a brief, context-cheap view (`--full`/`--no-brief` for more).

| Command | Purpose |
|---|---|
| `llmw init [--force]` | Scaffold `raw/`, `wiki/`, `.llmw/`, and the Claude Code skill/plugin |
| `llmw status [--brief\|--json]` | Page counts, broken links, orphans, last indexed time, dirty pages |
| `llmw rebuild` | Full re-index of `wiki/**/*.md` from scratch |
| `llmw index [--changed\|--all]` | Incremental (default) or full re-index |
| `llmw search "<query>" [--limit N] [--type T]` | SQLite FTS5 search over title/summary/body |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Look up a page; brief shows title/type/summary/key points/links/backlink count |
| `llmw links <target>` | Outgoing links, with broken status |
| `llmw backlinks <target>` | Incoming links |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Deterministic related-page candidates (no model calls) |
| `llmw ingest <raw/...>` | Register a `.md`/`.txt` source as a `wiki/sources/<slug>.md` draft |
| `llmw write <path> --reason "..." --stdin [--force]` | Create a new wiki page from stdin |
| `llmw patch <path> --reason "..." --stdin` | Apply a unified diff to an existing page (backs up first, rolls back on failure) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Move a page to `wiki/archived/YYYY/MM/`, stamp archive frontmatter, log the change |
| `llmw lint [--brief\|--json]` | Broken links, orphans, duplicate titles/aliases, missing/invalid frontmatter, dangling raw refs, archived-page links — reports only, never auto-fixes |
| `llmw health [--brief]` | System checks: config, index db, schema version, directories, locks |
| `llmw graph build` / `llmw graph export --format json\|html` | Regenerate/export the link graph |

## Safety rules

- `raw/` is immutable. `write`/`patch`/`archive` refuse any path under it.
- Every `write`/`patch`/`archive` requires `--reason`, recorded in
  `wiki/log.md` and the `log_entries` table.
- There is no `delete` — use `archive`. The default keeps a tombstone stub
  at the original path pointing to the new location.
- `patch` backs up the file before applying a unified diff, and leaves
  the original untouched if the diff doesn't apply cleanly (context
  mismatch).
- A simple advisory lock (`.llmw/locks/write.lock`) guards against two
  `llmw` processes mutating the wiki at the same time.

## Claude Code skill

`llmw init` writes `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}`
into the project. Claude Code auto-discovers this as a plain skill — no
install step. It tells the agent when to reach for `llmw`, the core
search-first workflow, and points to `reference.md`/`examples.md` for
full detail so the always-loaded `SKILL.md` stays short.

## Distributing `llmw` as an installable Claude Code plugin

The `plugin/` directory in this repo is a separate, standard Claude Code
plugin package (`plugin/.claude-plugin/plugin.json` + `plugin/skills/llm-wiki/`
+ `plugin/bin/llmw`), for sharing this tool via a marketplace or
`--plugin-dir` rather than per-project `llmw init`. `plugin/bin/llmw` is a
thin dispatcher; it still expects the `llmw` Python package to be
installed in the active environment.

## Obsidian compatibility

`wiki/` is plain Markdown with YAML frontmatter and `[[wikilinks]]` — open
it directly as an Obsidian vault to get graph view, backlinks, and search
in a GUI, without giving up any of the CLI-driven agent workflow.

## Development

```bash
pip install -e ".[dev]"
pytest
```

MVP scope deliberately excludes: an MCP server, daemon/watch mode,
embedding/vector search, direct PDF/DOCX parsing, an Obsidian plugin, a
web UI, and any auto-merge/auto-delete/contradiction-detection logic —
see the project's implementation notes for the full list and rationale.
