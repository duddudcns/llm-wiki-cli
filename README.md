# llmw

**English** · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · [Français](README.fr.md)

A simple command-line tool that gives an AI coding assistant its own personal notebook (a "wiki") for a project — so it can remember decisions, facts, and history instead of forgetting everything between conversations.

## Why use this?

Many AI tools work by stuffing a big block of instructions and data into every single message, which wastes space and slows things down. `llmw` works differently: it's a small, simple tool the AI only reaches for when it actually needs to look something up or write something down. The tool itself never "thinks" or generates text — it just stores notes, finds them again later, and double-checks they're written correctly. All the actual thinking (what to write, how to summarize) is done by the AI, not by `llmw`.

## The basic idea

- **Two folders, two jobs** — `raw/` holds original source material that never changes (like a document you uploaded). `wiki/` is where the AI writes its own notes, and keeps updating them as it learns more — so the notebook keeps getting more useful over time instead of just being a one-time search.
- **Notes that link to each other** — pages can link to other pages (like Wikipedia links), so the AI can follow a trail of related notes. This also works with the popular note-taking app [Obsidian](https://obsidian.md/), if you want a visual way to browse the same notes yourself.
- **Everything is just plain text files** — every note is a normal Markdown file you can open and read yourself, no special database required. There's also a small search-index file, but that's just a helper that can always be regenerated from the notes if needed.
- **The AI writes; the tool just checks and organizes** — searching, finding related notes, and checking notes are written correctly are all simple, predictable operations with no AI involved. Deciding what's worth writing down, and writing it well, is the AI's job.
- **It captures preferences as it goes** — mention a coding convention or correction in passing during ordinary work, and the AI records it (in the wiki, or its own rules file) without being told to "remember this" or "update the wiki." You shouldn't have to keep saying that for a tool to be worth using.

## Install

**Claude Code plugin:**

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

This also sets up some helpful safety nets that keep everything working correctly on their own — see [docs/en/hooks.md](docs/en/hooks.md) for details.

**Codex plugin (CLI installation is not required):**

```powershell
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

The Codex plugin supplies intent-discoverable skills, five native MCP tools (`llmw_init`, `llmw_status`, `llmw_search`, `llmw_read`, `llmw_write`), and its own PreToolUse/Stop hooks that nudge searching before edits and updating the wiki after them — separate from Claude Code's hooks, not run by them. The MCP server starts through `uvx`, so [uv](https://docs.astral.sh/uv/) must be available; the hooks self-install a pinned `llmw` CLI in the background the same way Claude Code's do, so nothing here needs a manual install either.

Want to install the command-line tool directly instead (for example, to use it outside of Claude Code)? See [docs/en/installation.md](docs/en/installation.md) for step-by-step instructions for Windows, macOS, and Linux. You can install both — they don't get in each other's way.

## Quickstart

```bash
mkdir my-project && cd my-project
llmw init
llmw rebuild
llmw status --brief
```

`llmw init` creates this folder structure for you:

```text
raw/                          # original source material — never edited
wiki/                         # the AI's own notes, which it keeps updating
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # behind-the-scenes search index (built by `llmw rebuild`, can be rebuilt anytime)
.claude/skills/llm-wiki/      # teaches Claude Code how to use this tool
.claude/rules/llm-wiki.md     # nudges Claude Code to search before/update after work, automatically
.codex/rules/llm-wiki.md      # same nudge, for Codex — written every init regardless of which plugin you use
.claude-plugin/plugin.json    # optional plugin info for this project
```

Want to keep your project folder tidier by tucking all of this into a subfolder instead? Or point `llmw` at a wiki you already made by hand? See [docs/en/project-layout.md](docs/en/project-layout.md).

## A typical AI workflow

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## All commands

Every command supports `--json` if you want the output in a format a program can read. Most "read" commands show a short summary by default (add `--full`/`--no-brief` to see everything).

| Command | What it does |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | Sets up `raw/`, `wiki/`, and the search index for a new project (or an existing one, with `--adopt` — see [docs/en/project-layout.md](docs/en/project-layout.md)) |
| `llmw status [--brief\|--json]` | Quick health check: how many notes exist, any broken links, when it was last updated |
| `llmw rebuild` | Rebuilds the entire search index from scratch |
| `llmw index [--changed\|--all]` | Updates the search index (just what changed, by default) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | Searches all notes — see [docs/en/commands.md](docs/en/commands.md) for how the search works |
| `llmw read <path\|title\|alias> [--full\|--brief]` | Opens a note; the short version shows the title, summary, and links |
| `llmw links <target>` | Shows what a note links out to |
| `llmw backlinks <target>` | Shows what other notes link to this one |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | Suggests related notes, using simple rules (no AI guessing involved) |
| `llmw ingest <raw/...>` | Turns a source document into a draft note ready for the AI to fill in |
| `llmw write <path> --reason "..." --stdin [--force]` | Creates a brand-new note |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | Replaces one exact piece of text in an existing note |
| `llmw patch <path> --reason "..." --stdin` | Applies a set of changes to a note (keeps a backup first, undoes itself if something goes wrong) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | Moves an old note out of the way instead of deleting it, and leaves a note behind pointing to its new location |
| `llmw lint [--brief\|--json]` | Checks for problems — broken links, missing information, duplicate titles — but never fixes them automatically |
| `llmw health [--brief]` | Checks that everything behind the scenes is set up correctly |
| `llmw graph build` / `llmw graph export --format json\|html` | Builds or exports a visual map of how notes link to each other |

## Built-in safety rules

- The original source material in `raw/` can never be changed — the tool simply refuses.
- Every change to a note has to come with a short reason, which gets written down in a permanent history log.
- There's no "delete" — only "archive", which moves a note aside and leaves a signpost behind so nothing just vanishes.
- Applying a set of changes always makes a backup first, and undoes itself automatically if anything goes wrong partway through.
- A simple lock file stops two copies of the tool from editing the same notes at once and clobbering each other.

## More documentation

| Doc | What's in it |
|---|---|
| [docs/en/installation.md](docs/en/installation.md) | Full install instructions for Windows, macOS, and Linux; how to update or remove it |
| [docs/en/hooks.md](docs/en/hooks.md) | How the Claude Code plugin keeps the AI from bypassing the wiki, and keeps itself up to date automatically |
| [docs/en/commands.md](docs/en/commands.md) | How search actually works under the hood |
| [docs/en/project-layout.md](docs/en/project-layout.md) | Different ways to organize the wiki folders, adopting a wiki you already made, using it alongside the note-taking app Obsidian |
| [docs/en/development.md](docs/en/development.md) | Setting up a dev environment to work on `llmw` itself |

## License

MIT — see [LICENSE](LICENSE).
