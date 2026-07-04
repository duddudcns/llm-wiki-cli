# Développement

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · **Français**

Voir la section "Clone local, installation éditable" de [installation.md](installation.md) pour configurer un environnement de dev ; `pytest` exécute la suite de tests à partir de là.

## Compétence Claude Code

`llmw init` écrit `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}` dans le projet. Claude Code découvre ceci automatiquement comme une compétence simple — aucune étape d'installation. Elle dit à l'agent quand atteindre `llmw`, le flux de travail central recherche-d'abord, et pointe vers `reference.md`/`examples.md` pour le détail complet afin que le toujours-chargé `SKILL.md` reste court.

Si le plugin Claude Code llm-wiki est déjà installé depuis la place de marché, passez `--no-claude-plugin` pour ignorer cette copie locale du projet — autrement le projet se retrouve avec deux copies de la même compétence (la place de marché du plugin, et celle-ci), qui est redondant et peut être confus quand Claude Code charge les deux.

## Étendue MVP

Exclut délibérément : un serveur MCP, mode daemon/watch, recherche par embedding/vecteur, analyse directe de PDF/DOCX, un plugin Obsidian, une UI web, et toute logique d'auto-fusion/auto-suppression/détection de contradiction.
