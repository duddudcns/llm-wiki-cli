# Installation

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · **Français**

## Recommandé : plugin Claude Code

Si vous utilisez `llmw` depuis Claude Code, installez-le comme plugin — c'est
la solution recommandée, et elle ne demande aucune étape séparée avec
`pip`/`uv`/`pipx` :

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(équivalents non interactifs : `claude plugin marketplace add duddudcns/llm-wiki-cli`
et `claude plugin install llm-wiki@llm-wiki-cli`)

Cela installe aussi quatre filets de sécurité : l'un garde automatiquement
l'outil en ligne de commande à jour, l'autre empêche l'IA de sauter
l'étape du wiki pour modifier des fichiers directement, et les deux
derniers lui rappellent de chercher dans le wiki avant de commencer un
nouveau travail et de le mettre à jour une fois le travail terminé —
voir [hooks.md](hooks.md) pour savoir exactement ce qu'ils font et comment
les désactiver si vous n'en voulez pas. Si vous préférez installer vous-même l'outil en ligne de
commande et gérer les mises à jour à la main, passez cette étape et
utilisez plutôt l'une des méthodes ci-dessous — elles ne se gênent pas,
vous pouvez installer les deux.

## Plugin Codex

Installez [uv](https://docs.astral.sh/uv/) d'abord (si `uvx --version` n'est pas disponible), puis installez la marketplace et le plugin :

```powershell
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

Vérifiez avec `codex plugin list`. Le plugin expose les outils du wiki de manière native par un serveur MCP, qu'il lance automatiquement avec `uvx` en utilisant votre version épinglée depuis GitHub — il n'y a donc pas besoin d'installer l'outil en ligne de commande `llmw` séparément. Codex n'exécute pas les fichiers de filets de sécurité du plugin Claude Code — il dispose de ses propres filets de sécurité PreToolUse/Stop séparés (mêmes rappels de chercher avant et de mettre à jour après, adaptés à la surface des outils de Codex), qui installent automatiquement une version épinglée de `llmw` en arrière-plan à la première utilisation. Une installation manuelle de l'outil en ligne de commande n'est encore nécessaire que si vous voulez l'utiliser directement en terminal ou dans un script automatisé.

## Outil en ligne de commande (sans le plugin)

Choisissez cette option si vous voulez utiliser `llmw` en dehors de
Claude Code — dans un script, dans un pipeline automatisé, ou avec un
autre éditeur/outil.

`llmw` nécessite **Python 3.11 ou une version plus récente**. Il n'est pas
encore publié sur un dépôt public de paquets, donc il s'installe
directement depuis ce dépôt GitHub public — comme le dépôt est public,
aucune connexion GitHub ni clé SSH n'est nécessaire.

Chaque méthode ci-dessous vous donne une commande `llmw` que vous pouvez
utiliser depuis n'importe où, sans toucher aux autres projets Python sur
votre ordinateur.

### Windows

Vérifiez d'abord quelle version de Python vous avez (PowerShell ou Git Bash) :

```powershell
python --version
```

Vous n'avez pas encore la 3.11 ou plus récente ?

```powershell
winget install Python.Python.3.12
```

ou téléchargez l'installeur depuis [python.org/downloads](https://www.python.org/downloads/).

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé — rapide, pas
besoin d'installer pipx séparément) :

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec [pipx](https://pipx.pypa.io/) :

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec pip tout simple (cela installe dans la configuration Python
actuellement active sur votre ordinateur — ne faites ça que si c'est
vraiment ce que vous voulez) :

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Les filets de sécurité du plugin Claude Code (voir [hooks.md](hooks.md))
> ont besoin de « Git Bash » installé sur Windows pour fonctionner. S'il
> est absent, ces fonctionnalités supplémentaires ne se lancent tout
> simplement pas — `llmw` lui-même continue de fonctionner normalement, et
> garde ses propres vérifications de sécurité dans tous les cas.

### macOS

Vérifiez d'abord quelle version de Python vous avez :

```bash
python3 --version
```

Vous n'avez pas encore la 3.11 ou plus récente ?

```bash
brew install python@3.12
```

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé) :

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec [pipx](https://pipx.pypa.io/) :

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec pip tout simple :

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

Vérifiez d'abord quelle version de Python vous avez :

```bash
python3 --version
```

Vous n'avez pas encore la 3.11 ou plus récente ?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

Ensuite, avec [uv](https://docs.astral.sh/uv/) (recommandé) :

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec [pipx](https://pipx.pypa.io/) :

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

ou avec pip tout simple :

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Travailler sur le code de `llmw` lui-même

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # tous les tests devraient passer
```

Voir [development.md](development.md) pour en savoir plus sur comment contribuer.

### Vérifier que ça a marché

```bash
llmw --version
llmw --help
```

### Mettre à jour

```bash
uv tool upgrade llmw           # si installé avec uv
pipx upgrade llmw              # si installé avec pipx
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # avec pip tout simple
```

(Si vous avez installé le plugin Claude Code, mettre le plugin à jour
depuis la marketplace met aussi automatiquement à jour l'outil en ligne de
commande — voir [hooks.md](hooks.md).)

### Désinstaller

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
