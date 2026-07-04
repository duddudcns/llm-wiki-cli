# Redes de seguridad integradas en el plugin

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · **Español** · [Français](../fr/hooks.md)

Instalar el plugin de Claude Code (mira [installation.md](installation.md))
activa dos funciones de seguridad automáticas. Ninguna de las dos es
obligatoria para usar `llmw` — son solo comodidades extra sobre una
herramienta que ya se protege sola de todas formas.

## Función 1: evitar que la IA edite las notas de la forma incorrecta

Técnicamente, nada impide que un asistente de IA ignore esta herramienta y
edite una nota de la wiki directamente, igual que edita cualquier otro
archivo. Si eso pasa, pierdes la copia de seguridad automática, la nota
obligatoria de "por qué hice este cambio", y la comprobación de que la
nota sigue bien escrita — y en la práctica, esto sí pasa cada vez que hay
otra instrucción al mando que nunca menciona esta herramienta.

Cuando lo instalas como plugin de Claude Code, un chequeo de seguridad
detecta esto: si la IA intenta editar una nota de la wiki directamente con
sus herramientas normales de edición de archivos, ese cambio se bloquea
(o, si prefieres, primero pide confirmación), y se le indica exactamente
qué comando de `llmw` debería usar en su lugar — así puede intentarlo de
nuevo enseguida, de la forma correcta, en vez de quedarse trabada.

Este chequeo solo se fija en cambios dirigidos a notas de la wiki dentro
de un proyecto que usa esta herramienta — todo lo demás se deja
completamente en paz, incluyendo simplemente leer archivos.

Puedes desactivarlo o cambiar qué tan estricto es, por proyecto, en
`.llmw/config.toml`:

```toml
[hooks]
wiki_guard = "deny"  # opción por defecto: bloquea el cambio y explica la forma correcta de hacerlo
# wiki_guard = "ask"   # pide confirmación en vez de bloquear
# wiki_guard = "off"   # desactiva este chequeo para este proyecto
```

En Windows, este chequeo necesita tener "Git Bash" instalado para
funcionar. Si no lo tienes, el chequeo simplemente no se ejecuta — las
reglas de seguridad propias de `llmw` (una razón obligatoria para cada
cambio, copias de seguridad antes de editar, etc.) se siguen aplicando
igual.

También aparece un pequeño recordatorio al comienzo de cada sesión: "este
proyecto tiene una wiki con N notas" si ya existe una, o una pista de una
sola línea que dice "deberías correr `llmw init`" si todavía no existe —
así la IA se entera de esta herramienta desde el primer mensaje, incluso
en un proyecto completamente nuevo.

## Función 2: mantener actualizada la herramienta de línea de comandos

El plugin incluye un pequeño programa auxiliar, pero el trabajo de verdad
lo hace una copia aparte de `llmw` instalada en tu computadora. Actualizar
el plugin desde el marketplace **no** actualiza automáticamente esa copia
aparte — si no se hiciera nada más, podrías terminar usando una versión
vieja sin darte cuenta.

Para evitar eso, se hace un chequeo rápido al comienzo de cada sesión:
compara la versión de `llmw` instalada en tu computadora con la versión
que el plugin espera. Si no coinciden — incluso si `llmw` todavía no está
instalada — la reinstala automáticamente en la versión correcta. Así,
actualizar el plugin también mantiene sincronizada la herramienta de línea
de comandos, sin que tengas que hacer nada extra.

Cuando las versiones ya coinciden, este chequeo es solo una comprobación
rápida y local, sin necesitar conexión a internet — la reinstalación de
verdad solo ocurre en las raras ocasiones en que algo está desincronizado.
