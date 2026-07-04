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

## Installation

### Prerequisites

`llmw` needs **Python 3.11 or later**. Check what you have:

```bash
python3 --version   # macOS/Linux
python --version    # Windows
```

Don't have 3.11+ yet?

| Platform | Command |
|---|---|
| macOS (Homebrew) | `brew install python@3.12` |
| Windows (winget) | `winget install Python.Python.3.12` |
| Windows (installer) | download from [python.org/downloads](https://www.python.org/downloads/) |
| Ubuntu/Debian | `sudo apt install python3.12 python3.12-venv` |
| Fedora | `sudo dnf install python3.12` |

`llmw` is not on PyPI yet, so it installs straight from this repo rather
than a package index. **This repo is currently private** — installing it
(any method below) needs your own authenticated `git` (e.g. already
logged in via `gh auth login`, or an SSH key on your GitHub account);
anyone without repo access will get a fetch error, not a partial install.

### Install `llmw`

Pick one. All of these give you a global `llmw` command without touching
any other Python project's dependencies.

**[uv](https://docs.astral.sh/uv/) (recommended — fast, no separate pipx install needed):**

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

**[pipx](https://pipx.pypa.io/):**

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

**plain pip** (installs into whatever Python environment is currently active — use a venv unless you know you want it global):

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

**Local clone, editable install (for contributing to `llmw` itself):**

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # should show all tests passing
```

### Verify

```bash
llmw --version
llmw --help
```

### Updating

```bash
uv tool upgrade llmw           # if installed via uv
pipx upgrade llmw              # if installed via pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # plain pip
```

### Uninstalling

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```

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
| `llmw init [--force] [--no-claude-plugin]` | Scaffold `raw/`, `wiki/`, `.llmw/`, and (by default) the Claude Code skill/plugin |
| `llmw status [--brief\|--json]` | Page counts, broken links, orphans, last indexed time, dirty pages |
| `llmw rebuild` | Full re-index of `wiki/**/*.md` from scratch |
| `llmw index [--changed\|--all]` | Incremental (default) or full re-index |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | SQLite FTS5 search over title/summary/body — see [Search semantics](#search-semantics) |
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

## Search semantics

`llmw search` never requires keyword-only phrasing — a full natural-
language query is fine. It tries up to three tiers, only moving to the
next when the previous one finds nothing, so a full match can never be
outranked by a partial one:

1. **strict** — every query term required (AND).
2. **relaxed** — terms that can't match any indexed page at all (typos,
   verb conjugations) are dropped; the rest are still required.
3. **any** — every term becomes optional (OR), ranked by relevance.

`--json` output reports which tier answered the query:
`{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
Pass `--strict` to disable the fallback tiers and only ever run tier 1.

Query terms that are a single Hangul word with a trailing particle (a
조사 — e.g. `스탯창을`, `포탈에서`) are stemmed to the bare noun (`스탯창`,
`포탈`) before matching, since SQLite FTS5's prefix search only matches a
query that is a prefix of the indexed word, not the other way around, so
an inflected query would otherwise miss a bare-noun page. This is a small
curated suffix list, not a full morphological analyzer — it won't stem verb
conjugations (that's what the relaxed tier is for) and will occasionally
strip a coincidental non-particle ending (e.g. `도로` → `도`); this is
always recall-safe (the stem is a prefix of the original word) at worst
adding minor ranking noise, never a missed page.

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

## How the plugin keeps agents honest

Nothing stops an agent from ignoring the skill and editing `wiki/*.md` or
`raw/**` directly with its own file-edit tools instead of `llmw` — that
skips the `--reason` audit log, frontmatter validation, and automatic
backup, and it happens in practice whenever a *different*, competing set
of instructions is in effect and never mentions `llmw`.

When installed as a Claude Code plugin (not a bare `llmw init` project
skill), a `PreToolUse` hook closes that gap at the harness level: a native
`Edit`/`Write`/`NotebookEdit` call targeting `wiki/*.md` or `raw/**` is
denied (or, per config, turned into a confirmation prompt), and the
denial message names the exact `llmw` command to run instead — so the
agent's very next action is a one-line rewrite, not a dead end. A
`SessionStart` hook also drops a short note into context every session:
"this project has an llmw wiki" (with page count) when `.llmw` already
exists, or a one-line "run `llmw init`" hint when it doesn't yet — so a
blank environment with no project `CLAUDE.md`, and no wiki initialized
at all, still discovers `llmw` on turn one.

The guard only ever looks at `Edit`/`Write`/`NotebookEdit` calls whose
target resolves (by walking up from the file, the same way `llmw` finds
its own project root) to a real llmw project's `wiki/*.md` or `raw/**` —
everything else, including plain `Read`, passes through untouched, and it
never inspects `Bash` commands (shell-string policing is its own
false-positive minefield, so the audit trail in `wiki/log.md` plus `llmw
lint` remain the detection layer for that gap instead of a hook trying
to block it).

Configure or disable it per project in `.llmw/config.toml`:

```toml
[hooks]
wiki_guard = "deny"  # default: block, with a message naming the llmw fix
# wiki_guard = "ask"   # prompt for confirmation instead of blocking
# wiki_guard = "off"   # disable the guard for this project
```

Both hooks require Git Bash on Windows (Claude Code falls back to
PowerShell when Git Bash isn't installed, which these shell-form hooks
don't support) — everywhere else, `llmw`'s own safety gate (reason
required, path confined, frontmatter validated, backup before write)
still holds regardless of whether the hook ran.

## Claude Code skill

`llmw init` writes `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}`
into the project. Claude Code auto-discovers this as a plain skill — no
install step. It tells the agent when to reach for `llmw`, the core
search-first workflow, and points to `reference.md`/`examples.md` for
full detail so the always-loaded `SKILL.md` stays short.

If the llm-wiki Claude Code plugin (below) is already installed from the
marketplace, pass `--no-claude-plugin` to skip this project-local copy —
otherwise the project ends up with two copies of the same skill (the
marketplace plugin's, and this one), which is redundant and can be
confusing when Claude Code loads both.

## Distributing `llmw` as an installable Claude Code plugin

This repo doubles as its own Claude Code plugin **marketplace** — no
separate `pip`/`uv`/`pipx` step needed:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(non-interactive equivalents: `claude plugin marketplace add duddudcns/llm-wiki-cli`
and `claude plugin install llm-wiki@llm-wiki-cli`)

This installs the `.claude-plugin/marketplace.json` → `plugin/` package
(`plugin/.claude-plugin/plugin.json` + `plugin/skills/llm-wiki/` +
`plugin/bin/llmw` + `plugin/hooks/hooks.json`). `plugin/bin/llmw` is a
thin dispatcher, not a bundled Python distribution — so a
`SessionStart` hook (`plugin/hooks/hooks.json`) checks for `llmw` on
`PATH` each session and installs it via `uv tool install` (falling back
to `pip install --user`) the first time it's missing. The check is a
single `command -v` (no-op, ~10ms) on every session after that. If you'd
rather manage the CLI install yourself, see [Installation](#installation)
above and skip the plugin, or install both — they don't conflict.

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
edges and llmw's title-based wikilink resolution (`[[Exact Page
Title]]` resolving even when it doesn't match the filename) are both
llmw extensions with no Obsidian equivalent — Obsidian's own graph view
won't show those edges. Two pages with the same filename stem in
different folders also resolve ambiguously (first match wins) in both
tools. Opening `wiki/` in Obsidian gets you a real, useful graph on the
same files, not a pixel-identical one.

## Adapting llmw to an existing wiki

If a wiki already has its own conventions (different frontmatter fields,
top-level files living outside `wiki/`), point `llmw init` at its root and
adjust `.llmw/config.toml` rather than reorganizing the wiki's files:

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

## Development

See [Installation](#installation)'s "Local clone, editable install" above
to set up a dev environment; `pytest` runs the test suite from there.

MVP scope deliberately excludes: an MCP server, daemon/watch mode,
embedding/vector search, direct PDF/DOCX parsing, an Obsidian plugin, a
web UI, and any auto-merge/auto-delete/contradiction-detection logic —
see the project's implementation notes for the full list and rationale.
