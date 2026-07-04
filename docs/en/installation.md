# Installation

**English** · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · [Français](../fr/installation.md)

## Recommended: Claude Code plugin

If you're using `llmw` from Claude Code, install it as a plugin — this is
the recommended path and needs no separate `pip`/`uv`/`pipx` step:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(non-interactive equivalents: `claude plugin marketplace add duddudcns/llm-wiki-cli`
and `claude plugin install llm-wiki@llm-wiki-cli`)

This installs the Claude Code skill plus two hooks that keep the standalone
`llmw` binary installed and in sync automatically, and keep agents from
bypassing it — see [hooks.md](hooks.md) for exactly what those hooks do and
how to configure them. If you'd rather manage the CLI install yourself, skip
this and use one of the methods below instead — they don't conflict, you can
also install both.

## Standalone CLI

Pick this if you want `llmw` on PATH outside of Claude Code (scripting, CI,
another editor/agent), or if you'd rather control upgrades manually instead
of the plugin's self-heal hook.

`llmw` needs **Python 3.11 or later**, and is not on PyPI yet, so it installs
straight from this repo rather than a package index. **This repo is
currently private** — installing it (any method below) needs your own
authenticated `git` (e.g. already logged in via `gh auth login`, or an SSH
key on your GitHub account); anyone without repo access gets a fetch error,
not a partial install.

All of the methods below give you a global `llmw` command without touching
any other Python project's dependencies.

### Windows

Check your Python version first (PowerShell or Git Bash):

```powershell
python --version
```

Don't have 3.11+ yet?

```powershell
winget install Python.Python.3.12
```

or download the installer from [python.org/downloads](https://www.python.org/downloads/).

Then, with [uv](https://docs.astral.sh/uv/) (recommended — fast, no separate
pipx install needed):

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or [pipx](https://pipx.pypa.io/):

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or plain pip (installs into whatever Python environment is currently active
— use a venv unless you know you want it global):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> The Claude Code plugin's hooks (see [hooks.md](hooks.md)) need Git Bash on
> Windows — Claude Code falls back to PowerShell when Git Bash isn't
> installed, which these shell-form hooks don't support. `llmw`'s own
> safety gate still holds either way; only the hooks' extra convenience is
> affected.

### macOS

Check your Python version first:

```bash
python3 --version
```

Don't have 3.11+ yet?

```bash
brew install python@3.12
```

Then, with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or plain pip:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

Check your Python version first:

```bash
python3 --version
```

Don't have 3.11+ yet?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

Then, with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

or plain pip:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Local clone, editable install (for contributing to `llmw` itself)

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # should show all tests passing
```

See [development.md](development.md) for the rest of the dev workflow.

### Verify

```bash
llmw --version
llmw --help
```

### Updating

```bash
uv tool upgrade llmw           # if installed via uv
pipx upgrade llmw              # if installed via pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # plain pip
```

(If you're using the Claude Code plugin, updating the plugin from the
marketplace also keeps the standalone CLI in sync automatically — see
[hooks.md](hooks.md).)

### Uninstalling

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
