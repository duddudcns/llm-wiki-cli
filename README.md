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

## Install

**Recommended: Claude Code plugin** — no separate `pip`/`uv`/`pipx` step:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

This also installs hooks that keep the CLI itself in sync automatically and
keep agents from bypassing it — see [docs/hooks.md](docs/hooks.md).

Want the standalone CLI directly instead (scripting, CI, another editor),
or to manage upgrades yourself? See
[docs/installation.md](docs/installation.md) for the full uv/pipx/pip/dev
install matrix, split by Windows/macOS/Linux. The two don't conflict — you
can install both.

## Quickstart

```bash
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

Pass `--layout ai-wiki` to nest `raw/`/`wiki/`/`.llmw/` under an `ai-wiki/`
folder instead (auto-detected by every command afterward), and `--adopt` to
point `llmw` at a wiki that already has real content under its own
conventions without scaffolding over it — see
[docs/project-layout.md](docs/project-layout.md).

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
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Scaffold `raw/`, `wiki/`, `.llmw/` (nested under `ai-wiki/` with `--layout ai-wiki`), and (by default) the Claude Code skill/plugin. `--adopt` skips default content/taxonomy scaffolding and protects `config.toml` from `--force`, to preserve existing wiki content and its config overrides |
| `llmw status [--brief\|--json]` | Page counts, broken links, orphans, last indexed time, dirty pages |
| `llmw rebuild` | Full re-index of `wiki/**/*.md` from scratch |
| `llmw index [--changed\|--all]` | Incremental (default) or full re-index |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | SQLite FTS5 search over title/summary/body — see [docs/commands.md](docs/commands.md) for search semantics |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Look up a page; brief shows title/type/summary/key points/links/backlink count |
| `llmw links <target>` | Outgoing links, with broken status |
| `llmw backlinks <target>` | Incoming links |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Deterministic related-page candidates (no model calls) |
| `llmw ingest <raw/...>` | Register a `.md`/`.txt` source as a `wiki/sources/<slug>.md` draft |
| `llmw write <path> --reason "..." --stdin [--force]` | Create a new wiki page from stdin |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Exact-string replace in an existing page (same semantics as a native Edit tool) |
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

## Documentation

| Doc | Covers |
|---|---|
| [docs/installation.md](docs/installation.md) | Full standalone-CLI install matrix (Windows/macOS/Linux), updating, uninstalling |
| [docs/hooks.md](docs/hooks.md) | The Claude Code plugin's `PreToolUse` wiki-guard and self-healing `SessionStart` version-sync hook |
| [docs/commands.md](docs/commands.md) | Search semantics (3-tier fallback, Korean particle stemming) |
| [docs/project-layout.md](docs/project-layout.md) | Classic vs. `ai-wiki/` layout, `--root`/`LLMW_ROOT`, `--adopt`, adapting `llmw` to an existing wiki's conventions, Obsidian compatibility notes |
| [docs/development.md](docs/development.md) | Dev setup, the Claude Code skill, MVP scope |

## License

MIT — see [LICENSE](LICENSE).
