# Redes de seguridad integradas en el plugin

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · **Español** · [Français](../fr/hooks.md)

Instalar el plugin de Claude Code (mira [installation.md](installation.md))
activa cuatro funciones de seguridad automáticas. Ninguna de las cuatro es
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

Este chequeo solo se fija en cambios dirigidos a notas de la wiki (y a la
carpeta `raw/`, las notas del material original sin tocar a partir de las
cuales se construyen) dentro de un proyecto que usa esta herramienta —
todo lo demás se deja completamente en paz, incluyendo simplemente leer
archivos.

Puedes desactivarlo o cambiar qué tan estricto es, por proyecto, en
`.llmw/config.toml` — el mismo ajuste controla tanto las notas de la wiki
como la carpeta `raw/`:

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

## Función 2: recordarle a la IA que revise la wiki antes de cada solicitud

Una wiki llena de decisiones y errores pasados solo sirve si la IA de
verdad la consulta antes de empezar un trabajo nuevo — y si se la deja a
su propio criterio, no siempre se va a acordar de hacerlo. (Es el mismo
problema que tiene la gente con una wiki llevada a mano en una app de
notas: escribes las cosas con toda dedicación, y la IA de todos modos
repite un error que ya habías anotado, porque nada le recordó que debía
mirar.)

También se muestra un pequeño recordatorio al comienzo de cada sesión:
"este proyecto tiene una wiki con N notas" si ya existe una, o una pista
de una sola línea que dice "deberías correr `llmw init`" si todavía no
existe — así la IA se entera de esta herramienta desde el primer mensaje,
incluso en un proyecto completamente nuevo.

Para ayudar más con eso, a la mayoría de los mensajes que envías también
se les agrega un recordatorio breve: "este proyecto tiene una wiki —
búscala primero". Esto es deliberadamente simple, a propósito: no intenta
adivinar si tu mensaje tiene realmente algo que ver con la wiki
comparando palabras clave, porque ese tipo de adivinanza automática
fácilmente puede pasar por alto una nota que está redactada de forma
distinta a tu mensaje. En cambio, simplemente le pide a la IA que revise,
cada vez, y deja el criterio real (y la búsqueda real) en manos de la
propia IA. (Un mensaje muy corto, como "ok" o "gracias", no lleva el
recordatorio — ahí no hay ningún trabajo real que empiece como para
revisar la wiki.)

Por sí solo, ese recordatorio es solo un empujoncito — nunca bloquea ni
retrasa tu solicitud, y de ninguna manera puede impedir que la IA
continúe. En la práctica, ver la misma línea en cada turno también hace
que sea fácil ignorarlo con el tiempo.

Por eso hay una segunda capa, más fuerte, debajo de esta: la primera vez
en una sesión que la IA intenta editar un archivo real del proyecto (no
una nota de la wiki en sí) sin haber buscado todavía, esa edición se
pausa una vez y se le pide que busque primero o que decida
explícitamente que la tarea no lo necesita. Esto se dispara como máximo
una vez por sesión — en cuanto se ejecuta una búsqueda (aunque sea
puntual), o justo después de esta única comprobación, la edición vuelve
a la normalidad. Sigue sin ser un bloqueo total: la IA puede confirmar y
continuar sin llegar a buscar nunca. Lo que consigues con esto es un
momento de decisión forzado, en vez de un recordatorio fácil de pasar
por alto.

```toml
[hooks]
search_gate = "ask"  # opción por defecto: pausa la primera edición real de una sesión hasta que se busque o se confirme
# search_gate = "off"  # desactiva este chequeo para este proyecto
```

## Función 3: recordarle a la IA que actualice la wiki una vez terminado el trabajo

Una wiki solo sigue siendo útil si se mantiene al día con lo que
realmente pasó — y de la misma forma en que una IA puede olvidarse de
revisar la wiki antes de empezar, también puede terminar un trabajo real
y nunca dejar nada escrito, incluso con las mejores intenciones al
comenzar.

Para detectar esto, `llmw` lleva la cuenta, por sesión, de si los
archivos del proyecto cambiaron desde la última vez que se tocó la wiki
(mediante `llmw write`/`edit`/`patch`/`archive`). Si la IA intenta
terminar su turno con eso todavía pendiente, se la detiene una vez y se
le pide que registre qué cambió y por qué, o que decida explícitamente
que ese cambio en particular no amerita una actualización de la wiki.
Igual que el chequeo de búsqueda de arriba, esto se dispara como máximo
una vez por turno — la propia protección contra bucles de Claude Code
garantiza que nunca se pueda convertir en un reintento atascado — así
que vuelve a recordarlo al final del turno *siguiente* si la wiki
todavía no se puso al día, en vez de insistir en cada mensaje.

```toml
[hooks]
update_gate = "ask"  # opción por defecto: pausa una vez por turno cuando el código cambió pero la wiki no
# update_gate = "off"  # desactiva este chequeo para este proyecto
```

## Función 4: mantener actualizada la herramienta de línea de comandos

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
