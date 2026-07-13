# Contribuir a `llmw`

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · **Español** · [Français](../fr/development.md)

Mira la sección "Trabajar en el código de `llmw` mismo" de
[installation.md](installation.md) para preparar un entorno de
desarrollo; desde ahí, corre `pytest` para ejecutar las pruebas.

## Cómo funciona la skill de Claude Code

`llmw init` escribe algunos archivos en `.claude/skills/llm-wiki/` dentro
de tu proyecto. Claude Code los detecta automáticamente — no hace falta
ningún paso de instalación aparte. Estos archivos le enseñan a la IA
cuándo debería usar `llmw` y cómo hacerlo, sin necesitar cargar todo el
detalle cada vez.

Si ya instalaste el plugin de Claude Code desde el marketplace, agrega
`--no-claude-plugin` al correr `llmw init` para no crear esta copia
extra — de lo contrario terminarías con dos copias de las mismas
instrucciones, lo cual es redundante y puede generar confusión.

`llmw init` también escribe siempre `.claude/rules/llm-wiki.md`, sin
importar `--no-claude-plugin`. Un manifiesto de plugin de Claude Code
puede distribuir hooks y skills, pero no tiene forma de distribuir
contenido de `.claude/rules/`, así que este es el único camino que mete
automáticamente la guía de "buscar antes / actualizar después" en cada
sesión, sin ninguna copia del marketplace con la que duplicarse.

`llmw init` también escribe lo mismo en `.codex/rules/llm-wiki.md` cada
vez, sin importar cuál plugin (o ninguno) estés usando realmente — un
manifiesto de plugin de Codex tiene la misma brecha "hooks y skills sí,
rules no" que el de Claude Code. Se escribe sin condiciones, no detrás de
un flag específico de Codex: un archivo de rules que nadie usa porque en
tu proyecto no usás esa plataforma no molesta a nadie, pero un equipo que
usa Claude Code y Codex a la vez se encuentra con ambos listos para usar
sin ninguna configuración extra.

## Lo que esta herramienta todavía no hace, a propósito

Por diseño, esto se queda fuera del alcance por ahora: conectarse
directamente a modelos de IA, vigilar archivos para detectar cambios de
forma automática, búsqueda semántica con IA, leer archivos PDF o Word
directamente, tener una aplicación gráfica, o cualquier fusión, borrado o
resolución de conflictos automática entre notas.
