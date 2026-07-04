# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · **Français**

Interface CLI sans tête de type Obsidian pour wiki LLM destinée aux agents IA.

## Pourquoi

Les outils MCP sont pratiques, mais les schémas d'outils et les longues instructions consomment du contexte à chaque tour. `llmw` adopte une approche différente : une petite CLI déterministe plus une compétence Claude Code. L'agent appelle le wiki uniquement quand il en a besoin, et la CLI elle-même n'appelle jamais un modèle — elle indexe, recherche et valide simplement.

## Concepts

- **Wiki LLM Karpathy** — `raw/` contient le matériel source immuable ; `wiki/` est une couche de connaissances persistante que l'agent IA écrit et maintient ; ce n'est pas une RAG ordinaire, le wiki est un artefact composé.
- **Wikilinks de style Obsidian** — `[[Page]]`, `[[Page|Alias]]`, `[[Page#Heading]]`, `![[Embed]]`, backlinks, tags, frontmatter YAML. `wiki/` est un coffre Obsidian valide ; ouvrez-le là-bas si vous voulez un IDE visuel humain sur les mêmes fichiers.
- **Markdown comme source de vérité** — `.llmw/index.sqlite` et `.llmw/graph.json` sont des données dérivées, reconstructibles. `llmw rebuild` régénère les deux à partir de `wiki/*.md` seul.
- **L'agent IA écrit le wiki ; la CLI indexe et le valide** — recherche (SQLite FTS5), backlinks, notation des pages connexes, et lint sont tous déterministes, basés sur des règles, et sans modèle. Résumer les sources, écrire des pages, et décider quoi archiver est le travail de l'agent.

## Installer

**Recommandé : plugin Claude Code** — aucune étape séparée `pip`/`uv`/`pipx` :

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

Cela installe également des hooks qui gardent la CLI elle-même synchronisée automatiquement et empêchent les agents de la contourner — voir [docs/fr/hooks.md](docs/fr/hooks.md).

Vous voulez la CLI autonome directement à la place (scripting, CI, un autre éditeur), ou gérer les mises à jour vous-même ? Voir [docs/fr/installation.md](docs/fr/installation.md) pour la matrice d'installation uv/pipx/pip/dev complète, divisée par Windows/macOS/Linux. Les deux ne sont pas en conflit — vous pouvez installer les deux.

## Démarrage rapide

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` crée :

```text
raw/                          # matériel source immuable
wiki/                         # couche de connaissances maintenue par l'agent
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # index/cache/sauvegardes/verrous dérivés (reconstructibles)
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # métadonnées de plugin optionnelles pour ce projet
```

Passez `--layout ai-wiki` pour imbriquer `raw/`/`wiki/`/`.llmw/` sous un dossier `ai-wiki/` à la place (auto-détecté par chaque commande après), et `--adopt` pour pointer `llmw` vers un wiki qui a déjà du contenu réel dans ses propres conventions sans y scaffolder par-dessus — voir [docs/fr/project-layout.md](docs/fr/project-layout.md).

## Flux de travail de l'agent

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## Référence des commandes

Toutes les commandes acceptent `--json` pour une sortie analysable par machine ; la plupart des lectures par défaut à une vue brève et bon marché en contexte (`--full`/`--no-brief` pour plus).

| Commande | Objectif |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Créer `raw/`, `wiki/`, `.llmw/` (imbriqué sous `ai-wiki/` avec `--layout ai-wiki`), et (par défaut) la compétence/plugin Claude Code. `--adopt` ignore le contenu par défaut/l'échafaudage de taxonomie et protège `config.toml` de `--force`, pour préserver le contenu wiki existant et ses remplacements de configuration |
| `llmw status [--brief\|--json]` | Comptes de pages, liens rompus, orphelins, heure du dernier index, pages modifiées |
| `llmw rebuild` | Réindexation complète de `wiki/**/*.md` à partir de zéro |
| `llmw index [--changed\|--all]` | Réindexation incrémentale (par défaut) ou complète |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | Recherche FTS5 SQLite sur titre/résumé/corps — voir [docs/fr/commands.md](docs/fr/commands.md) pour la sémantique de recherche |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Chercher une page ; brief affiche titre/type/résumé/points clés/liens/nombre de backlinks |
| `llmw links <target>` | Liens sortants, avec statut des liens rompus |
| `llmw backlinks <target>` | Liens entrants |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Candidats de pages connexes déterministes (aucun appel de modèle) |
| `llmw ingest <raw/...>` | Enregistrer une source `.md`/`.txt` comme un brouillon `wiki/sources/<slug>.md` |
| `llmw write <path> --reason "..." --stdin [--force]` | Créer une nouvelle page wiki à partir de stdin |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Remplacement de chaîne exact dans une page existante (même sémantique qu'un outil Edit natif) |
| `llmw patch <path> --reason "..." --stdin` | Appliquer un diff unifié à une page existante (sauvegarde d'abord, revient en arrière en cas d'échec) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Déplacer une page vers `wiki/archived/YYYY/MM/`, tamponner le frontmatter d'archive, enregistrer le changement |
| `llmw lint [--brief\|--json]` | Liens rompus, orphelins, titres/alias dupliqués, frontmatter manquant/invalide, références raw pendantes, liens de pages archivées — rapports uniquement, jamais d'auto-correction |
| `llmw health [--brief]` | Vérifications du système : config, db d'index, version du schéma, répertoires, verrous |
| `llmw graph build` / `llmw graph export --format json\|html` | Régénérer/exporter le graphe de liens |

## Règles de sécurité

- `raw/` est immuable. `write`/`patch`/`archive` refusent tout chemin en dessous.
- Chaque `write`/`patch`/`archive` nécessite `--reason`, enregistré dans `wiki/log.md` et la table `log_entries`.
- Il n'y a pas de `delete` — utilisez `archive`. La valeur par défaut conserve un stub tombeau au chemin d'origine pointant vers le nouvel emplacement.
- `patch` sauvegarde le fichier avant d'appliquer un diff unifié, et laisse l'original intact si le diff ne s'applique pas proprement (inadéquation de contexte).
- Un simple verrou consultatif (`.llmw/locks/write.lock`) protège contre deux processus `llmw` mutant le wiki en même temps.

## Documentation

| Doc | Couvre |
|---|---|
| [docs/fr/installation.md](docs/fr/installation.md) | Matrice d'installation complète de la CLI autonome (Windows/macOS/Linux), mise à jour, désinstallation |
| [docs/fr/hooks.md](docs/fr/hooks.md) | Le garde wiki `PreToolUse` du plugin Claude Code et le hook de synchronisation de version auto-cicatrisant `SessionStart` |
| [docs/fr/commands.md](docs/fr/commands.md) | Sémantique de recherche (fallback sur 3 niveaux, stemming des particules coréennes) |
| [docs/fr/project-layout.md](docs/fr/project-layout.md) | Disposition classique vs `ai-wiki/`, `--root`/`LLMW_ROOT`, `--adopt`, adaptation de `llmw` aux conventions du wiki existant, notes de compatibilité Obsidian |
| [docs/fr/development.md](docs/fr/development.md) | Configuration de dev, la compétence Claude Code, étendue MVP |

## Licence

MIT — voir [LICENSE](LICENSE).
