# LLM Wiki MCP Reference (Codex)

Codex has no CLI equivalent of `llmw` for the agent to shell out to (the
`llmw` binary that `SessionStart` self-installs exists only so the
PreToolUse/Stop hooks can call it quickly — it is not an agent-facing
surface). All wiki access goes through the `llm-wiki` MCP server's tools.

## Tools

- `llmw_status(root?)` — page counts, broken links, orphans, last indexed
  time, dirty pages.
- `llmw_search(query, root?, limit=5)` — SQLite FTS5 search over
  title/summary/body. Natural-language queries are fine: search tries
  strict AND-of-terms first, then relaxes to drop terms that can't match
  anything, then falls back to OR-of-all-terms. Korean particle suffixes
  (e.g. `스탯창을`) are stemmed to the bare noun before matching. Returns
  `{"mode": "strict"|"relaxed"|"any", "dropped_tokens": [...], "results": [...]}`.
- `llmw_read(target, root?, full=false)` — look up a page by path, title,
  or alias. `full=false` (default) returns title, type, summary, key
  points, links, backlink count. Pass `full=true` to also get `full_text`
  (the raw page body) — needed before `llmw_edit`/`llmw_patch` so the old
  text you're matching against is exact.
- `llmw_write(path, content, reason, root?, force=false)` — create or
  fully replace a wiki page. Fails if the file exists unless `force=true`.
  `reason` is required and is appended to `wiki/log.md` and the
  `log_entries` table.
- `llmw_edit(path, old, new, reason, root?, replace_all=false)` — exact-string
  replace in an existing page, the same old/new semantics as a native
  Edit tool. Fails if `old` isn't found, or matches more than once without
  `replace_all=true`. Prefer this over `llmw_write` for a small,
  contiguous change — no need to resend the whole page.
- `llmw_patch(path, diff, reason, root?)` — apply a unified diff to an
  existing page. Backs up first; rolls back (leaves the original
  untouched) if the diff fails to apply. Use for a structural multi-line
  change where `llmw_edit`'s single old/new pair doesn't fit.
- `llmw_archive(path, reason, root?, tombstone?)` — move a page to
  `wiki/archived/YYYY/MM/`, stamp archive frontmatter, log the change.
  This is the delete: there is no other way to retire a page.
  `tombstone` (default: project config, else `true`) leaves a stub with
  `moved_to:` at the original path so inbound links don't dangle.
- `llmw_related(target, root?, limit=10, by="links,tags,terms")` —
  deterministic related-page candidates (shared links, tags, title/term
  overlap), no model calls.
- `llmw_links(target, root?)` — outgoing links from a page, with broken
  status.
- `llmw_backlinks(target, root?)` — incoming links to a page.
- `llmw_lint(root?)` — broken links, orphans, duplicate titles/aliases,
  missing frontmatter, and other deterministic wiki issues. Reports only,
  never auto-fixes — fix findings via `llmw_edit`/`llmw_patch`/
  `llmw_write`/`llmw_archive`.
- `llmw_health(root?)` — system-level checks distinct from `llmw_lint`'s
  content checks: config readable, index db readable and on the expected
  schema version, no stale locks.
- `llmw_ingest(source, root?)` — register a `raw/` source (`.md`/`.txt`
  only) as a `wiki/sources/<slug>.md` draft, ready for `llmw_edit`/
  `llmw_write` to flesh out.
- `llmw_graph(root?)` — the wiki's link graph (nodes = pages with
  type/tags/degree, edges = resolved references). Read-only: does not
  write `graph.json`/`graph.html` (see Rules below).
- `llmw_init(path=".", layout="classic")` — scaffold `raw/`, `wiki/`,
  `.llmw/` in a project that doesn't have a wiki yet. User-invoked only
  (see the `llmw-init` skill) — do not call this on your own initiative.
  Does not accept `force`/`adopt` overrides; if a wiki already partially
  exists, expect an error and tell the user instead of retrying with
  different arguments.

## Rules

- `raw/` is immutable — never write there.
- Every `llmw_write`/`llmw_edit`/`llmw_patch`/`llmw_archive` call requires
  a meaningful `reason`.
- There is no delete — `llmw_archive` is the sanctioned way to retire
  content.
- `index.sqlite` and `graph.json` are derived data owned by the MCP
  server's host project — `llmw_graph` returns the graph in-memory but
  never writes those files; that stays the host project's job.
- A page's `related:` frontmatter (list of paths/titles) counts as links,
  same as inline `[[wikilinks]]`.

## No wiki/raw write guard on Codex

Unlike the Claude Code plugin, there is **no** `PreToolUse` guard here
that blocks a native file-edit tool from touching `wiki/*.md` or `raw/**`
— nothing enforces the "use `llmw_write`, not a raw edit" rule but this
skill's own instructions. Treat `wiki/*.md` as off-limits to `apply_patch`
and any other file-edit tool; go through `llmw_write` instead so
validation, locking, and the audit log stay active.
