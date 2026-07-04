# Desarrollo

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · **Español** · [Français](../fr/development.md)

Ver la sección "Clon local, instalación editable" de [installation.md](installation.md)
para configurar un entorno de dev; `pytest` ejecuta el conjunto de pruebas desde
allí.

## Habilidad de Claude Code

`llmw init` escribe `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}`
en el proyecto. Claude Code auto-descubre esto como una habilidad plana — sin
paso de instalación. Le dice al agente cuándo alcanzar `llmw`, el flujo de trabajo central
búsqueda-primero, y apunta a `reference.md`/`examples.md` para detalle completo así que el siempre cargado `SKILL.md` permanece corto.

Si el plugin de Claude Code llm-wiki ya está instalado desde el
mercado, pasa `--no-claude-plugin` para omitir esta copia de proyecto-local —
de otra manera el proyecto termina con dos copias de la misma habilidad (del
plugin de mercado, y esta), que es redundante y puede ser
confuso cuando Claude Code carga ambas.

## Alcance MVP

Deliberadamente excluye: un servidor MCP, modo daemon/watch, búsqueda de embedding/vector,
análisis directo de PDF/DOCX, un plugin Obsidian, una interfaz web, y cualquier
lógica de auto-merge/auto-delete/detección de contradicción.
