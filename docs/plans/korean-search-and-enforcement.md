# Plan: Korean Search Semantics + Out-of-the-Box Agent Compliance

Authored by a Fable-model agent given full repo read access + empirical FTS5
experiments (see conversation history for the research prompt). Tracked here
as a living checklist while implementation proceeds phase by phase.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

## Phase 0 — cross-cutting hardening (no behavior change) — DONE (60fa30d)

- [x] `tests/test_release_consistency.py::test_version_lockstep` — assert the
      version string is identical across `pyproject.toml`,
      `src/llmw/__init__.py`, `plugin/.claude-plugin/plugin.json`,
      `src/llmw/templates/plugin.json`,
      `examples/sample-project/.claude-plugin/plugin.json`.
- [x] `test_plugin_skill_matches_templates` — `plugin/skills/llm-wiki/{SKILL,reference,examples}.md`
      byte-identical to `src/llmw/templates/skill_*.md`.

## Phase 1 — Korean search (0.1.6) — DONE (066d137), deployed

Root cause: `build_match_query` ANDs every token with no fallback; FTS5
prefix-match is asymmetric (query longer than indexed token != match), so
particle-suffixed queries ("스탯창을") miss the bare-word page, and full
sentence queries fail outright on unmatched conjugated tokens.

- [x] `src/llmw/korean.py` (new) — `strip_josa(token) -> str | None`, ~35-entry
      curated particle list, longest-suffix-first, all-Hangul tokens only,
      never empties the stem.
- [x] `src/llmw/search.py` — stem tokens (replace, not OR) in
      `build_match_query`; add 3-tier fallback (`strict` → `relaxed` drops
      zero-df tokens → `any` OR-of-all); `bm25` column weights
      title=5.0/summary=3.0/body=1.0; new `SearchResponse(results, mode,
      dropped_tokens)` return type; `MAX_QUERY_TOKENS = 12` cap.
- [x] `src/llmw/cli.py` — adapt `search` command to `SearchResponse`; human
      output prints a `note:` line when `mode != "strict"`; `--json` shape
      becomes `{"mode", "dropped_tokens", "results"}` (breaking change,
      document it); add `--strict` flag.
- [x] `tests/test_korean.py` (new) — stem stripping unit tests incl. false-strip
      documentation case (`도로` → `도`, recall-safe, pinned intentionally).
- [x] `tests/test_search.py` — particle-query regression, full-sentence
      regression, strict/relaxed/any mode tests, token cap test; update
      existing tests for `SearchResponse`.
- [x] `tests/test_related.py` — Korean-title term-overlap regression
      (`related.py` consumes `build_match_query` unchanged).
- [x] README + `plugin/skills/llm-wiki/reference.md` +
      `src/llmw/templates/skill_reference.md` — document search modes.
- [x] Version bump 0.1.5 → 0.1.6 across all 5 lockstep files.
- [x] `uv tool upgrade llmw` (or reinstall) + `claude plugin marketplace update`
      + `claude plugin update` to deploy. Confirmed: standalone `llmw
      --version` -> 0.1.6; `claude plugin details llm-wiki@llm-wiki-cli`
      -> 0.1.6 (restart needed to fully apply on the Claude Code side).

## Phase 2 — llmw-usage enforcement (0.1.7) — DONE, deploying

Root cause: no `PreToolUse` hook exists; `raw/`-immutability and
write/patch safety gates are reachable only when an agent *voluntarily*
calls `llmw`; the sanctioned mutation path (`llmw patch`, unified diff) is
ergonomically worse than native `Edit`, which is part of why agents bypass
it under a competing skill's instructions.

- [x] `src/llmw/writer.py` — `edit_page(paths, rel_path, old, new, reason,
      replace_all=False)`: old/new exact-string replace (mirrors native Edit
      semantics) through the same gate as `write_page`/`patch_page`
      (reason required, path safety, frontmatter validation before write,
      backup, log, reindex). New exceptions: `OldStringNotFoundError`,
      `OldStringNotUniqueError`.
- [x] `src/llmw/cli.py` — `llmw edit PATH --old TEXT --new TEXT --reason TEXT
      [--all]`; hidden `llmw hook pretooluse` / `llmw hook session-start`
      subcommands (always exit 0, broad try/except).
- [x] `src/llmw/hook.py` (new) — `evaluate_pretooluse(payload) -> dict | None`
      (deny/ask only for `Edit|Write|NotebookEdit` on `<root>/wiki/**.md` or
      `<root>/raw/**`, `None`/no-op for everything else, incl. no `.llmw`
      project found); `evaluate_sessionstart(cwd) -> str | None` (brief
      "this project has an llmw wiki" context, silent outside a project).
      Schema verified live against the official Claude Code hooks docs
      (hookSpecificOutput/hookEventName/permissionDecision/
      permissionDecisionReason; exit 0 + no JSON = no opinion).
