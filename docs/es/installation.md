# Instalación

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · **Español** · [Français](../fr/installation.md)

## Recomendado: plugin de Claude Code

Si vas a usar `llmw` desde Claude Code, instálalo como plugin — es el camino recomendado y no necesita ningún paso aparte con `pip`, `uv` o `pipx`:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(el equivalente para usar sin interacción: `claude plugin marketplace add duddudcns/llm-wiki-cli`
y `claude plugin install llm-wiki@llm-wiki-cli`)

Esto también instala cuatro redes de seguridad: una mantiene actualizada por su cuenta la herramienta de línea de comandos, otra evita que la IA se salte la wiki y edite los archivos directamente, y las otras dos le recuerdan a la IA que busque en la wiki antes de empezar un trabajo nuevo y que la actualice una vez terminado — mira [hooks.md](hooks.md) para ver exactamente qué hace cada una y cómo desactivarlas si no las quieres. Si prefieres instalar tú mismo la herramienta de línea de comandos y encargarte de las actualizaciones a mano, sáltate esto y usa uno de los métodos de abajo — no chocan entre sí, puedes instalar las dos cosas.

## Plugin de Codex

Instala el marketplace directamente desde GitHub, después instala el plugin:

```powershell
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

Verificalo con `codex plugin list`. El plugin expone herramientas nativas de la wiki a través de un servidor MCP y usa `uvx` para obtener automáticamente su versión fija de GitHub. Instala [uv](https://docs.astral.sh/uv/) primero si `uvx --version` no funciona. Codex no ejecuta los archivos de redes del plugin de Claude Code — tiene sus propias redes PreToolUse/Stop, separadas (mantienen los mismos recordatorios de buscar-antes/actualizar-después, adaptados a la superficie de herramientas de Codex), que instalan por su cuenta una versión fija de `llmw` en el fondo la primera vez que las usas. Así que solo necesitas instalar la herramienta de línea de comandos manualmente si quieres usarla directamente desde la terminal.

## Herramienta de línea de comandos (sin el plugin)

Elige esta opción si quieres usar `llmw` fuera de Claude Code — en un script, en un proceso automatizado, o con otro editor u otra herramienta.

`llmw` necesita **Python 3.11 o más reciente**. Todavía no está publicada en un índice de paquetes público, así que se instala directamente desde este repositorio público de GitHub — como el repositorio es público, no necesitas configurar un inicio de sesión de GitHub ni una llave SSH.

Cualquiera de estos métodos te deja con un comando `llmw` que puedes usar desde donde sea, sin afectar ningún otro proyecto de Python que tengas en tu computadora.

### Windows

Primero, revisa qué versión de Python tienes (con PowerShell o Git Bash):

```powershell
python --version
```

¿Todavía no tienes la 3.11 o más nueva?

```powershell
winget install Python.Python.3.12
```

o descarga el instalador desde [python.org/downloads](https://www.python.org/downloads/).

Después, con [uv](https://docs.astral.sh/uv/) (recomendado — es rápido y no necesita instalar pipx aparte):

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con [pipx](https://pipx.pypa.io/):

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con pip normal (esto instala en el Python que esté activo en tu computadora en ese momento — hazlo solo si estás seguro de que eso es lo que quieres):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Las redes de seguridad del plugin de Claude Code (mira [hooks.md](hooks.md))
> necesitan tener "Git Bash" instalado en Windows para funcionar. Si no lo
> tienes, esas funciones extra simplemente no se van a ejecutar — `llmw`
> sigue funcionando bien de todas formas, y mantiene sus propios chequeos de
> seguridad de cualquier manera.

### macOS

Primero, revisa qué versión de Python tienes:

```bash
python3 --version
```

¿Todavía no tienes la 3.11 o más nueva?

```bash
brew install python@3.12
```

Después, con [uv](https://docs.astral.sh/uv/) (recomendado):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con pip normal:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

Primero, revisa qué versión de Python tienes:

```bash
python3 --version
```

¿Todavía no tienes la 3.11 o más nueva?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

Después, con [uv](https://docs.astral.sh/uv/) (recomendado):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

o con pip normal:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Trabajar en el código de `llmw` mismo

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # debería mostrar todas las pruebas pasando
```

Mira [development.md](development.md) para más detalles sobre cómo contribuir.

### Comprobar que funcionó

```bash
llmw --version
llmw --help
```

### Actualizarla

```bash
uv tool upgrade llmw           # si la instalaste con uv
pipx upgrade llmw              # si la instalaste con pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # con pip normal
```

(Si instalaste el plugin de Claude Code, actualizarlo desde el
marketplace también actualiza automáticamente la herramienta de línea de
comandos — mira [hooks.md](hooks.md).)

### Quitarla

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
