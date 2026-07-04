# Hooks: keeping agents honest and the CLI in sync

**English** · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · [Français](../fr/hooks.md)

The Claude Code plugin (see [installation.md](installation.md)) installs two
hooks. Neither is required to use `llmw` — they're conveniences layered on
top of a CLI that already enforces its own safety rules regardless of
whether a hook ran.

## PreToolUse: the wiki guard

Nothing stops an agent from ignoring the Claude Code skill and editing
`wiki/*.md` or `raw/**` directly with its own file-edit tools instead of
`llmw` — that skips the `--reason` audit log, frontmatter validation, and
automatic backup, and it happens in practice whenever a *different*,
competing set of instructions is in effect and never mentions `llmw`.

When installed as a Claude Code plugin (not a bare `llmw init` project
skill), a `PreToolUse` hook closes that gap at the harness level: a native
`Edit`/`Write`/`NotebookEdit` call targeting `wiki/*.md` or `raw/**` is
denied (or, per config, turned into a confirmation prompt), and the denial
message names the exact `llmw` command to run instead — so the agent's very
next action is a one-line rewrite, not a dead end.

The guard only ever looks at `Edit`/`Write`/`NotebookEdit` calls whose
target resolves (by walking up from the file, the same way `llmw` finds its
own project root) to a real llmw project's `wiki/*.md` or `raw/**` —
everything else, including plain `Read`, passes through untouched, and it
never inspects `Bash` commands (shell-string policing is its own
false-positive minefield, so the audit trail in `wiki/log.md` plus `llmw
lint` remain the detection layer for that gap instead of a hook trying to
block it).

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
required, path confined, frontmatter validated, backup before write) still
holds regardless of whether the hook ran.

Also drops a short `SessionStart` note into context every session: "this
project has an llmw wiki" (with page count) when `.llmw` already exists, or
a one-line "run `llmw init`" hint when it doesn't yet — so a blank
environment with no project `CLAUDE.md`, and no wiki initialized at all,
still discovers `llmw` on turn one.

## SessionStart: self-healing CLI install

`plugin/bin/llmw` is a thin dispatcher, not a bundled Python distribution —
it shells out to a real `llmw` on PATH. Updating the plugin from the
marketplace only updates the plugin's own files (skill, hooks); it does
**not** touch that standalone binary. Left alone, that means installing a
plugin update can silently leave you running an old CLI underneath it.

A `SessionStart` hook (`plugin/hooks/session-start.sh`, wired up via
`plugin/hooks/hooks.json`) closes that gap: every session, it compares the
installed `llmw --version` against the version this plugin bundle declares
(`plugin/.claude-plugin/plugin.json`). On a mismatch — including "not
installed at all" — it (re)installs via `uv tool install --force` (falling
back to `pip install --user --force-reinstall`), pinned to the matching
`git` tag (`git+...@v<version>`), so a plugin-marketplace update also
brings the standalone CLI binary in sync without a separate manual
`uv tool upgrade llmw`.

When versions already match, the check is just one local `llmw --version`
call (no network) each session — the reinstall path only runs on genuine
version drift, roughly once per release.
