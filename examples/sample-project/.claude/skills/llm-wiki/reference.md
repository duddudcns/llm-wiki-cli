# LLM Wiki CLI Reference

Most commands accept `--json` for machine-parseable output —
`write`/`edit`/`patch`/`archive`/`ingest` report success or failure as
plain text only. Most read commands default to a brief, context-cheap
output; pass `--full` for more detail.

## Commands

- `llmw init` / `llmw init --force` — scaffold `raw/`, `wiki/`, `.llmw/`,
  and this skill in the current directory. `--layout ai-wiki` nests
  everything under an `ai-wiki/` folder instead of the project root;
  `--adopt` indexes an already-populated wiki without scaffolding over
  its content; `--no-claude-plugin` skips writing this skill (use when
  the Claude Code plugin is already installed).
- `llmw status --brief` / `--json` — page counts, broken links, orphans,
  last indexed time, dirty pages.
- `llmw rebuild` — full re-index of `wiki/**/*.md` from scratch.
- `llmw index --changed` — incremental re-index (hash/mtime based).
- `llmw search "<query>" [--limit N] [--type TYPE] [--strict] [--json]` —
  SQLite FTS5 search over title/summary/body. Default limit 5. Natural-
  language queries are fine: search tries strict AND-of-terms first, then
  relaxes to drop terms that can't match anything, then falls back to
  OR-of-all-terms — it never needs keyword-only phrasing. Korean particle
  suffixes (e.g. `스탯창을`) are stemmed to the bare noun before matching.
  `--json` output is `{"mode": "strict"|"relaxed"|"any", "dropped_tokens":
  [...], "results": [...]}`. Pass `--strict` to disable the fallback tiers.
- `llmw read <path-or-title> [--brief|--full] [--json]` — look up a page
  by path, title, or alias. `--brief` (default) shows title, type,
  summary, key points, links, backlink count.
- `llmw links <path-or-title> [--json]` — outgoing links, with broken
  status.
- `llmw backlinks <path-or-title> [--json]` — incoming links.
- `llmw related <path-or-title> [--limit N] [--by links,tags,terms]
  [--json]` — deterministic related-page candidates (no model calls).
- `llmw ingest <file>` — register a `raw/` source (`.md`/`.txt` only in
  this MVP) as a `wiki/sources/<slug>.md` draft. Does not summarize;
  leaves a placeholder for the agent to fill in.
- `llmw write <path> --reason "<reason>" --stdin [--force]` — create a
  new wiki page from stdin. Fails if the file exists unless `--force`.
- `llmw edit <path> --old "<text>" --new "<text>" --reason "<reason>"
  [--all]` — exact-string replace in an existing page, the same old/new
  semantics as a native Edit tool. Fails if `--old` isn't found, or
  matches more than once without `--all`. Prefer this over `patch` for a
  small, exact change — no diff/context-line bookkeeping required.
- `llmw patch <path> --reason "<reason>" --stdin` — apply a unified diff
  to an existing wiki page. Creates a backup first; rolls back on
  failure. Use for structural, multi-line changes.
- `llmw archive <path> --reason "<reason>" [--tombstone/--no-tombstone]`
  — move a page to `wiki/archived/YYYY/MM/`, stamp archive frontmatter,
  leave a tombstone stub at the original path (default; `--no-tombstone`
  skips it), and log the change.
- `llmw lint [--brief] [--json]` — broken links, orphans, duplicate
  titles/aliases, missing/invalid frontmatter, missing summary/type,
  isolated pages, dangling raw references, active pages linking into
  `archived/`. Does not auto-fix.
- `llmw health [--brief]` — system-level checks (config, index db,
  schema version, directory existence, lock state).
- `llmw graph build` — regenerate `.llmw/graph.json`.
- `llmw graph export [--format json|html|both]` — write `graph.json`
  and/or `graph.html`.

## Rules

- `raw/` is immutable — `write`/`patch`/`archive` refuse any path inside
  it.
- Every `write`/`edit`/`patch`/`archive` call requires `--reason`; the
  reason is appended to `wiki/log.md` and the `log_entries` table.
- There is no `delete` command by design — use `archive`.
- `index.sqlite` and `graph.json` are derived data; `llmw rebuild` always
  regenerates them from `wiki/*.md`, the source of truth.
- CLI output is brief by default to save context; do not assume `--full`
  or `--json` output unless you asked for it.
- A page's `related:` frontmatter (list of paths/titles) counts as links,
  same as inline `[[wikilinks]]`. If this wiki already used `related:` as
  its cross-reference convention before `llmw`, you don't need to also add
  inline wikilinks.
- If this project keeps `index.md`/`log.md`/schema-style files outside
  `wiki/`, or uses different required frontmatter fields (e.g.
  `last_updated` instead of `created`/`updated`), check
  `.llmw/config.toml` for `extra_root_pages` / `[lint] required_frontmatter`
  overrides before assuming those files are being ignored or that lint
  findings are real gaps.

## Native Edit/Write are guarded

When installed as a Claude Code plugin, a `PreToolUse` hook denies (or
asks, per config) native `Edit`/`Write`/`NotebookEdit` calls targeting
`wiki/*.md` or `raw/**` — the denial message names the exact `llmw`
command to run instead. This is enforced by the harness, not just this
skill's advice, so it applies even if another skill's instructions never
mention `llmw`. A project can change or disable it via `.llmw/config.toml`:

```toml
[hooks]
wiki_guard = "deny"  # default. Also: "ask" (prompt instead), "off" (disable)
```
