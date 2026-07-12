# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · **Español** · [Français](README.fr.md)

Una herramienta sencilla de línea de comandos que le da a un asistente de IA para programar su propio cuaderno de notas (una "wiki") para un proyecto — así puede recordar decisiones, datos e historial en vez de olvidarlo todo entre conversaciones.

## ¿Por qué usar esto?

Muchas herramientas de IA funcionan metiendo un montón de instrucciones y datos en cada mensaje, lo que desperdicia espacio y hace todo más lento. `llmw` funciona distinto: es una herramienta pequeña y simple a la que la IA solo recurre cuando de verdad necesita buscar o anotar algo. La herramienta en sí nunca "piensa" ni genera texto — solo guarda notas, las vuelve a encontrar cuando hace falta y comprueba que estén bien escritas. Todo el trabajo de pensar (qué anotar, cómo resumirlo) lo hace la IA, no `llmw`.

## La idea básica

- **Dos carpetas, dos trabajos** — `raw/` guarda el material original, que nunca cambia (como un documento que subiste). `wiki/` es donde la IA escribe sus propias notas, y las va actualizando a medida que aprende más — así el cuaderno se vuelve cada vez más útil con el tiempo, en vez de ser solo una búsqueda de una sola vez.
- **Notas que se enlazan entre sí** — las páginas pueden enlazar a otras páginas (como los enlaces de Wikipedia), para que la IA pueda seguir un rastro de notas relacionadas. Esto también funciona con la popular app de notas [Obsidian](https://obsidian.md/), por si quieres una forma visual de explorar esas mismas notas tú mismo.
- **Todo son simples archivos de texto** — cada nota es un archivo Markdown normal que puedes abrir y leer tú mismo, sin que haga falta ninguna base de datos especial. También hay un pequeño archivo de índice de búsqueda, pero es solo un ayudante que siempre se puede volver a generar a partir de las notas si hace falta.
- **La IA escribe; la herramienta solo revisa y organiza** — buscar, encontrar notas relacionadas y comprobar que las notas estén bien escritas son operaciones simples y predecibles, sin ninguna IA de por medio. Decidir qué vale la pena anotar, y escribirlo bien, es trabajo de la IA.
- **Recoge preferencias sobre la marcha** — mencionás una convención de código o una corrección de pasada mientras trabajás, y la IA la registra (en la wiki, o en su propio archivo de reglas) sin que le digas "acordate de esto" o "actualizá la wiki". Si tenés que estar diciendo eso todo el tiempo, la herramienta no vale mucho la pena.

## Instalación

**Recomendado: instalar como plugin de Claude Code** — solo dos comandos, sin nada más que configurar:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

Esto también activa algunas redes de seguridad útiles que mantienen todo funcionando bien por su cuenta — mira [docs/es/hooks.md](docs/es/hooks.md) para los detalles.

¿Prefieres instalar la herramienta de línea de comandos directamente (por ejemplo, para usarla fuera de Claude Code)? Mira [docs/es/installation.md](docs/es/installation.md), donde hay instrucciones paso a paso para Windows, macOS y Linux. Puedes instalar ambas cosas — no se estorban entre sí.

## Para empezar rápido

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` crea esta estructura de carpetas por ti:

```text
raw/                          # material original — nunca se edita
wiki/                         # las notas propias de la IA, que ella va actualizando
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # índice de búsqueda interno (se puede reconstruir cuando quieras)
.claude/skills/llm-wiki/      # le enseña a Claude Code cómo usar esta herramienta
.claude/rules/llm-wiki.md     # empuja a Claude Code a buscar antes y actualizar después, automáticamente
.claude-plugin/plugin.json    # información opcional del plugin para este proyecto
```

¿Quieres mantener más ordenada la carpeta de tu proyecto metiendo todo esto en una subcarpeta, en vez de dejarlo suelto? ¿O apuntar `llmw` a una wiki que ya armaste a mano? Mira [docs/es/project-layout.md](docs/es/project-layout.md).

## Un flujo de trabajo típico con IA

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## Todos los comandos

Todos los comandos aceptan `--json` si quieres la salida en un formato que un programa pueda leer. La mayoría de los comandos de "lectura" muestran un resumen corto por defecto (agrega `--full`/`--no-brief` para ver todo).

| Comando | Qué hace |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Prepara `raw/`, `wiki/` y el índice de búsqueda para un proyecto nuevo (o uno ya existente, con `--adopt` — mira [docs/es/project-layout.md](docs/es/project-layout.md)) |
| `llmw status [--brief\|--json]` | Chequeo rápido de estado: cuántas notas hay, si hay enlaces rotos, cuándo se actualizó por última vez |
| `llmw rebuild` | Reconstruye desde cero todo el índice de búsqueda |
| `llmw index [--changed\|--all]` | Actualiza el índice de búsqueda (por defecto, solo lo que cambió) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | Busca en todas las notas — mira [docs/es/commands.md](docs/es/commands.md) para saber cómo funciona la búsqueda |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Abre una nota; la versión corta muestra el título, el resumen y los enlaces |
| `llmw links <target>` | Muestra a qué enlaza una nota |
| `llmw backlinks <target>` | Muestra qué otras notas enlazan a esta |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Sugiere notas relacionadas, usando reglas simples (sin que la IA tenga que adivinar) |
| `llmw ingest <raw/...>` | Convierte un documento fuente en un borrador de nota listo para que la IA lo complete |
| `llmw write <path> --reason "..." --stdin [--force]` | Crea una nota completamente nueva |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Reemplaza un fragmento exacto de texto en una nota que ya existe |
| `llmw patch <path> --reason "..." --stdin` | Aplica un conjunto de cambios a una nota (primero guarda una copia de seguridad, y se deshace sola si algo sale mal) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Mueve una nota vieja fuera del camino en lugar de borrarla, y deja una nota que señala su nueva ubicación |
| `llmw lint [--brief\|--json]` | Busca problemas — enlaces rotos, información que falta, títulos duplicados — pero nunca los corrige por su cuenta |
| `llmw health [--brief]` | Comprueba que todo lo que trabaja detrás de escena esté bien configurado |
| `llmw graph build` / `llmw graph export --format json\|html` | Crea o exporta un mapa visual de cómo se enlazan las notas entre sí |

## Reglas de seguridad incorporadas

- El material original en `raw/` no se puede cambiar nunca — la herramienta simplemente se niega a hacerlo.
- Todo cambio en una nota debe venir con una razón breve, que queda anotada en un registro histórico permanente.
- No existe "borrar" — solo "archivar", que mueve una nota a un lado y deja una señal de adónde fue, para que nada desaparezca sin dejar rastro.
- Aplicar un conjunto de cambios siempre hace primero una copia de seguridad, y se deshace automáticamente si algo falla a mitad de camino.
- Un simple archivo de bloqueo evita que dos copias de la herramienta editen las mismas notas al mismo tiempo y se pisen entre sí.

## Más documentación

| Doc | Qué encontrarás |
|---|---|
| [docs/es/installation.md](docs/es/installation.md) | Instrucciones completas de instalación para Windows, macOS y Linux; cómo actualizarla o quitarla |
| [docs/es/hooks.md](docs/es/hooks.md) | Cómo el plugin de Claude Code evita que la IA se salte la wiki, y cómo se mantiene actualizado por su cuenta |
| [docs/es/commands.md](docs/es/commands.md) | Cómo funciona realmente la búsqueda por dentro |
| [docs/es/project-layout.md](docs/es/project-layout.md) | Distintas formas de organizar las carpetas de la wiki, cómo adoptar una wiki que ya armaste, cómo usarla junto con la app de notas Obsidian |
| [docs/es/development.md](docs/es/development.md) | Cómo preparar un entorno de desarrollo para trabajar en `llmw` mismo |

## Licencia

MIT — mira [LICENSE](LICENSE).
