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

This also installs three safety nets: one keeps the command-line tool
itself up to date automatically, one keeps the AI from skipping the wiki
and editing files directly, and one reminds the AI to search the wiki
before starting new work — see [hooks.md](hooks.md) for exactly what they
do and how to turn them off if you don't want them. If you'd rather
install the command-line tool yourself and manage updates by hand, skip
this and use one of the methods below instead — they don't conflict, you
can install both.

## Command-line tool (without the plugin)

Pick this if you want to use `llmw` outside of Claude Code — in a script,
in an automated pipeline, or with another editor/tool.

`llmw` needs **Python 3.11 or later**. It isn't published to a public
package index yet, so it installs directly from this GitHub repository
instead. **This repository is currently private** — installing it (any
method below) requires your own GitHub login to be set up for `git` (for
example, already logged in via `gh auth login`, or an SSH key added to
your GitHub account). Without that, the install will fail with a clear
error instead of installing something broken.

Every method below gives you an `llmw` command you can run from anywhere,
without affecting any other Python project on your computer.

### Windows

First, check which version of Python you have (PowerShell or Git Bash):

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

or plain pip (this installs into whichever Python setup is currently
active on your computer — only do this if you're sure that's what you
want):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> The Claude Code plugin's safety-net features (see [hooks.md](hooks.md))
> need "Git Bash" installed on Windows to work. If it's missing, those
> extra features just won't run — `llmw` itself still works fine and
> keeps its own safety checks either way.

### macOS

First, check which version of Python you have:

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

First, check which version of Python you have:

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

### Working on `llmw`'s own code

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # should show all tests passing
```

See [development.md](development.md) for more on contributing.

### Check it worked

```bash
llmw --version
llmw --help
```

### Getting updates

```bash
uv tool upgrade llmw           # if installed via uv
pipx upgrade llmw              # if installed via pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # plain pip
```

(If you installed the Claude Code plugin, updating it from the
marketplace also updates the command-line tool automatically — see
[hooks.md](hooks.md).)

### Removing it

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
