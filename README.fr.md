# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · **Français**

Un outil en ligne de commande tout simple qui donne à un assistant IA de code son propre carnet de notes (un « wiki ») pour un projet — pour qu'il puisse se souvenir des décisions prises, des informations et de l'historique, au lieu de tout oublier d'une conversation à l'autre.

## Pourquoi utiliser cet outil ?

Beaucoup d'outils IA fonctionnent en collant un gros bloc d'instructions et de données dans chaque message, ce qui gaspille de la place et ralentit tout. `llmw` fait les choses autrement : c'est un petit outil tout simple que l'IA n'utilise que quand elle a vraiment besoin de retrouver une information ou d'en noter une. L'outil lui-même ne « réfléchit » jamais et ne génère pas de texte — il se contente de stocker des notes, de les retrouver plus tard, et de vérifier qu'elles sont bien écrites. Toute la réflexion (quoi écrire, comment le résumer) est faite par l'IA, pas par `llmw`.

## L'idée de base

- **Deux dossiers, deux rôles** — `raw/` contient les documents sources d'origine, qui ne changent jamais (comme un document que vous auriez importé). `wiki/` est l'endroit où l'IA écrit ses propres notes, et continue de les mettre à jour au fur et à mesure qu'elle apprend de nouvelles choses — le carnet devient donc de plus en plus utile avec le temps, au lieu d'être une simple recherche ponctuelle.
- **Des notes qui se relient entre elles** — les pages peuvent renvoyer vers d'autres pages (un peu comme sur Wikipédia), pour que l'IA puisse suivre une piste de notes liées entre elles. Cela fonctionne aussi avec l'application de prise de notes très connue [Obsidian](https://obsidian.md/), si vous voulez parcourir ces mêmes notes vous-même, de façon visuelle.
- **Tout n'est que du texte brut** — chaque note est un simple fichier Markdown que vous pouvez ouvrir et lire vous-même, sans base de données particulière. Il y a aussi un petit fichier d'index de recherche, mais ce n'est qu'un fichier d'appoint qu'on peut toujours régénérer à partir des notes si besoin.
- **L'IA écrit ; l'outil se contente de vérifier et de ranger** — chercher, retrouver des notes liées, et vérifier que les notes sont bien écrites sont toutes des opérations simples et prévisibles, sans aucune IA impliquée. Décider ce qui vaut la peine d'être noté, et bien l'écrire, c'est le travail de l'IA.
- **Elle retient les préférences au fil de l'eau** — mentionnez une convention de code ou une correction en passant pendant que vous travaillez, et l'IA l'enregistre (dans le wiki, ou dans son propre fichier de règles) sans qu'on lui dise « souviens-toi de ça » ou « mets à jour le wiki ». S'il faut le répéter à chaque fois pour que l'outil serve à quelque chose, ce n'est pas un bon outil.

## Installation

**Recommandé : installer comme plugin Claude Code** — seulement deux commandes, rien d'autre à configurer :

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

Cela met aussi en place quelques filets de sécurité utiles qui gardent tout en bon état de fonctionnement tout seuls — voir [docs/fr/hooks.md](docs/fr/hooks.md) pour les détails.

Vous préférez installer directement l'outil en ligne de commande (par exemple pour l'utiliser en dehors de Claude Code) ? Voir [docs/fr/installation.md](docs/fr/installation.md) pour des instructions pas à pas sous Windows, macOS et Linux. Vous pouvez installer les deux — ils ne se gênent pas l'un l'autre.

