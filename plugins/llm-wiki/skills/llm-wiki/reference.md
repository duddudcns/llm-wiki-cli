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
  points, links, backlink count.
- `llmw_write(path, content, reason, root?, force=false)` — create or
  fully replace a wiki page. Fails if the file exists unless `force=true`.
  `reason` is required and is appended to `wiki/log.md` and the
  `log_entries` table.
- `llmw_init(path=".", layout="classic")` — scaffold `raw/`, `wiki/`,
  `.llmw/` in a project that doesn't have a wiki yet. User-invoked only
  (see the `llmw-init` skill) — do not call this on your own initiative.
  Does not accept `force`/`adopt` overrides; if a wiki already partially
  exists, expect an error and tell the user instead of retrying with
  different arguments.

## Not available over MCP yet

The standalone CLI (used by the Claude Code plugin) also has
`edit`/`patch`/`archive`/`lint`/`graph`/`related`/`backlinks`/`links`/`ingest`
commands, but none of them are exposed as MCP tools here — only the five
above are. In practice this means: a small exact-text fix or a structural
multi-line change both go through `llmw_write(force=true)` with the full
new page content, not a diff; there's no built-in "related pages" or
"lint" call to reach for. If a task genuinely needs one of these and
`llmw_write` can't express it, say so rather than guessing at a tool name
that doesn't exist.

## Rules

- `raw/` is immutable — never write there.
- Every `llmw_write` call requires a meaningful `reason`.
- There is no delete — write an archived-style page by convention if you
  need to retire content (see `archive` guidance on the CLI side, which
  isn't exposed here; a plain content edit noting the page is superseded
  is the practical substitute).
- `index.sqlite` and `graph.json` are derived data owned by the MCP
  server's host project, not something this skill manages directly.
- A page's `related:` frontmatter (list of paths/titles) counts as links,
  same as inline `[[wikilinks]]`.

## No wiki/raw write guard on Codex

Unlike the Claude Code plugin, there is **no** `PreToolUse` guard here
that blocks a native file-edit tool from touching `wiki/*.md` or `raw/**`
— nothing enforces the "use `llmw_write`, not a raw edit" rule but this
skill's own instructions. Treat `wiki/*.md` as off-limits to `apply_patch`
and any other file-edit tool; go through `llmw_write` instead so
validation, locking, and the audit log stay active.
