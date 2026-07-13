# Organiser votre wiki, et utiliser un wiki déjà existant

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · **Français**

## Deux façons d'organiser les dossiers

Par défaut, `llmw init` place les dossiers `raw/`, `wiki/`, et le dossier
technique en coulisse directement dans le dossier principal de votre
projet. Si vous préférez garder votre dossier de projet bien rangé, vous
pouvez tout glisser dans un sous-dossier appelé `ai-wiki/` à la place :

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # les mêmes dossiers qu'avant, juste un niveau plus bas
.claude/skills/llm-wiki/       # reste toujours dans le dossier principal de votre projet
.claude/rules/llm-wiki.md      # reste aussi toujours dans le dossier principal de votre projet
.codex/rules/llm-wiki.md       # reste aussi toujours dans le dossier principal de votre projet
.claude-plugin/plugin.json     # reste toujours dans le dossier principal de votre projet
```

Chaque commande détecte automatiquement le style que vous utilisez — vous
n'avez jamais besoin de le préciser à nouveau après le premier `init`. Si
vous avez déjà des notes organisées de la façon classique, vous n'avez
rien à changer.

Si vous lancez `llmw` depuis un endroit en dehors du dossier de projet
(par exemple depuis un script), vous pouvez simplement lui indiquer où
chercher, et il devinera tout seul lequel des deux styles de dossiers
vous utilisez :

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Utiliser `llmw` avec un wiki que vous avez déjà créé à la main

Peut-être avez-vous déjà votre propre ensemble de notes, créé avant même
de connaître cet outil, et vous voulez juste que `llmw` commence à s'en
occuper. Utilisez `--adopt` plutôt qu'un simple `init` :

```bash
llmw init --adopt                  # ou : llmw init --layout ai-wiki --adopt
```

Cela met en place l'index de recherche en coulisse, mais ne **créera** ni
n'**écrasera** jamais aucune de vos notes ou de vos dossiers existants —
même si vous relancez plus tard la commande avec `--force`. Votre fichier
de configuration est protégé de la même manière, donc les réglages
personnalisés que vous avez faits ne seront jamais réinitialisés par
accident. (Un simple `llmw init`, sans `--adopt`, se comporte
différemment : il crée bien quelques notes et dossiers de départ, et
`--force` les écrasera — donc n'utilisez la version simple que sur un
projet tout neuf et vide.)

## Adapter `llmw` à des notes qui suivent des règles différentes

Si vos notes existantes sont organisées un peu différemment — par
exemple, certains fichiers importants se trouvent en dehors du dossier
`wiki/`, ou ils utilisent des étiquettes différentes de celles attendues
par `llmw` — vous n'avez pas besoin de tout réorganiser. Il suffit
d'ajuster un petit fichier de configuration, après avoir adopté le wiki
comme montré ci-dessus :

```toml
[paths]
# Fichiers de notes individuels supplémentaires (en dehors du dossier wiki/
# habituel) qui doivent quand même être inclus dans la recherche — par
# exemple un fichier d'index ou de journal gardé au niveau racine.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Quelles informations chaque note est censée avoir en haut.
# La valeur par défaut est ["type", "status", "created", "updated"] ;
# "updated" accepte aussi une note qui utilise plutôt "last_updated".
required_frontmatter = ["type", "status", "last_updated"]
```

Aucune de vos notes existantes n'a besoin de changer pour que cela
fonctionne.

## Utiliser `llmw` avec Obsidian

Chaque note est un simple fichier texte, donc vous pouvez aussi ouvrir le
dossier `wiki/` directement dans l'application de prise de notes très
connue [Obsidian](https://obsidian.md/) — vous obtenez sa vue en carte
visuelle, sa vue « qui pointe vers cette note », et sa recherche, le tout
sur les mêmes notes, sans rien perdre de la façon dont l'IA les utilise.

Certains détails sur la façon dont les notes se relient entre elles sont
conçus pour correspondre à ce que fait Obsidian lui-même, y compris
quelques cas particuliers délicats :

- Tous les styles de liens d'Obsidian sont reconnus : un lien simple vers
  une autre note, un lien avec un nom d'affichage personnalisé, un lien
  vers un titre précis à l'intérieur d'une note, et une « intégration »
  qui reprend le contenu d'une autre note.
- Un lien qui contient un chemin de dossier est interprété exactement
  comme Obsidian l'interprète — relatif au sommet du wiki, pas relatif à
  la note dans laquelle le lien est écrit.
- Les notes peuvent aussi lister des « notes liées » en haut, dans
  plusieurs formats différents, et les deux sont reconnus correctement.
- Les liens vers des fichiers dont le nom contient des espaces ou des
  caractères spéciaux (fréquent quand des notes sont exportées depuis
  d'autres outils) sont quand même correctement associés.
- Un lien qui pointe en dehors du dossier `wiki/` est vérifié par rapport
  à ce qui existe réellement sur le disque, donc il n'est signalé comme
  cassé que s'il n'existe vraiment nulle part.

**Quelques petites différences avec le vrai Obsidian** : cet outil
comprend quelques types de connexions supplémentaires entre les notes
(comme la liste de « notes liées » mentionnée plus haut) que la vue en
carte d'Obsidian ne montrera pas, car ces connexions sont propres à cet
outil. Et si deux notes ont exactement le même nom de fichier dans des
dossiers différents, cet outil et Obsidian peuvent tous les deux parfois
choisir la mauvaise note quand un lien ne précise pas de quel dossier il
s'agit. Pour tout le reste, ça correspond.