- [x] `src/llmw/config.py` — `hooks_wiki_guard: "deny"|"ask"|"off"` under
      `[hooks]` in `.llmw/config.toml`, default `deny`.
- [x] `plugin/hooks/hooks.json` — add `PreToolUse` (matcher
      `Edit|Write|NotebookEdit`, shell prefilter on `wiki`/`raw` substring,
      pipes to `llmw hook pretooluse`, `|| true` version-skew guard); extend
      `SessionStart` to also run `llmw hook session-start`. End-to-end
      shell-level smoke test run manually against a real scratch project
      (deny fired correctly; version-skew `|| true` fallback verified with
      a deliberately-unknown subcommand).
- [x] `tests/test_hook.py` (new) — deny/ask/ignore matrix, malformed stdin,
      Windows path handling, nested-project resolution, config off-switch,
      plus CLI-level subprocess tests for both hidden hook subcommands.
- [x] `tests/test_writer.py` — `edit_page` happy path + not-found/
      ambiguous/raw-refusal/reason-required/invalid-frontmatter-rollback
      cases.
- [x] `tests/test_config.py` (new) — `hooks_wiki_guard` default/round-trip/
      invalid-value-fallback.
- [x] `plugin/skills/llm-wiki/SKILL.md` + mirror
      `src/llmw/templates/skill_SKILL.md` (+ `reference.md`/`examples.md`
      pairs) — sharper `description:`, explicit "never native-edit
      wiki/raw" rule, document `llmw edit`, worked example.
- [x] README — "how the plugin keeps agents honest" section (guard,
      config off-switch, PowerShell-only-Windows caveat: hooks need Git
      Bash on Windows).
- [x] Version bump 0.1.6 → 0.1.7 across all 5 lockstep files.
- [x] Deploy: `uv tool upgrade llmw` + `claude plugin marketplace update` +
      `claude plugin update`; smoke-test in a scratch project (native Edit
      on a wiki page gets denied with a working `llmw edit` suggestion; a
      non-llmw project sees zero hook side effects). Confirmed: standalone
      `llmw --version` -> 0.1.7; `claude plugin update` reports 0.1.6 ->
      0.1.7 (restart needed for the new PreToolUse hook to take effect in
      this session).

## Phase 3 — SessionStart init hint (0.1.8) — DONE

Root cause: `evaluate_sessionstart` returned `None` (fully silent) when no
`.llmw` project exists yet, so a brand-new repo with the plugin installed
gave zero signal that `llmw init` was even an option — the only path to
discovery was the model spontaneously matching the SKILL.md description.
Explicitly NOT auto-running `llmw init` from the hook itself: doing so
would silently scaffold `.llmw/`/`wiki/`/`raw/` into every project ever
opened with the plugin installed, including ones that never want a wiki —
a bigger, more surprising side effect than the minimal-harness bar allows.
User chose "hint only" over "auto-init" or "no signal" when asked directly.

- [x] `src/llmw/hook.py` — `evaluate_sessionstart` returns a one-line
      `_NO_PROJECT_HINT` ("Run `llmw init` if you want persistent,
      searchable project knowledge tracked here") instead of `None` when
      `find_project_root` raises `ProjectNotFoundError`. Pure text, no
      file-system side effects — same fail-open shape as everywhere else
      in `hook.py`.
- [x] `tests/test_hook.py` — updated `test_sessionstart_silent_outside_project`
      -> `test_sessionstart_hints_init_outside_project` and the matching
      CLI-level test to assert the hint text instead of silence.
- [x] README "How the plugin keeps agents honest" section updated to
      describe both `SessionStart` cases (inside vs. outside a project).
- [x] Version bump 0.1.7 → 0.1.8 across all 5 lockstep files.

## Status: all phases shipped

All four phases are done and pushed to `origin/master` (`60fa30d`,
`066d137`, `2baa791`, plus Phase 3's commit). Restart Claude Code to pick
up the new `PreToolUse` hook and updated `SessionStart` context in this
session.

## Explicitly out of scope (per Fable's plan)

- Real Korean morphological analyzer (`kiwipiepy`) as a hard dependency —
  documented as a future optional `llmw[ko]` extra behind the same
  `strip_josa` seam.
- Blocking `Bash`-based edits to wiki/raw files — shell-string policing is
  the over-blocking failure mode; `wiki/log.md` + `llmw lint` remain the
  detection layer for that gap.
- Per-turn `UserPromptSubmit` context injection — the user explicitly ruled
  out a heavy, always-on harness.
