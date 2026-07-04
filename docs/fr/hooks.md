# Hooks : garder les agents honnêtes et la CLI synchronisée

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · **Français**

Le plugin Claude Code (voir [installation.md](installation.md)) installe deux hooks. Ni l'un ni l'autre n'est requis pour utiliser `llmw` — ce sont des commodités superposées sur une CLI qui applique déjà ses propres règles de sécurité indépendamment de l'exécution d'un hook.

## PreToolUse : le garde wiki

Rien n'arrête un agent d'ignorer la compétence Claude Code et d'éditer directement `wiki/*.md` ou `raw/**` avec ses propres outils d'édition de fichier au lieu de `llmw` — cela ignore le journal d'audit `--reason`, la validation du frontmatter, et la sauvegarde automatique, et c'est ce qui se passe en pratique chaque fois qu'un *different*, ensemble concurrent d'instructions est en vigueur et ne mentionne jamais `llmw`.

Installé en tant que plugin Claude Code (pas une compétence de projet `llmw init` brut), un hook `PreToolUse` ferme cette brèche au niveau du harnais : un appel natif `Edit`/`Write`/`NotebookEdit` ciblant `wiki/*.md` ou `raw/**` est refusé (ou, selon la config, transformé en invite de confirmation), et le message de refus nomme la commande `llmw` exacte à exécuter à la place — donc l'action très suivante de l'agent est une réécriture d'une ligne, pas une impasse.

Le garde ne regarde que les appels `Edit`/`Write`/`NotebookEdit` dont la cible se résout (en marchant jusqu'à partir du fichier, de la même manière que `llmw` trouve sa propre racine de projet) vers un vrai projet llmw `wiki/*.md` ou `raw/**` — tout le reste, y compris les `Read` simples, passe intact, et il n'inspecte jamais les commandes `Bash` (la police des chaînes shell est sa propre mine terrestre de faux positifs, donc le journal d'audit dans `wiki/log.md` plus `llmw lint` restent la couche de détection pour cette brèche à la place qu'un hook essayant de le bloquer).

Configurez ou désactivez-le par projet dans `.llmw/config.toml` :

```toml
[hooks]
wiki_guard = "deny"  # par défaut : bloquer, avec un message nommant le fix llmw
# wiki_guard = "ask"   # demander une confirmation au lieu de bloquer
# wiki_guard = "off"   # désactiver le garde pour ce projet
```

Les deux hooks nécessitent Git Bash sur Windows (Claude Code revient à PowerShell quand Git Bash n'est pas installé, que ces hooks de forme shell ne supportent pas) — partout ailleurs, la porte de sécurité propre de `llmw` (raison requise, chemin confiné, frontmatter validé, sauvegarde avant écriture) tient toujours indépendamment de l'exécution du hook.

Laisse également tomber une brève note `SessionStart` dans le contexte chaque session : "ce projet a un wiki llmw" (avec nombre de pages) quand `.llmw` existe déjà, ou un indice d'une ligne "exécuter `llmw init`" quand ce n'est pas encore le cas — donc un environnement vierge sans projet `CLAUDE.md`, et aucun wiki initialisé du tout, découvre toujours `llmw` au tour un.

## SessionStart : auto-cicatrisation de l'installation de la CLI

`plugin/bin/llmw` est un despatcheur mince, pas une distribution Python regroupée — il s'exécute vers un vrai `llmw` sur PATH. La mise à jour du plugin à partir de la place de marché ne met à jour que les propres fichiers du plugin (compétence, hooks) ; elle ne touche **pas** ce binaire autonome. Laissé seul, cela signifie l'installation d'une mise à jour de plugin peut silencieusement vous laisser exécutant une ancienne CLI en dessous d'elle.

Un hook `SessionStart` (`plugin/hooks/session-start.sh`, câblé via `plugin/hooks/hooks.json`) ferme cette brèche : chaque session, il compare le `llmw --version` installé contre la version que ce bundle de plugin déclare (`plugin/.claude-plugin/plugin.json`). Sur une inadéquation — y compris "pas du tout installé" — il (réinstalle via `uv tool install --force` (revenant à `pip install --user --force-reinstall`), épinglé à la balise `git` correspondante (`git+...@v<version>`), donc une mise à jour de plugin-marketplace apporte également le binaire CLI autonome en synchronisation sans une `uv tool upgrade llmw` manuelle séparée.

Quand les versions correspondent déjà, la vérification est juste un appel local `llmw --version` (pas de réseau) chaque session — le chemin réinstall ne s'exécute que sur une dérive de version authentique, environ une fois par libération.