**Plugin Codex (installation de l'outil en ligne de commande non requise) :**

```powershell
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

Le plugin Codex fournit des compétences détectables par intention, cinq outils MCP natifs (`llmw_init`, `llmw_status`, `llmw_search`, `llmw_read`, `llmw_write`), et ses propres filets de sécurité PreToolUse/Stop qui poussent à chercher avant les modifications et à mettre à jour le wiki après — séparés des filets de Claude Code, qu'ils ne remplacent pas. Le serveur MCP démarre par `uvx`, donc [uv](https://docs.astral.sh/uv/) doit être disponible ; les filets de sécurité installent automatiquement une version épinglée de `llmw` en arrière-plan, comme ceux de Claude Code le font, donc là non plus aucune installation manuelle n'est nécessaire.

## Démarrage rapide

```bash
mkdir my-project && cd my-project
llmw init
llmw rebuild
llmw status --brief
```

`llmw init` crée pour vous cette structure de dossiers :

```text
raw/                          # documents sources d'origine — jamais modifiés
wiki/                         # les propres notes de l'IA, qu'elle continue de mettre à jour
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # index de recherche interne (construit par `llmw rebuild`, peut être reconstruit à tout moment)
.claude/skills/llm-wiki/      # apprend à Claude Code comment utiliser cet outil
.claude/rules/llm-wiki.md     # pousse Claude Code à chercher avant et mettre à jour après, automatiquement
.codex/rules/llm-wiki.md      # même nudge, pour Codex — écrit à chaque init peu importe quel plugin vous utilisez
.claude-plugin/plugin.json    # informations facultatives sur le plugin pour ce projet
```

Vous préférez garder votre dossier de projet plus rangé en glissant tout ça dans un sous-dossier ? Ou pointer `llmw` vers un wiki que vous avez déjà créé vous-même à la main ? Voir [docs/fr/project-layout.md](docs/fr/project-layout.md).

## Un flux de travail IA typique

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## Toutes les commandes

La plupart des commandes acceptent `--json` si vous voulez un résultat dans un format lisible par un programme — les exceptions sont `write`/`edit`/`patch`/`archive`/`ingest`, qui ne rapportent le succès ou l'échec qu'en texte brut. La plupart des commandes de « lecture » affichent par défaut un résumé court (ajoutez `--full`/`--no-brief` pour tout voir).

| Commande | Ce qu'elle fait |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Met en place `raw/`, `wiki/` et l'index de recherche pour un nouveau projet (ou un projet existant, avec `--adopt` — voir [docs/fr/project-layout.md](docs/fr/project-layout.md)) |
| `llmw status [--brief\|--json]` | Vérification rapide : combien de notes existent, s'il y a des liens cassés, quand tout a été mis à jour pour la dernière fois |
| `llmw rebuild` | Reconstruit entièrement l'index de recherche depuis le début |
| `llmw index [--changed\|--all]` | Met à jour l'index de recherche (uniquement ce qui a changé, par défaut) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | Cherche dans toutes les notes — voir [docs/fr/commands.md](docs/fr/commands.md) pour comprendre comment la recherche fonctionne |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Ouvre une note ; la version courte montre le titre, le résumé et les liens |
| `llmw links <target>` | Montre vers quoi une note pointe |
| `llmw backlinks <target>` | Montre quelles autres notes pointent vers celle-ci |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Suggère des notes liées, à partir de règles simples (aucune supposition de l'IA) |
| `llmw ingest <raw/...>` | Transforme un document source en brouillon de note, prêt à être complété par l'IA |
| `llmw write <path> --reason "..." --stdin [--force]` | Crée une toute nouvelle note |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Remplace un passage exact de texte dans une note existante |
| `llmw patch <path> --reason "..." --stdin` | Applique un ensemble de modifications à une note (garde d'abord une sauvegarde, et annule tout automatiquement en cas de problème) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Met une vieille note de côté au lieu de la supprimer, et laisse une note à sa place indiquant son nouvel emplacement |
| `llmw lint [--brief\|--json]` | Repère les problèmes — liens cassés, informations manquantes, titres en double — mais ne les corrige jamais automatiquement |
| `llmw health [--brief]` | Vérifie que tout ce qui tourne en coulisse est correctement configuré |
| `llmw graph build` / `llmw graph export --format json\|html` | Construit ou exporte une carte visuelle des liens entre les notes |

## Règles de sécurité intégrées

- Les documents sources d'origine dans `raw/` ne peuvent jamais être modifiés — l'outil refuse tout simplement.
- Chaque modification d'une note doit s'accompagner d'une courte raison, qui est consignée dans un journal permanent.
- Il n'y a pas de « suppression » — seulement une « mise en archive », qui déplace une note de côté et laisse un panneau indicateur derrière elle, pour que rien ne disparaisse simplement.
- Appliquer un ensemble de modifications fait toujours d'abord une sauvegarde, et annule tout automatiquement si quelque chose tourne mal en cours de route.
- Un simple fichier de verrouillage empêche deux copies de l'outil de modifier les mêmes notes en même temps et de se marcher dessus.

## Pour aller plus loin

| Doc | Ce qu'on y trouve |
|---|---|
| [docs/fr/installation.md](docs/fr/installation.md) | Instructions d'installation complètes pour Windows, macOS et Linux ; comment mettre à jour ou désinstaller |
| [docs/fr/hooks.md](docs/fr/hooks.md) | Comment le plugin Claude Code empêche l'IA de contourner le wiki, et se met à jour tout seul |
| [docs/fr/commands.md](docs/fr/commands.md) | Comment la recherche fonctionne vraiment en coulisse |
| [docs/fr/project-layout.md](docs/fr/project-layout.md) | Différentes façons d'organiser les dossiers du wiki, comment adopter un wiki déjà créé, comment l'utiliser avec l'application de prise de notes Obsidian |
| [docs/fr/development.md](docs/fr/development.md) | Mettre en place un environnement de développement pour travailler sur `llmw` lui-même |

## Licence

MIT — voir [LICENSE](LICENSE).
