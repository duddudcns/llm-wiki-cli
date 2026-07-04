# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · **Español** · [Français](README.fr.md)

CLI de Wiki para Agentes IA estilo Obsidian sin interfaz gráfica.

## Por qué

Las herramientas MCP son convenientes, pero los esquemas de herramientas y las instrucciones largas consumen contexto en cada turno. `llmw` adopta un enfoque diferente: una CLI pequeña y determinista más una habilidad de Claude Code. El agente llama al wiki solo cuando lo necesita, y la CLI nunca llama un modelo — solo indexa, busca y valida.

## Conceptos

- **Wiki de Karpathy para LLM** — `raw/` contiene material fuente inmutable; `wiki/`
  es una capa de conocimiento persistente que un agente IA escribe y mantiene;
  esto no es RAG ordinario, el wiki es un artefacto compuesto.
- **Wikilinks estilo Obsidian** — `[[Página]]`, `[[Página|Alias]]`,
  `[[Página#Encabezado]]`, `![[Insertar]]`, enlaces hacia atrás, etiquetas, YAML frontmatter.
  `wiki/` es un almacén válido de Obsidian; ábrelo allí si quieres un IDE visual humano
  en los mismos archivos.
- **Markdown como fuente de verdad** — `.llmw/index.sqlite` y
  `.llmw/graph.json` son datos derivados y reconstruibles. `llmw rebuild`
  regenera ambos desde `wiki/*.md` solamente.
- **El agente IA escribe el wiki; la CLI indexa y lo valida** — búsqueda
  (SQLite FTS5), enlaces hacia atrás, puntuación de páginas relacionadas, y lint son todos
  deterministas, basados en reglas, e independientes del modelo. Resumir fuentes, escribir
  páginas, y decidir qué archivar es trabajo del agente.

## Instalar

**Recomendado: Plugin de Claude Code** — sin paso separado `pip`/`uv`/`pipx`:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

Esto también instala hooks que mantienen la CLI misma en sincronización automáticamente y
evitan que los agentes la eludan — ver [docs/es/hooks.md](docs/es/hooks.md).

¿Prefieres la CLI autónoma directamente (scripting, CI, otro editor),
o gestionar actualizaciones tú mismo? Ver
[docs/es/installation.md](docs/es/installation.md) para la matriz completa de instalación uv/pipx/pip/dev,
dividida por Windows/macOS/Linux. Los dos no entran en conflicto — puedes
instalar ambos.

## Inicio rápido

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` genera:

```text
raw/                          # material fuente inmutable
wiki/                         # capa de conocimiento mantenida por agentes
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # índice/caché/copias de seguridad/bloqueos derivados (reconstruible)
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # metadatos de plugin opcionales para este proyecto
```

Pasa `--layout ai-wiki` para anidar `raw/`/`wiki/`/`.llmw/` bajo una carpeta `ai-wiki/`
en su lugar (auto-detectado por cada comando después), y `--adopt` para
apuntar `llmw` a un wiki que ya tiene contenido real bajo sus propias
convenciones sin andamios sobre él — ver
[docs/es/project-layout.md](docs/es/project-layout.md).

## Flujo de trabajo del agente

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## Referencia de comandos

Todos los comandos aceptan `--json` para salida interpretable por máquina; la mayoría de lecturas
muestran una vista breve y económica de contexto por defecto (`--full`/`--no-brief` para más).

| Comando | Propósito |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Genera `raw/`, `wiki/`, `.llmw/` (anidado bajo `ai-wiki/` con `--layout ai-wiki`), y (por defecto) la habilidad/plugin de Claude Code. `--adopt` omite el contenido por defecto/andamios de taxonomía y protege `config.toml` de `--force`, para preservar contenido de wiki existente y sus anulaciones de config |
| `llmw status [--brief\|--json]` | Conteos de páginas, enlaces rotos, huérfanos, última hora indexada, páginas sucias |
| `llmw rebuild` | Re-índice completo de `wiki/**/*.md` desde cero |
| `llmw index [--changed\|--all]` | Re-índice incremental (por defecto) o completo |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | Búsqueda SQLite FTS5 sobre título/resumen/cuerpo — ver [docs/es/commands.md](docs/es/commands.md) para semántica de búsqueda |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Buscar una página; breve muestra título/tipo/resumen/puntos clave/enlaces/conteo de enlaces hacia atrás |
| `llmw links <target>` | Enlaces salientes, con estado de rotura |
| `llmw backlinks <target>` | Enlaces entrantes |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Candidatos de página relacionada deterministas (sin llamadas a modelo) |
| `llmw ingest <raw/...>` | Registrar una fuente `.md`/`.txt` como borrador `wiki/sources/<slug>.md` |
| `llmw write <path> --reason "..." --stdin [--force]` | Crear una nueva página wiki desde stdin |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Reemplazo exacto de cadena en una página existente (misma semántica que una herramienta Edit nativa) |
| `llmw patch <path> --reason "..." --stdin` | Aplicar un diff unificado a una página existente (hace copia de seguridad primero, revierte en fallo) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Mover una página a `wiki/archived/YYYY/MM/`, marcar frontmatter de archivo, registrar cambio |
| `llmw lint [--brief\|--json]` | Enlaces rotos, huérfanos, títulos/aliases duplicados, frontmatter faltante/inválido, referencias raw colgantes, enlaces a páginas archivadas — solo reporta, nunca auto-corrige |
| `llmw health [--brief]` | Verificaciones del sistema: config, bd de índice, versión de esquema, directorios, bloqueos |
| `llmw graph build` / `llmw graph export --format json\|html` | Regenerar/exportar el gráfico de enlaces |

## Reglas de seguridad

- `raw/` es inmutable. `write`/`patch`/`archive` rechazan cualquier ruta bajo él.
- Cada `write`/`patch`/`archive` requiere `--reason`, registrado en
  `wiki/log.md` y la tabla `log_entries`.
- No hay `delete` — usa `archive`. El predeterminado mantiene un stub de lápida
  en la ruta original apuntando a la nueva ubicación.
- `patch` respalda el archivo antes de aplicar un diff unificado, y deja
  el original intacto si el diff no aplica limpiamente (desajuste de contexto).
- Un simple bloqueo consultivo (`.llmw/locks/write.lock`) protege contra dos
  procesos `llmw` mutando el wiki al mismo tiempo.

## Documentación

| Doc | Cubre |
|---|---|
| [docs/es/installation.md](docs/es/installation.md) | Matriz completa de instalación CLI autónoma (Windows/macOS/Linux), actualización, desinstalación |
| [docs/es/hooks.md](docs/es/hooks.md) | Hook `PreToolUse` guardián de wiki del plugin Claude Code y hook de sincronización de versión auto-sanador `SessionStart` |
| [docs/es/commands.md](docs/es/commands.md) | Semántica de búsqueda (fallback de 3 niveles, stemming de partículas coreanas) |
| [docs/es/project-layout.md](docs/es/project-layout.md) | Diseño clásico vs. `ai-wiki/`, `--root`/`LLMW_ROOT`, `--adopt`, adaptar `llmw` a las convenciones de wiki existentes, notas de compatibilidad con Obsidian |
| [docs/es/development.md](docs/es/development.md) | Configuración de dev, la habilidad de Claude Code, alcance MVP |

## Licencia

MIT — ver [LICENSE](LICENSE).
