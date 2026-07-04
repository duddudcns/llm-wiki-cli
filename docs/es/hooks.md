# Hooks: mantener agentes honestos y la CLI en sincronización

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · **Español** · [Français](../fr/hooks.md)

El plugin de Claude Code (ver [installation.md](installation.md)) instala dos
hooks. Ninguno es requerido para usar `llmw` — son conveniencias capas
encima de una CLI que ya refuerza sus propias reglas de seguridad sin importar
si un hook se ejecutó.

## PreToolUse: el guardián wiki

Nada detiene a un agente de ignorar la habilidad de Claude Code y editar
`wiki/*.md` o `raw/**` directamente con sus propias herramientas de edición de archivos en lugar de
`llmw` — esto omite el registro de auditoría `--reason`, validación de frontmatter, y
copia de seguridad automática, y sucede en la práctica siempre que un *diferente*,
conjunto competidor de instrucciones está en efecto y nunca menciona `llmw`.

Cuando se instala como un plugin de Claude Code (no una habilidad de proyecto bare `llmw init`),
un hook `PreToolUse` cierra esa brecha al nivel del arnés: una llamada nativa
`Edit`/`Write`/`NotebookEdit` dirigida a `wiki/*.md` o `raw/**` se
niega (o, por config, se convierte en un aviso de confirmación), y el mensaje de negación nombra el comando exacto `llmw` a ejecutar en su lugar — así la próxima
acción del agente es una reescritura de una línea, no un callejón sin salida.

El guardián solo mira llamadas `Edit`/`Write`/`NotebookEdit` cuyo
objetivo se resuelve (caminando hacia arriba desde el archivo, de la misma manera que `llmw` encuentra su
propia raíz de proyecto) a un proyecto llmw real's `wiki/*.md` o `raw/**` —
todo lo demás, incluyendo plain `Read`, pasa sin tocar, y nunca
inspecciona comandos `Bash` (la policía de cadenas shell es su propio
campo minado de falsos positivos, así que el registro de auditoría en `wiki/log.md` más `llmw
lint` permanecen como la capa de detección para esa brecha en lugar de un hook tratando de
bloquearla).

Configura o desactiva por proyecto en `.llmw/config.toml`:

```toml
[hooks]
wiki_guard = "deny"  # default: block, with a message naming the llmw fix
# wiki_guard = "ask"   # prompt for confirmation instead of blocking
# wiki_guard = "off"   # disable the guard for this project
```

Ambos hooks requieren Git Bash en Windows (Claude Code vuelve a
PowerShell cuando Git Bash no está instalado, que estos hooks de forma shell
no soportan) — en todos lados, la puerta de seguridad propia de `llmw` (razón
requerida, ruta confinada, frontmatter validado, copia de seguridad antes de escribir) se mantiene sin importar si el hook se ejecutó.

También deja una nota corta `SessionStart` en contexto cada sesión: "este
proyecto tiene un wiki llmw" (con conteo de páginas) cuando `.llmw` ya existe, o
un aviso de una línea "ejecuta `llmw init`" cuando aún no lo hace — así un entorno en blanco
sin proyecto `CLAUDE.md`, y sin wiki inicializado en absoluto,
aún descubre `llmw` en turno uno.

## SessionStart: instalación CLI auto-sanadora

`plugin/bin/llmw` es un despachador delgado, no una distribución Python empaquetada — se
canaliza hacia un real `llmw` en PATH. Actualizar el plugin desde el
marketplace solo actualiza los archivos del plugin mismo (habilidad, hooks); **no**
toca ese binario autónomo. Dejado solo, eso significa instalar una
actualización de plugin puede silenciosamente dejarte ejecutando una CLI vieja debajo de él.

Un hook `SessionStart` (`plugin/hooks/session-start.sh`, cableado vía
`plugin/hooks/hooks.json`) cierra esa brecha: cada sesión, compara el
`llmw --version` instalado contra la versión que este paquete de plugin declara
(`plugin/.claude-plugin/plugin.json`). En un desajuste — incluyendo "no
instalado en absoluto" — (re)instala vía `uv tool install --force` (volviendo
a `pip install --user --force-reinstall`), fijado a la etiqueta `git` coincidente (`git+...@v<version>`), así que una
actualización de mercado de plugins también trae el binario de CLI autónomo en sincronización sin un `uv tool upgrade llmw`
manual separado.

Cuando las versiones ya coinciden, la verificación es solo una llamada local `llmw --version`
(sin red) cada sesión — la ruta de reinstalación solo se ejecuta en desajuste de versión genuino, aproximadamente una vez por lanzamiento.
