# Plan: Korean Search Semantics + Out-of-the-Box Agent Compliance

Authored by a Fable-model agent given full repo read access + empirical FTS5
experiments (see conversation history for the research prompt). Tracked here
as a living checklist while implementation proceeds phase by phase.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

## Phase 0 — cross-cutting hardening (no behavior change)

- [ ] `tests/test_release_consistency.py::test_version_lockstep` — assert the
      version string is identical across `pyproject.toml`,
      `src/llmw/__init__.py`, `plugin/.claude-plugin/plugin.json`,
      `src/llmw/templates/plugin.json`,
      `examples/sample-project/.claude-plugin/plugin.json`.
- [ ] `test_plugin_skill_matches_templates` — `plugin/skills/llm-wiki/{SKILL,reference,examples}.md`
      byte-identical to `src/llmw/templates/skill_*.md`.

## Phase 1 — Korean search (target release: 0.1.6)

Root cause: `build_match_query` ANDs every token with no fallback; FTS5
prefix-match is asymmetric (query longer than indexed token != match), so
particle-suffixed queries ("스탯창을") miss the bare-word page, and full
sentence queries fail outright on unmatched conjugated tokens.

- [ ] `src/llmw/korean.py` (new) — `strip_josa(token) -> str | None`, ~35-entry
      curated particle list, longest-suffix-first, all-Hangul tokens only,
      never empties the stem.
- [ ] `src/llmw/search.py` — stem tokens (replace, not OR) in
      `build_match_query`; add 3-tier fallback (`strict` → `relaxed` drops
      zero-df tokens → `any` OR-of-all); `bm25` column weights
      title=5.0/summary=3.0/body=1.0; new `SearchResponse(results, mode,
      dropped_tokens)` return type; `MAX_QUERY_TOKENS = 12` cap.
- [ ] `src/llmw/cli.py` — adapt `search` command to `SearchResponse`; human
      output prints a `note:` line when `mode != "strict"`; `--json` shape
      becomes `{"mode", "dropped_tokens", "results"}` (breaking change,
      document it); add `--strict` flag.
- [ ] `tests/test_korean.py` (new) — stem stripping unit tests incl. false-strip
      documentation case (`도로` → `도`, recall-safe, pinned intentionally).
- [ ] `tests/test_search.py` — particle-query regression, full-sentence
      regression, strict/relaxed/any mode tests, token cap test; update
      existing tests for `SearchResponse`.
- [ ] `tests/test_related.py` — Korean-title term-overlap regression
      (`related.py` consumes `build_match_query` unchanged).
- [ ] README + `plugin/skills/llm-wiki/reference.md` +
      `src/llmw/templates/skill_reference.md` — document search modes.
- [ ] Version bump 0.1.5 → 0.1.6 across all 5 lockstep files.
- [ ] `uv tool upgrade llmw` (or reinstall) + `claude plugin marketplace update`
      + `claude plugin update` to deploy.

## Phase 2 — llmw-usage enforcement (target release: 0.1.7)

Root cause: no `PreToolUse` hook exists; `raw/`-immutability and
write/patch safety gates are reachable only when an agent *voluntarily*
calls `llmw`; the sanctioned mutation path (`llmw patch`, unified diff) is
ergonomically worse than native `Edit`, which is part of why agents bypass
it under a competing skill's instructions.

- [ ] `src/llmw/writer.py` — `edit_page(paths, rel_path, old, new, reason,
      replace_all=False)`: old/new exact-string replace (mirrors native Edit
      semantics) through the same gate as `write_page`/`patch_page`
      (reason required, path safety, frontmatter validation before write,
      backup, log, reindex). New exceptions: `OldStringNotFoundError`,
      `OldStringNotUniqueError`.
- [ ] `src/llmw/cli.py` — `llmw edit PATH --old TEXT --new TEXT --reason TEXT
      [--all]`; hidden `llmw hook pretooluse` / `llmw hook session-start`
      subcommands (always exit 0, broad try/except).
- [ ] `src/llmw/hook.py` (new) — `evaluate_pretooluse(payload) -> dict | None`
      (deny/ask only for `Edit|Write|NotebookEdit` on `<root>/wiki/**.md` or
      `<root>/raw/**`, `None`/no-op for everything else, incl. no `.llmw`
      project found); `evaluate_sessionstart(cwd) -> str | None` (brief
      "this project has an llmw wiki" context, silent outside a project).
- [ ] `src/llmw/config.py` — `hooks_wiki_guard: "deny"|"ask"|"off"` under
      `[hooks]` in `.llmw/config.toml`, default `deny`.
- [ ] `plugin/hooks/hooks.json` — add `PreToolUse` (matcher
      `Edit|Write|NotebookEdit`, shell prefilter on `wiki`/`raw` substring,
      pipes to `llmw hook pretooluse`, `|| true` version-skew guard); extend
      `SessionStart` to also run `llmw hook session-start`.
- [ ] `tests/test_hook.py` (new) — deny/ask/ignore matrix, malformed stdin,
      Windows path handling, nested-project resolution, config off-switch.
- [ ] `tests/test_writer.py` (or new `tests/test_edit.py`) — `edit_page`
      happy path + not-found/ambiguous/raw-refusal/reason-required/
      invalid-frontmatter-rollback cases.
- [ ] `plugin/skills/llm-wiki/SKILL.md` + mirror
      `src/llmw/templates/skill_SKILL.md` (+ `reference.md`/`examples.md`
      pairs) — sharper `description:`, explicit "never native-edit
      wiki/raw" rule, document `llmw edit`.
- [ ] README — "how the plugin keeps agents honest" section (guard,
      config off-switch, PowerShell-only-Windows caveat: hooks need Git
      Bash on Windows).
- [ ] Version bump 0.1.6 → 0.1.7 across all 5 lockstep files.
- [ ] Deploy: `uv tool upgrade llmw` + `claude plugin marketplace update` +
      `claude plugin update`; smoke-test in a scratch project (native Edit
      on a wiki page gets denied with a working `llmw edit` suggestion; a
      non-llmw project sees zero hook side effects).

## Explicitly out of scope (per Fable's plan)

- Real Korean morphological analyzer (`kiwipiepy`) as a hard dependency —
  documented as a future optional `llmw[ko]` extra behind the same
  `strip_josa` seam.
- Blocking `Bash`-based edits to wiki/raw files — shell-string policing is
  the over-blocking failure mode; `wiki/log.md` + `llmw lint` remain the
  detection layer for that gap.
- Per-turn `UserPromptSubmit` context injection — the user explicitly ruled
  out a heavy, always-on harness.
