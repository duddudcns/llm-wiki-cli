---
name: llm-wiki
description: Search, read, and maintain this project's llmw wiki. Use for project history, prior decisions, source documents, backlinks, and persistent knowledge.
---

# LLM Wiki Skill

Use `llmw` instead of loading the whole wiki into context.

## Prerequisite

Run `llmw --version`. If it is unavailable, explain that the CLI is separate from the Codex plugin and can be installed from the same GitHub repository:

```text
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

Do not silently install software. Initialization is user-invoked through the `llmw-init` skill.

## Workflow

1. Run `llmw status --brief`.
2. Search first with `llmw search "<query>" --limit 5`.
3. Read relevant pages with `llmw read <path> --brief`; use `--full` only when needed.
4. Use `llmw edit` for exact replacements, `llmw patch` for structural diffs, and `llmw write --force` for full replacement.
5. Prefer `llmw archive` over deletion.
6. Run `llmw lint --brief` after major wiki changes.

## Safety

- Never modify `raw/`.
- Do not use generic file-edit tools on `wiki/*.md`; use `llmw edit`, `write`, `patch`, or `archive` so validation, locking, backups, and the audit log remain active.
- Destructive or structural changes require `--reason`.
- Keep command output brief; request JSON only for machine parsing.

See [reference.md](reference.md) for commands and [examples.md](examples.md) for workflows.
