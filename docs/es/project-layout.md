# Cómo organizar tu wiki, y cómo usar una que ya tienes

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · **Español** · [Français](../fr/project-layout.md)

## Dos formas de organizar las carpetas

Por defecto, `llmw init` pone las carpetas `raw/`, `wiki/` y las de uso
interno directamente en la carpeta principal de tu proyecto. Si prefieres
mantener ordenada la carpeta de tu proyecto, puedes meter todo dentro de
una subcarpeta llamada `ai-wiki/` en su lugar:

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # las mismas carpetas de antes, solo que un nivel más adentro
.claude/skills/llm-wiki/       # esto igual va en la carpeta principal de tu proyecto
.claude/rules/llm-wiki.md      # esto también va igual en la carpeta principal de tu proyecto
.claude-plugin/plugin.json     # esto igual va en la carpeta principal de tu proyecto
```

Cada comando descubre automáticamente cuál de los dos estilos estás
usando — nunca tienes que decírselo de nuevo después del primer `init`.
Si ya tienes tus notas organizadas de la forma sencilla, no necesitas
cambiar nada.

Si estás corriendo `llmw` desde afuera de la carpeta del proyecto
(digamos, desde un script), simplemente puedes decirle dónde buscar, y él
mismo va a averiguar cuál de los dos estilos de carpetas estás usando:

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Usar `llmw` con una wiki que ya armaste a mano

Tal vez ya tengas tu propio conjunto de notas, hechas antes de conocer
esta herramienta, y solo quieras que `llmw` empiece a manejarlas. Usa
`--adopt` en vez de un `init` normal:

```bash
llmw init --adopt                  # o: llmw init --layout ai-wiki --adopt
```

Esto prepara el índice de búsqueda interno, pero **nunca** va a crear ni
sobrescribir ninguna de tus notas o carpetas existentes — ni siquiera si
más adelante vuelves a correr el comando con `--force`. Tu archivo de
configuración está protegido de la misma manera, así que ninguna
configuración personalizada que hayas hecho se va a reiniciar por
accidente. (Un `llmw init` normal, sin `--adopt`, se comporta distinto:
sí crea algunas notas y carpetas de partida, y `--force` sí las
sobrescribe — así que usa la versión normal solo en un proyecto nuevo y
vacío.)

## Ajustar `llmw` a notas que usan reglas distintas

Si tus notas ya están organizadas de manera un poco diferente — por
ejemplo, algunos archivos importantes están fuera de la carpeta `wiki/`,
o usan etiquetas distintas a las que `llmw` espera — no hace falta
reorganizar nada. Solo ajusta un pequeño archivo de configuración,
después de adoptar la wiki como se explicó arriba:

```toml
[paths]
# Archivos de nota individuales adicionales (fuera de la carpeta wiki/
# normal) que igual deberían incluirse al buscar — por ejemplo, un
# archivo de índice o de historial de cambios que se mantiene en el
# nivel superior.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Qué datos se espera que tenga cada nota al principio.
# Por defecto son ["type", "status", "created", "updated"];
# "updated" también acepta una nota que en vez de eso use "last_updated".
required_frontmatter = ["type", "status", "last_updated"]
```

Ninguna de tus notas existentes necesita cambiar para que esto funcione.

## Usarla junto con Obsidian

Cada nota es un archivo de texto normal, así que también puedes abrir la
carpeta `wiki/` directamente en la popular app de notas
[Obsidian](https://obsidian.md/) — vas a tener su vista de mapa visual, su
vista de "qué enlaza aquí", y su buscador, todo sobre las mismas notas,
sin perder nada de cómo las usa la IA.

Algunos detalles de cómo se enlazan las notas entre sí están pensados
para calzar con lo que hace el propio Obsidian, incluyendo algunos casos
particulares:

- Se entienden todos los estilos de enlace de Obsidian: un enlace simple
  a otra nota, un enlace con un nombre de visualización personalizado, un
  enlace a un encabezado específico dentro de una nota, y un "embed" que
  trae el contenido de otra nota.
- Un enlace que incluye una ruta de carpeta se entiende igual que lo
  entiende Obsidian — relativo a la raíz de la wiki, no relativo a la
  nota donde está escrito el enlace.
- Las notas también pueden listar "notas relacionadas" arriba del todo,
  en un par de formatos distintos, y ambos se entienden correctamente.
- Los enlaces a archivos con espacios o caracteres especiales en el
  nombre (algo común cuando las notas se exportan desde otras
  herramientas) igual se emparejan correctamente.
- Un enlace que apunta fuera de la carpeta `wiki/` se comprueba contra lo
  que realmente existe en el disco, así que solo se marca como roto si de
  verdad no existe en ningún lado.

**Un par de pequeñas diferencias con el Obsidian real:** esta herramienta
entiende un par de tipos extra de conexiones entre notas (como la lista
de "notas relacionadas" mencionada arriba) que la vista de mapa propia de
Obsidian no va a mostrar, porque son específicas de esta herramienta. Y si
dos notas tienen exactamente el mismo nombre de archivo en carpetas
distintas, tanto esta herramienta como Obsidian a veces van a elegir la
que no es cuando un enlace no especifica de qué carpeta se trata. Todo lo
demás calza igual.
