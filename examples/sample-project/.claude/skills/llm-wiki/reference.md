# LLM Wiki CLI Reference

All commands accept `--json` for machine-parseable output. Most read
commands default to a brief, context-cheap output; pass `--full` or
`--verbose` for more detail.

## Commands

- `llmw init` / `llmw init --force` — scaffold `raw/`, `wiki/`, `.llmw/`,
  and this skill in the current directory.
- `llmw status --brief` / `--json` — page counts, broken links, orphans,
  last indexed time, dirty pages.
- `llmw rebuild` — full re-index of `wiki/**/*.md` from scratch.
- `llmw index --changed` — incremental re-index (hash/mtime based).
- `llmw search "<query>" [--limit N] [--type TYPE] [--json]` — SQLite
  FTS5 search over title/summary/body. Default limit 5.
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
- `llmw patch <path> --reason "<reason>" --stdin` — apply a unified diff
  to an existing wiki page. Creates a backup first; rolls back on
  failure.
- `llmw archive <path> --reason "<reason>"` — move a page to
  `wiki/archived/YYYY/MM/`, stamp archive frontmatter, leave a tombstone
  stub at the original path (default), and log the change.
- `llmw lint [--brief] [--json]` — broken links, orphans, duplicate
  titles/aliases, missing/invalid frontmatter, missing summary/type,
  isolated pages, dangling raw references, active pages linking into
  `archived/`. Does not auto-fix.
- `llmw health [--brief]` — system-level checks (config, index db,
  schema version, directory existence, lock state).
- `llmw graph build` — regenerate `.llmw/graph.json`.
- `llmw graph export [--format json|html]` — write `graph.json` and/or
  `graph.html`.

## Rules

- `raw/` is immutable — `write`/`patch`/`archive` refuse any path inside
  it.
- Every `write`/`patch`/`archive` call requires `--reason`; the reason is
  appended to `wiki/log.md` and the `log_entries` table.
- There is no `delete` command by design — use `archive`.
- `index.sqlite` and `graph.json` are derived data; `llmw rebuild` always
  regenerates them from `wiki/*.md`, the source of truth.
- CLI output is brief by default to save context; do not assume `--full`
  or `--json` output unless you asked for it.
