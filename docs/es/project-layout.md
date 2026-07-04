# Diseño del proyecto, adoptar un wiki existente, y compatibilidad con Obsidian

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · **Español** · [Français](../fr/project-layout.md)

## Diseño del proyecto: clásico vs. `ai-wiki/`

Por defecto (`--layout classic`) `raw/`, `wiki/`, y `.llmw/` se sientan directamente
en la raíz del proyecto. Pasa `--layout ai-wiki` para anidarlos un nivel abajo
en su lugar, manteniendo la raíz sin clutter:

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # mismo contenido que el diseño clásico, anidado
.claude/skills/llm-wiki/       # aún genera en la raíz de proyecto real
.claude-plugin/plugin.json     # aún genera en la raíz de proyecto real
```

Cada comando auto-detecta qué diseño usa un proyecto — verifica `.llmw/` directamente
en la raíz del proyecto primero, luego vuelve a `ai-wiki/.llmw`. Los proyectos de diseño clásico existentes
no necesitan migración.

Si un proyecto no puede ser auto-detectado desde el directorio actual (p. ej., un
script ejecutándose desde otro lugar, o un checkout no estándar), apunta `llmw`
a él explícitamente con `--root <path>` o la variable de entorno `LLMW_ROOT` — cualquiera
es verificada para ambos diseños, así que un valor único es suficiente (no hay necesidad
de especificar `raw/`/`wiki/`/`.llmw/` individualmente):

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Adoptar un wiki existente

Si `raw/`/`wiki/` (o un equivalente anidado en `ai-wiki/`) ya tiene contenido real
bajo sus propias convenciones — p. ej., un wiki de patrón Karpathy hecho a mano que predateca `llmw` —
usa `--adopt` en lugar de un simple `init`:

```bash
llmw init --adopt                  # o: llmw init --layout ai-wiki --adopt
```

`--adopt` crea `.llmw/` y `config.toml` en la primera ejecución, pero nunca escribe
los archivos de contenido predeterminados (`raw/README.md`, `wiki/index.md`,
`wiki/overview.md`, `wiki/log.md`) o los subcarpetas de taxonomía predeterminadas
(`entities/`, `concepts/`, `decisions/`, `syntheses/`, `projects/`,
`glossary/`, `archived/`, `sources/`) — **ni siquiera con `--force`** — así que
contenido pre-existente en esas rutas nunca se toca ni sobrescribe. Una vez
que `config.toml` existe, `--force` nunca lo reescribe de vuelta a predeterminados tampoco,
así que anulaciones afinadas a mano para el esquema adoptado (ver abajo) sobreviven a
re-`init --adopt --force`. Un simple `llmw init` (sin `--adopt`) siempre
genera esos predeterminados, los sobrescribe en `--force`, y reinicia
`config.toml` a predeterminados en `--force` también; solo usalo contra un directorio vacío
(o ya gestionado por llmw). Las peculiaridades de esquema existentes (p. ej., un
campo `last_updated` en lugar de `created`/`updated`, o archivos de nivel raíz
`index.md`/`log.md` fuera de `wiki/`) se manejan vía
`.llmw/config.toml`'s `lint.required_frontmatter` y
`paths.extra_root_pages` — ver abajo.

## Adaptar llmw a un wiki existente

Si un wiki ya tiene sus propias convenciones (campos frontmatter diferentes,
archivos de nivel superior viviendo fuera de `wiki/`), apunta `llmw init --adopt` a su
raíz (ver arriba) y ajusta `.llmw/config.toml` en lugar de reorganizar
los archivos del wiki:

```toml
[paths]
# Archivos Markdown individuales adicionales (relativos a la raíz del proyecto) a indexar
# junto con wiki/**/*.md — p. ej., un archivo de esquema/índice/registro mantenido fuera de wiki/.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Anula qué claves de frontmatter requiere `llmw lint`. El predeterminado es
# ["type", "status", "created", "updated"]; "updated" también acepta una
# clave `last_updated`.
required_frontmatter = ["type", "status", "last_updated"]
```

Ninguna página existente necesita cambiar — `llmw rebuild` recoge la nueva config
en la próxima ejecución.

## Compatibilidad con Obsidian

`wiki/` es Markdown simple con YAML frontmatter y `[[wikilinks]]` — ábrelo directamente
como un almacén Obsidian para obtener vista de gráfico, enlaces hacia atrás, y búsqueda
en una GUI, sin renunciar a ninguno del flujo de trabajo impulsado por CLI del agente.

La resolución de enlaces específicamente maneja peculiaridades de exportación de Obsidian del mundo real:

- `[[Página]]`, `[[Página|Alias]]`, `[[Página#Encabezado|Alias]]`, `[[#Encabezado]]`,
  `![[Insertar]]` — gramática completa de wikilink.
- Objetivos wikilink similares a rutas (`[[concepts/foo]]`) se resuelven relativos a la
  **raíz del almacén** (`wiki/`), coincidiendo con cómo Obsidian las resuelve cuando
  realmente abres `wiki/` como un almacén — no solo relativo a la carpeta de la página
  de enlace propia.
- Frontmatter `related:` es una fuente de enlace de primera clase, igual que wikilinks en línea —
  tanto una ruta/título plano (`related: [wiki/concepts/foo]`, la
  convención que algunos wikis usaban antes de adoptar `llmw`) y el formato de panel Properties
  propio de Obsidian (`related: ["[[Nota]]"]`) se resuelven correctamente.
- Enlaces Markdown con objetivos codificados por URL (`[Perfil](Project%20Profile.md)`,
  común cuando un nombre de archivo tiene espacios) se decodifican antes de coincidir contra
  páginas en disco.
- Wikilinks relativos que apuntan fuera de `wiki/` (p. ej. `[[../notes/x]]`) se
  verifican contra el sistema de archivos real — solo se reportan como rotos por
  `llmw lint` si el objetivo genuinamente no existe en ningún lugar del
  proyecto, no meramente porque no sean una página wiki indexada.

**Donde el gráfico deliberadamente diverge del propio Obsidian's**: aristas `related:`
y resolución de wikilink basada en título de llmw (`[[Exact Page Title]]`
resolviendo incluso cuando no coincide con el nombre de archivo) son ambas extensiones llmw
sin equivalente Obsidian — la vista de gráfico propia de Obsidian no
mostrará esas aristas. Dos páginas con el mismo tallo de nombre de archivo en diferentes
carpetas también se resuelven ambiguamente (primer coincidencia gana) en ambas herramientas. Abrir
`wiki/` en Obsidian te obtiene un gráfico real y útil en los mismos archivos, no uno
idéntico en píxeles.
