# Organizing your wiki, and using an existing one

**English** · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · [Français](../fr/project-layout.md)

## Two ways to organize the folders

By default, `llmw init` puts the `raw/`, `wiki/`, and behind-the-scenes
folders right in your project's main folder. If you'd rather keep your
project folder tidy, you can tuck everything into a subfolder called
`ai-wiki/` instead:

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # same folders as before, just nested one level down
.claude/skills/llm-wiki/       # this still goes in your main project folder either way
.claude/rules/llm-wiki.md      # this still goes in your main project folder either way
.codex/rules/llm-wiki.md       # this still goes in your main project folder either way
.claude-plugin/plugin.json     # this still goes in your main project folder either way
```

Every command automatically figures out which style you're using — you
never have to tell it again after the first `init`. If you already have
notes set up the plain way, you don't need to change anything.

If you're running `llmw` from somewhere outside the project folder (say,
from a script), you can just tell it where to look, and it'll figure out
which of the two folder styles you're using on its own:

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## Using `llmw` with a wiki you already made by hand

Maybe you already have your own set of notes, made before you ever heard
of this tool, and you just want `llmw` to start managing it. Use
`--adopt` instead of a plain `init`:

```bash
llmw init --adopt                  # or: llmw init --layout ai-wiki --adopt
```

This sets up the behind-the-scenes search index, but it will **never**
create or overwrite any of your existing notes or folders — even if you
later re-run the command with `--force`. Your settings file is protected
the same way, so any custom settings you've made will never get reset by
accident. (A plain `llmw init`, without `--adopt`, behaves differently:
it does create some starter notes and folders, and `--force` will
overwrite them — so only use the plain version on a brand-new, empty
project.)

## Fitting `llmw` to notes that use different rules

If your existing notes are organized a little differently — for example,
some important files live outside the `wiki/` folder, or they use
different labels than `llmw` expects — you don't need to reorganize
anything. Just adjust a small settings file instead, after adopting the
wiki as shown above:

```toml
[paths]
# Extra individual note files (outside the normal wiki/ folder) that
# should still be included when searching — for example, an index or
# changelog file kept at the top level.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# Which pieces of information every note is expected to have at the top.
# The built-in default is ["type", "status", "created", "updated"];
# "updated" also accepts a note that instead uses "last_updated".
required_frontmatter = ["type", "status", "last_updated"]
```

None of your existing notes need to change for this to work.

## Using it together with Obsidian

Every note is a plain text file, so you can also open the `wiki/` folder
directly in the popular note-taking app [Obsidian](https://obsidian.md/)
— you'll get its visual map view, its "what links here" view, and its
search, all on the very same notes, without giving up anything about how
the AI uses them.

Some details about how notes link to each other are designed to match
what Obsidian itself does, including some tricky edge cases:

- All of Obsidian's linking styles are understood: a plain link to
  another note, a link with a custom display name, a link to a specific
  heading inside a note, and an "embed" that pulls in another note's
  content.
- A link that includes a folder path is understood the same way Obsidian
  understands it — relative to the top of the wiki, not relative to
  whichever note the link is written in.
- Notes can also list "related notes" at the top in a couple of different
  formats, and both are understood correctly.
- Links to files with spaces or special characters in their names (common
  when notes are exported from other tools) are still matched up
  correctly.
- A link pointing outside the `wiki/` folder is checked against what
  actually exists on disk, so it's only flagged as broken if it truly
  doesn't exist anywhere.

**A couple of small differences from real Obsidian:** this tool
understands a couple of extra kinds of connections between notes (like
the "related notes" list mentioned above) that Obsidian's own map view
won't show, since they're specific to this tool. And if two notes
happen to have the exact same filename in different folders, both this
tool and Obsidian will sometimes pick the wrong one when a link doesn't
specify which folder it means. Everything else lines up.
