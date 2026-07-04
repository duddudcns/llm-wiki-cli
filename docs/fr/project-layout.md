# Disposition du projet, adoption d'un wiki existant, et compatibilité Obsidian

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · **Français**

## Disposition du projet : classique vs `ai-wiki/`

Par défaut (`--layout classic`) `raw/`, `wiki/`, et `.llmw/` s'assoient directement dans la racine du projet. Passez `--layout ai-wiki` pour les imbriquer un niveau plus bas à la place, gardant la racine désencombré :

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # même contenu que la disposition classique, imbriqué
.claude/skills/llm-wiki/       # crée toujours à la vraie racine du projet
.claude-plugin/plugin.json     # crée toujours à la vraie racine du projet
```

Chaque commande auto-détecte la disposition qu'un projet utilise — elle vérifie d'abord `.llmw/` directement dans la racine du projet, puis revient à `ai-wiki/.llmw`. Les projets à disposition classique existants ne nécessitent pas de migration.

Si un projet ne peut pas être auto-détecté depuis le répertoire courant (par exemple un script s'exécutant ailleurs, ou un checkout non-standard), pointez `llmw` vers lui explicitement avec `--root <path>` ou la variable d'environnement `LLMW_ROOT` — soit l'une soit vérifiée pour les deux dispositions, donc une seule valeur suffit (pas besoin de spécifier `raw/`/`wiki/`/`.llmw/` individuellement) :

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Adoption d'un wiki existant

Si `raw/`/`wiki/` (ou un équivalent imbriqué `ai-wiki/`) a déjà du contenu réel dans ses propres conventions — par exemple un wiki de motif Karpathy fait à la main qui précède `llmw` — utilisez `--adopt` à la place d'un `init` simple :

```bash
llmw init --adopt                  # ou: llmw init --layout ai-wiki --adopt
```

`--adopt` crée `.llmw/` et `config.toml` à la première exécution, mais n'écrit jamais les fichiers de contenu par défaut (`raw/README.md`, `wiki/index.md`, `wiki/overview.md`, `wiki/log.md`) ou les sous-dossiers de taxonomie par défaut (`entities/`, `concepts/`, `decisions/`, `syntheses/`, `projects/`, `glossary/`, `archived/`, `sources/`) — **pas même avec `--force`** — donc le contenu pré-existant à ces chemins n'est jamais touché ou écrasé. Une fois que `config.toml` existe, `--force` ne le réécrit jamais avec des défauts non plus, donc les remplacements ajustés à la main pour le schéma adopté (voir ci-dessous) survivent un re-`init --adopt --force`. Un simple `llmw init` (sans `--adopt`) crée toujours ces défauts, les écrase sur `--force`, et réinitialise également `config.toml` aux défauts sur `--force` ; ne l'utilisez que contre un répertoire vide (ou déjà géré par llmw). Les bizarreries du schéma existant (par exemple un champ `last_updated` au lieu de `created`/`updated`, ou des fichiers `index.md`/`log.md` au niveau racine en dehors de `wiki/`) sont traitées via les `lint.required_frontmatter` et `paths.extra_root_pages` de `.llmw/config.toml` — voir ci-dessous.

## Adaptation de llmw à un wiki existant

Si un wiki a déjà ses propres conventions (champs de frontmatter différents, fichiers de niveau supérieur vivant en dehors de `wiki/`), pointez `llmw init --adopt` vers sa racine (voir ci-dessus) et ajustez `.llmw/config.toml` plutôt que de réorganiser les fichiers du wiki :

```toml
[paths]
# Fichiers Markdown individuels supplémentaires (relatifs à la racine du projet) à indexer
# aux côtés de wiki/**/*.md — par exemple un fichier de schéma/index/log conservé en dehors de wiki/.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Remplacer quelles clés de frontmatter `llmw lint` nécessite. Par défaut
# ["type", "status", "created", "updated"] ; "updated" accepte aussi une
# clé `last_updated`.
required_frontmatter = ["type", "status", "last_updated"]
```

Aucune page existante ne doit changer — `llmw rebuild` récupère la nouvelle config à la prochaine exécution.

## Compatibilité Obsidian

`wiki/` est du Markdown simple avec frontmatter YAML et `[[wikilinks]]` — ouvrez-le directement comme un coffre Obsidian pour obtenir la vue graphique, backlinks, et recherche dans une GUI, sans renoncer à aucun du flux de travail de l'agent piloté par la CLI.

La résolution de liens traite spécifiquement les bizarreries réelles d'export Obsidian :

- `[[Page]]`, `[[Page|Alias]]`, `[[Page#Heading|Alias]]`, `[[#Heading]]`, `![[Embed]]` — grammaire de wikilink complète.
- Les cibles de wikilink de type chemin (`[[concepts/foo]]`) se résolvent relatif à la **racine du coffre** (`wiki/`), correspondant à la façon dont Obsidian les résout quand vous ouvrez réellement `wiki/` en tant que coffre — pas juste relatif au dossier propre de la page de liaison.
- Le frontmatter `related:` est une source de lien de première classe, même que les wikilinks en ligne — tant un chemin simple/titre (`related: [wiki/concepts/foo]`, la convention que certains wikis utilisaient avant d'adopter `llmw`) que le propre format Properties-panel d'Obsidian (`related: ["[[Note]]"]`) se résolvent correctement.
- Les liens Markdown avec cibles codées en URL (`[Profile](Project%20Profile.md)`, courant quand un nom de fichier a des espaces) sont décodés avant de correspondre à des pages sur disque.
- Les wikilinks relatifs qui pointent en dehors de `wiki/` (par exemple `[[../notes/x]]`) sont vérifiés contre le système de fichiers réel — ils sont uniquement rapportés comme rompus par `llmw lint` si la cible n'existe vraiment nulle part dans le projet, pas simplement parce qu'elle n'est pas une page wiki indexée.

**Où le graphe diverge délibérément d'Obsidian** : les bords `related:` et la résolution de wikilink basée sur le titre de llmw (`[[Exact Page Title]]` se résolvant même quand cela ne correspond pas au nom de fichier) sont tous deux des extensions llmw sans équivalent Obsidian — la propre vue graphique d'Obsidian ne montrera pas ces bords. Deux pages avec le même stem de nom de fichier dans des dossiers différents se résolvent aussi ambiguïment (première correspondance gagne) dans les deux outils. Ouvrir `wiki/` dans Obsidian vous obtient un vrai graphe utile sur les mêmes fichiers, pas un pixel-identique.
