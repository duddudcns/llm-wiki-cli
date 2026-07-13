# Contributing to `llmw`

Bug reports, feature discussion, and pull requests are welcome.

## Reporting bugs / requesting features

Open a [GitHub issue](https://github.com/duddudcns/llm-wiki-cli/issues).
For a bug, include your `llmw --version`, OS, and the exact command that
misbehaved. For a security vulnerability, see [SECURITY.md](SECURITY.md)
instead of opening a public issue.

## Development setup

See [docs/en/installation.md](docs/en/installation.md)'s "Working on
`llmw`'s own code" section to set up a dev environment and run the test
suite, and [docs/en/development.md](docs/en/development.md) for how the
Claude Code / Codex skill-and-rules scaffolding works.

## Before opening a pull request

- Add or update tests for any behavior change — `pytest` should pass.
- Keep the standalone CLI, the Claude Code plugin (`plugin/`), and the
  Codex plugin (`plugins/llm-wiki/`) consistent when a change touches
  shared behavior (commands, flags, hook logic); `tests/
  test_release_consistency.py` and `tests/test_codex_plugin.py` guard
  some of this automatically, but not everything.
- Commit messages follow `<type>: <description>` (`feat`, `fix`, `docs`,
  `test`, `refactor`, `chore`, `perf`, `ci`), matching the existing git
  history.

## Scope

This project intentionally stays small: no direct model calls, no file
watching, no AI-powered semantic search, no PDF/Word ingestion, no GUI.
See the "What this tool intentionally doesn't do (yet)" section of
[docs/en/development.md](docs/en/development.md) before proposing a
feature that crosses one of those lines.
