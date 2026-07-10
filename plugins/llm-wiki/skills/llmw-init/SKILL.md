---
name: llmw-init
description: Explicit, user-invoked setup for this project's llmw wiki. Use only when the user asks to initialize or adopt an llmw wiki.
disable-model-invocation: false
---

# llmw init

User-invoked only. Do not initialize a wiki on your own initiative.

## Prerequisite

Check `llmw --version`. If the command is missing, tell the user to install it from the same GitHub repository:

```text
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

Do not silently install software.

## What to do

1. Check whether a wiki already exists (`raw/`, `wiki/`, `.llmw/`, or under `ai-wiki/`).
2. If one exists, ask whether to use `--force`, `--adopt`, or a different `--layout`.
3. Run `llmw init` with the user's requested flags.
4. Report what was created and suggest `llmw status --brief`.

The main `llm-wiki` skill handles ongoing wiki work after setup.
