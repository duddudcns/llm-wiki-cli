# Installation

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · **Français**

## Recommandé : plugin Claude Code

Si vous utilisez `llmw` depuis Claude Code, installez-le comme plugin — c'est le chemin recommandé et ne nécessite aucune étape séparée `pip`/`uv`/`pipx` :

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(équivalents non-interactifs : `claude plugin marketplace add duddudcns/llm-wiki-cli` et `claude plugin install llm-wiki@llm-wiki-cli`)

Cela installe la compétence Claude Code plus deux hooks qui gardent le binaire `llmw` autonome installé et synchronisé automatiquement, et empêchent les agents de le contourner — voir [hooks.md](hooks.md) pour savoir exactement ce que ces hooks font et comment les configurer. Si vous préférez gérer l'installation de la CLI vous-même, sautez ceci et utilisez l'une des méthodes ci-dessous à la place — elles ne sont pas en conflit, vous pouvez également installer les deux.

## CLI autonome

Choisissez ceci si vous voulez `llmw` sur PATH en dehors de Claude Code (scripting, CI, un autre éditeur/agent), ou si vous préférez contrôler les mises à jour manuellement au lieu du hook d'auto-cicatrisation du plugin.

`llmw` nécessite **Python 3.11 ou ultérieur**, et n'est pas encore sur PyPI, il s'installe donc directement depuis ce dépôt plutôt que d'un index de paquet. **Ce dépôt est actuellement privé** — l'installation (n'importe quelle méthode ci-dessous) nécessite votre propre `git` authentifié (par exemple déjà connecté via `gh auth login`, ou une clé SSH sur votre compte GitHub) ; quiconque sans accès au dépôt obtient une erreur de récupération, pas une installation partielle.

Toutes les méthodes ci-dessous vous donnent une commande `llmw` globale sans toucher aux dépendances de tout autre projet Python.

### Windows

Vérifiez d'abord votre version Python (PowerShell ou Git Bash) :

```powershell
python --version
```

N'avez-vous pas encore 3.11+ ?

```powershell
winget install Python.Python.3.12
```

ou téléchargez le programme d'installation depuis [python.org/downloads](https://www.python.org/downloads/).

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé — rapide, aucune installation pipx séparée nécessaire) :

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou [pipx](https://pipx.pypa.io/) :

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou pip simple (installe dans n'importe quel environnement Python actuellement actif — utilisez un venv à moins que vous sachiez que vous le voulez globalement) :

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Les hooks du plugin Claude Code (voir [hooks.md](hooks.md)) ont besoin de Git Bash sur Windows — Claude Code revient à PowerShell quand Git Bash n'est pas installé, que ces hooks de forme shell ne supportent pas. La porte de sécurité propre de `llmw` tient toujours de toute façon ; seule la commodité supplémentaire des hooks est affectée.

### macOS

Vérifiez d'abord votre version Python :

```bash
python3 --version
```

N'avez-vous pas encore 3.11+ ?

```bash
brew install python@3.12
```

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé) :

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou [pipx](https://pipx.pypa.io/) :

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou pip simple :

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

Vérifiez d'abord votre version Python :

```bash
python3 --version
```

N'avez-vous pas encore 3.11+ ?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé) :

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou [pipx](https://pipx.pypa.io/) :

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou pip simple :

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Clone local, installation éditable (pour contribuer à `llmw` lui-même)

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # devrait afficher tous les tests réussis
```

Voir [development.md](development.md) pour le reste du flux de travail de dev.

### Vérifier

```bash
llmw --version
llmw --help
```

### Mise à jour

```bash
uv tool upgrade llmw           # si installé via uv
pipx upgrade llmw              # si installé via pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # pip simple
```

(Si vous utilisez le plugin Claude Code, la mise à jour du plugin depuis la place de marché garde également la CLI autonome synchronisée automatiquement — voir [hooks.md](hooks.md).)

### Désinstallation

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
