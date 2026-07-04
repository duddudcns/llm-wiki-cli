# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · **简体中文** · [Español](README.es.md) · [Français](README.fr.md)

面向 AI 智能体的无头 Obsidian 式 LLM Wiki CLI。

## 为什么

MCP 工具虽然便利，但工具架构和冗长的说明会在每一轮消耗上下文。`llmw` 采用了不同的方式：一个小型的、确定性的 CLI 加上一个 Claude Code 技能。智能体只在需要时调用 wiki，CLI 本身永远不调用模型 —— 它仅用来索引、搜索和验证。

## 概念

- **Karpathy LLM Wiki** —— `raw/` 保存不可变的源材料；`wiki/` 是一个持久化知识层，由 AI 智能体编写和维护；这不是普通的 RAG，wiki 是一个不断增长的工件。
- **Obsidian 式 wikilinks** —— `[[Page]]`、`[[Page|Alias]]`、`[[Page#Heading]]`、`![[Embed]]`、反向链接、标签、YAML 前置元数据。`wiki/` 是一个有效的 Obsidian vault；如果需要人类可视化的 IDE，可以在那里打开它。
- **Markdown 作为单一事实来源** —— `.llmw/index.sqlite` 和 `.llmw/graph.json` 是派生的、可重建的数据。`llmw rebuild` 仅从 `wiki/*.md` 重新生成两者。
- **AI 智能体写 wiki；CLI 索引并验证它** —— 搜索（SQLite FTS5）、反向链接、相关页面评分和 lint 都是确定性的、基于规则的，无需模型。总结来源、编写页面和决定要归档什么是智能体的工作。

## 安装

**推荐：Claude Code 插件** —— 无需单独的 `pip`/`uv`/`pipx` 步骤：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

这也会安装钩子，让 CLI 本身保持同步，并防止智能体绕过它 —— 参见 [docs/zh-Hans/hooks.md](docs/zh-Hans/hooks.md)。

想直接使用独立的 CLI（用于脚本编写、CI 或其他编辑器），或者想自己管理升级？参见 [docs/zh-Hans/installation.md](docs/zh-Hans/installation.md) 了解完整的 uv/pipx/pip/dev 安装矩阵，按 Windows/macOS/Linux 划分。两者不冲突 —— 可以同时安装两个。

## 快速开始

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` 搭建：

```text
raw/                          # 不可变的源材料
wiki/                         # 智能体维护的知识层
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 派生的索引/缓存/备份/锁（可重建）
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # 此项目的可选插件元数据
```

传递 `--layout ai-wiki` 将 `raw/`/`wiki/`/`.llmw/` 嵌套到 `ai-wiki/` 文件夹下（之后每个命令都会自动检测），以及 `--adopt` 以指向已经有真实内容的 wiki，且使用自己的约定，无需在其上搭建 —— 参见 [docs/zh-Hans/project-layout.md](docs/zh-Hans/project-layout.md)。

## 智能体工作流

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## 命令参考

所有命令都接受 `--json` 以获得机器可解析的输出；大多数读取默认为简洁、上下文节约的视图（使用 `--full`/`--no-brief` 以获取更多）。

| 命令 | 目的 |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | 搭建 `raw/`、`wiki/`、`.llmw/`（使用 `--layout ai-wiki` 时嵌套在 `ai-wiki/` 下），默认还包括 Claude Code 技能/插件。`--adopt` 跳过默认内容/分类搭建，并保护 `config.toml` 不被 `--force` 覆盖，以保留现有 wiki 内容及其配置覆盖 |
| `llmw status [--brief\|--json]` | 页面计数、损坏的链接、孤立页面、最后索引时间、脏页面 |
| `llmw rebuild` | 从头完全重新索引 `wiki/**/*.md` |
| `llmw index [--changed\|--all]` | 增量（默认）或完全重新索引 |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | 对标题/摘要/正文进行 SQLite FTS5 搜索 —— 参见 [docs/zh-Hans/commands.md](docs/zh-Hans/commands.md) 了解搜索语义 |
| `llmw read <path\|title\|alias> [--full\|--brief]` | 查找页面；简洁版显示标题/类型/摘要/关键点/链接/反向链接计数 |
| `llmw links <target>` | 出站链接及其损坏状态 |
| `llmw backlinks <target>` | 入站链接 |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 确定性相关页面候选（无模型调用） |
| `llmw ingest <raw/...>` | 将 `.md`/`.txt` 源注册为 `wiki/sources/<slug>.md` 草稿 |
| `llmw write <path> --reason "..." --stdin [--force]` | 从 stdin 创建新的 wiki 页面 |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 在现有页面中精确字符串替换（语义与原生编辑工具相同） |
| `llmw patch <path> --reason "..." --stdin` | 对现有页面应用统一差异（先备份，失败时回滚） |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | 将页面移至 `wiki/archived/YYYY/MM/`，加上存档前置元数据，记录更改 |
| `llmw lint [--brief\|--json]` | 损坏的链接、孤立页面、重复的标题/别名、缺失/无效的前置元数据、悬挂的原始引用、存档页面链接 —— 仅报告，永不自动修复 |
| `llmw health [--brief]` | 系统检查：配置、索引数据库、架构版本、目录、锁 |
| `llmw graph build` / `llmw graph export --format json\|html` | 重新生成/导出链接图 |

## 安全规则

- `raw/` 不可变。`write`/`patch`/`archive` 拒绝其下任何路径。
- 每个 `write`/`patch`/`archive` 都需要 `--reason`，记录在 `wiki/log.md` 和 `log_entries` 表中。
- 没有 `delete` —— 使用 `archive`。默认保留墓碑存根在原始位置，指向新位置。
- `patch` 在应用统一差异前备份文件，如果差异不能干净地应用（上下文不匹配），则保留原始文件不变。
- 一个简单的建议锁（`.llmw/locks/write.lock`）防止两个 `llmw` 进程同时变更 wiki。

## 文档

| 文档 | 涵盖内容 |
|---|---|
| [docs/zh-Hans/installation.md](docs/zh-Hans/installation.md) | 完整的独立 CLI 安装矩阵（Windows/macOS/Linux）、更新、卸载 |
| [docs/zh-Hans/hooks.md](docs/zh-Hans/hooks.md) | Claude Code 插件的 `PreToolUse` wiki 守卫和自愈 `SessionStart` 版本同步钩子 |
| [docs/zh-Hans/commands.md](docs/zh-Hans/commands.md) | 搜索语义（3 层回退、韩语助词词干提取） |
| [docs/zh-Hans/project-layout.md](docs/zh-Hans/project-layout.md) | 经典 vs. `ai-wiki/` 布局、`--root`/`LLMW_ROOT`、`--adopt`、将 `llmw` 适应到现有 wiki 的约定、Obsidian 兼容性注意事项 |
| [docs/zh-Hans/development.md](docs/zh-Hans/development.md) | 开发设置、Claude Code 技能、MVP 范围 |

## 许可

MIT —— 参见 [LICENSE](LICENSE)。
