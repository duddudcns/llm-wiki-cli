# Contribuer à `llmw`

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · **Français**

Voir la section « Travailler sur le code de `llmw` lui-même » de
[installation.md](installation.md) pour mettre en place un environnement
de développement ; lancez `pytest` depuis là pour exécuter la suite de
tests.

## Comment fonctionne la compétence Claude Code

`llmw init` écrit quelques fichiers dans `.claude/skills/llm-wiki/` de
votre projet. Claude Code les reconnaît automatiquement — aucune étape
d'installation séparée n'est nécessaire. Ces fichiers apprennent à l'IA
quand et comment utiliser `llmw`, sans avoir besoin de charger tous les
détails à chaque fois.

Si vous avez déjà installé le plugin Claude Code depuis la marketplace,
ajoutez `--no-claude-plugin` en lançant `llmw init` pour éviter de créer
cette copie en plus — sinon vous vous retrouveriez avec deux copies des
mêmes instructions, ce qui est redondant et peut créer de la confusion.

`llmw init` écrit aussi toujours `.claude/rules/llm-wiki.md`, que vous
utilisiez `--no-claude-plugin` ou non. Un manifeste de plugin Claude Code
peut distribuer des hooks et des skills, mais n'a aucun moyen de
distribuer du contenu `.claude/rules/` — c'est donc le seul chemin qui
charge automatiquement, à chaque session, le rappel « chercher avant /
mettre à jour après », sans aucune copie côté marketplace avec laquelle
faire doublon.

De la même manière, `llmw init` écrit aussi le même contenu dans `.codex/rules/llm-wiki.md`, à chaque fois, peu importe quel plugin (ou aucun) vous utilisez réellement — un manifeste de plugin Codex a exactement le même gap que celui de Claude Code : « des hooks et des skills oui, du contenu `.codex/rules/` non ». C'est écrit inconditionnellement plutôt que d'être gâté derrière un drapeau propre à Codex : un fichier de règles inutilisé pour une plateforme que personne n'utilise sur ce projet est inoffensif, tandis qu'une équipe qui mélange Claude Code et Codex les récupère tous les deux déjà configurés sans travail supplémentaire.

## Ce que cet outil ne fait volontairement pas (pour l'instant)

Par choix, cela reste hors du périmètre pour l'instant : se connecter
directement à des modèles d'IA, surveiller automatiquement les fichiers
pour détecter des changements, la recherche sémantique par IA, lire
directement des fichiers PDF ou Word, une application graphique, ou toute
fusion, suppression ou résolution de conflit automatique des notes.
