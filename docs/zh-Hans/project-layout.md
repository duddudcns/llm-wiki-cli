# 项目布局、采用现有 wiki 和 Obsidian 兼容性

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · [日本語](../ja/project-layout.md) · **简体中文** · [Español](../es/project-layout.md) · [Français](../fr/project-layout.md)

## 项目布局：经典 vs. `ai-wiki/`

默认（`--layout classic`）`raw/`、`wiki/` 和 `.llmw/` 直接放在项目根目录。传递 `--layout ai-wiki` 以改为将它们嵌套下一级，保持根目录整洁：

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # 与经典布局相同的内容，嵌套
.claude/skills/llm-wiki/       # 仍然在真实项目根目录中搭建
.claude-plugin/plugin.json     # 仍然在真实项目根目录中搭建
```

每个命令自动检测项目使用的布局 —— 它首先检查项目根目录中的 `.llmw/`，然后回退到 `ai-wiki/.llmw`。现有的经典布局项目不需要迁移。

如果项目无法从当前目录自动检测（例如从其他地方运行的脚本，或非标准检出），用 `--root <path>` 或 `LLMW_ROOT` 环境变量显式指向 `llmw` —— 两者都对两种布局进行检查，所以单个值就够了（不需要单独指定 `raw/`/`wiki/`/`.llmw/`）：

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## 采用现有 wiki

如果 `raw/`/`wiki/`（或等效的 `ai-wiki/` 嵌套）已经有真实内容在自己的约定下 —— 例如一个前置 `llmw` 的手工 Karpathy 模式 wiki —— 用 `--adopt` 代替纯 `init`：

```bash
llmw init --adopt                  # 或：llmw init --layout ai-wiki --adopt
```

`--adopt` 在首次运行时创建 `.llmw/` 和 `config.toml`，但永远不写默认内容文件（`raw/README.md`、`wiki/index.md`、`wiki/overview.md`、`wiki/log.md`）或默认分类子文件夹（`entities/`、`concepts/`、`decisions/`、`syntheses/`、`projects/`、`glossary/`、`archived/`、`sources/`）—— **即使用 `--force`** —— 所以这些路径的前期内容永不被接触或覆盖。一旦 `config.toml` 存在，`--force` 也永不将其重写回默认值，所以已采用架构的手工调整覆盖（见下方）存活重新 `init --adopt --force`。纯 `llmw init`（无 `--adopt`）总是搭建那些默认值、在 `--force` 上覆盖它们，也在 `--force` 上重置 `config.toml` 到默认值；仅对空（或已由 llmw 管理）目录使用它。现有架构怪癖（例如一个 `last_updated` 字段代替 `created`/`updated`，或在 `wiki/` 外的根级 `index.md`/`log.md` 文件）通过 `.llmw/config.toml` 的 `lint.required_frontmatter` 和 `paths.extra_root_pages` 处理 —— 见下方。

## 将 llmw 适应到现有 wiki

如果 wiki 已有自己的约定（不同的前置元数据字段、顶级文件在 `wiki/` 外），指向 `llmw init --adopt` 到其根（见上方）并调整 `.llmw/config.toml` 而不是重新组织 wiki 的文件：

```toml
[paths]
# 额外的个别 Markdown 文件（相对于项目根目录）与 wiki/**/*.md 一起索引
# —— 例如一个保持在 wiki/ 外的架构/索引/日志文件。
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# 覆盖 `llmw lint` 需要的前置元数据键。默认是
# ["type", "status", "created", "updated"]；"updated" 也接受
# `last_updated` 键。
required_frontmatter = ["type", "status", "last_updated"]
```

无现有页面需要改变 —— `llmw rebuild` 下次运行时拾起新配置。

## Obsidian 兼容性

`wiki/` 是纯 Markdown，有 YAML 前置元数据和 `[[wikilinks]]` —— 直接作为 Obsidian vault 打开以在 GUI 中获得图表视图、反向链接和搜索，不放弃 CLI 驱动的智能体工作流的任何部分。

链接解析专门处理现实世界的 Obsidian 导出怪癖：

- `[[Page]]`、`[[Page|Alias]]`、`[[Page#Heading|Alias]]`、`[[#Heading]]`、`![[Embed]]` —— 完整 wikilink 语法。
- 类路径 wikilink 目标（`[[concepts/foo]]`）解析相对于 **vault 根**（`wiki/`），匹配 Obsidian 在你实际打开 `wiki/` 作为 vault 时如何解析它们 —— 不仅是相对于链接页面自己的文件夹。
- `related:` 前置元数据是一阶链接来源，与内联 wikilinks 相同 —— 既是纯路径/标题（`related: [wiki/concepts/foo]`，一些 wiki 在采用 `llmw` 之前使用的约定）也是 Obsidian 自身的属性面板格式（`related: ["[[Note]]"]`）都正确解析。
- 带 URL 编码目标的 Markdown 链接（`[Profile](Project%20Profile.md)`，当文件名有空格时很常见）在与磁盘上的页面匹配前解码。
- 指向 `wiki/` 外的相对 wikilinks（例如 `[[../notes/x]]`）检查真实文件系统 —— 它们仅被 `llmw lint` 报告为损坏，如果目标在项目的任何地方真的不存在，不是仅因为它们不是一个索引的 wiki 页面。

**图表故意与 Obsidian 的自身分歧的地方**：`related:` 边和 llmw 的标题基础 wikilink 解析（`[[Exact Page Title]]` 即使不匹配文件名也解析）都是 llmw 扩展，无 Obsidian 等效物 —— Obsidian 自身的图表视图不会显示那些边。两个在不同文件夹中有相同文件名主干的页面在两个工具中也会模糊解析（第一个匹配赢）。在 Obsidian 中打开 `wiki/` 在相同文件上得到一个真实、有用的图表，而不是像素相同的。
