# Instalación

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · **Español** · [Français](../fr/installation.md)

## Recomendado: Plugin de Claude Code

Si estás usando `llmw` desde Claude Code, instálalo como un plugin — este es
el camino recomendado y no requiere paso separado `pip`/`uv`/`pipx`:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(equivalentes no interactivos: `claude plugin marketplace add duddudcns/llm-wiki-cli`
y `claude plugin install llm-wiki@llm-wiki-cli`)

Esto instala la habilidad de Claude Code más dos hooks que mantienen el
binario `llmw` autónomo instalado y en sincronización automática, y evitan que los agentes
lo eludan — ver [hooks.md](hooks.md) para exactamente qué hacen esos hooks y
cómo configurarlos. Si prefieres gestionar la instalación de la CLI tú mismo, omite
esto y usa uno de los métodos a continuación en su lugar — no entran en conflicto, también puedes
instalar ambos.

## CLI autónoma

Elige esto si quieres `llmw` en PATH fuera de Claude Code (scripting, CI,
otro editor/agente), o si prefieres controlar las actualizaciones manualmente en lugar
del hook auto-sanador del plugin.

`llmw` necesita **Python 3.11 o posterior**, y aún no está en PyPI, así que se instala
directamente desde este repositorio en lugar de un índice de paquetes. **Este repositorio es
actualmente privado** — instalarlo (cualquier método abajo) necesita tu propio
`git` autenticado (p. ej., ya conectado vía `gh auth login`, o una clave SSH
en tu cuenta GitHub); cualquiera sin acceso al repositorio obtiene un error de fetch,
no una instalación parcial.

Todos los métodos a continuación te dan un comando global `llmw` sin tocar
las dependencias de ningún otro proyecto Python.

### Windows

Primero verifica tu versión de Python (PowerShell o Git Bash):

```powershell
python --version
```

¿Aún no tienes 3.11+?

```powershell
winget install Python.Python.3.12
```

o descarga el instalador desde [python.org/downloads](https://www.python.org/downloads/).

Luego, con [uv](https://docs.astral.sh/uv/) (recomendado — rápido, sin instalación separada de
pipx necesaria):

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o [pipx](https://pipx.pypa.io/):

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o pip simple (instala en cualquier entorno Python actualmente activo
— usa un venv a menos que sepas que lo quieres global):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Los hooks del plugin de Claude Code (ver [hooks.md](hooks.md)) necesitan Git Bash en
> Windows — Claude Code vuelve a PowerShell cuando Git Bash no está
> instalado, que estos hooks de forma shell no soportan. La puerta de seguridad propia de `llmw`
> se mantiene de todas formas; solo la conveniencia extra de los hooks se ve
> afectada.

### macOS

Primero verifica tu versión de Python:

```bash
python3 --version
```

¿Aún no tienes 3.11+?

```bash
brew install python@3.12
```

Luego, con [uv](https://docs.astral.sh/uv/) (recomendado):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o pip simple:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

Primero verifica tu versión de Python:

```bash
python3 --version
```

¿Aún no tienes 3.11+?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

Luego, con [uv](https://docs.astral.sh/uv/) (recomendado):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o pip simple:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Clon local, instalación editable (para contribuir a `llmw` mismo)

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # should show all tests passing
```

Ver [development.md](development.md) para el resto del flujo de trabajo de dev.

### Verificar

```bash
llmw --version
llmw --help
```

### Actualizando

```bash
uv tool upgrade llmw           # if installed via uv
pipx upgrade llmw              # if installed via pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # plain pip
```

(Si estás usando el plugin de Claude Code, actualizar el plugin desde el
marketplace también mantiene la CLI autónoma en sincronización automáticamente — ver
[hooks.md](hooks.md).)

### Desinstalando

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
