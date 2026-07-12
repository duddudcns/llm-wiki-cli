# llmw

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · **简体中文** · [Español](README.es.md) · [Français](README.fr.md)

一个简单的命令行工具，能让 AI 编程助手拥有属于自己的项目笔记本("wiki")——这样它就能记住之前做过的决定、了解到的事实和历史,而不是每次对话之后就把一切都忘光。

## 为什么要用它?

很多 AI 工具的做法是,每条消息都塞进一大堆说明和资料,这样既占地方又拖慢速度。`llmw` 的思路不一样：它是一个很小、很简单的工具,只有 AI 真正需要查资料或记点什么的时候才会用到它。这个工具本身从不"思考"或生成文字——它只是负责把笔记存起来、之后再找出来,以及检查笔记有没有写对格式。真正的思考工作(该写什么、怎么概括)全部由 AI 自己完成,`llmw` 不参与。

## 基本思路

- **两个文件夹,两种用途** —— `raw/` 存放原始资料,这些内容永远不会改动(就像你上传的一份文档)。`wiki/` 是 AI 写自己笔记的地方,它会随着了解得越多不断更新这些笔记——所以这个笔记本会越用越好用,而不只是查一次就完事。
- **笔记之间可以互相链接** —— 页面可以链接到其他页面(有点像维基百科的链接),这样 AI 就能顺着相关笔记的线索找下去。这也能配合大家常用的笔记软件 [Obsidian](https://obsidian.md/) 使用,如果你想自己用可视化的方式浏览这些笔记的话。
- **一切都只是普通的文本文件** —— 每一篇笔记都是一个普通的 Markdown 文件,你自己也能打开看,不需要什么特殊数据库。另外还有一个小小的搜索索引文件,但那只是个辅助工具,需要的话随时都能从笔记内容重新生成出来。
- **AI 负责写,工具只负责检查和整理** —— 搜索、查找相关笔记、检查笔记格式是否正确,这些都是简单、可预测的操作,不涉及任何 AI。至于什么值得记下来、怎么写好,这是 AI 的工作。
- **干活时顺口提到的偏好,它也会自己记下来** —— 干活的时候顺嘴提一句编码习惯或者纠正一下什么,不用你专门说"记住这个"或者"更新一下 wiki",AI 就会自己写进 wiki 或者它自己的规则文件里。要是每次都得这么提醒,那也算不上什么好用的工具。

## 安装

**推荐做法：作为 Claude Code 插件安装** —— 只需要两条命令,不用再折腾别的：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

这样装还会顺带装上几个贴心的安全保障机制,让一切都能自动保持正常运转——详情见 [docs/zh-Hans/hooks.md](docs/zh-Hans/hooks.md)。

想直接安装命令行工具(比如想在 Claude Code 之外使用)?可以看 [docs/zh-Hans/installation.md](docs/zh-Hans/installation.md),里面有针对 Windows、macOS、Linux 的详细步骤。两种方式可以同时装,互不影响。

## 快速上手

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` 会帮你建好这样的文件夹结构：

```text
raw/                          # 原始资料 —— 不会被编辑
wiki/                         # AI 自己的笔记,会不断更新
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 后台用的搜索索引(随时可以重新生成)
.claude/skills/llm-wiki/      # 教 Claude Code 怎么用这个工具
.claude/rules/llm-wiki.md     # 自动提醒开工前搜索、收工后更新 wiki 的规则
.claude-plugin/plugin.json    # 这个项目的可选插件信息
```

想让项目文件夹更清爽,把这些都收进一个子文件夹里?或者想让 `llmw` 使用你早就手动建好的 wiki?可以看看 [docs/zh-Hans/project-layout.md](docs/zh-Hans/project-layout.md)。

## AI 的典型使用流程

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## 全部命令

每个命令都支持 `--json`,如果你想要程序能读懂的输出格式。大多数"读取"类命令默认只显示简短摘要(加上 `--full`/`--no-brief` 可以看到全部内容)。

| 命令 | 作用 |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | 为新项目搭建 `raw/`、`wiki/` 和搜索索引(如果是已有项目,加上 `--adopt`——参见 [docs/zh-Hans/project-layout.md](docs/zh-Hans/project-layout.md)) |
| `llmw status [--brief\|--json]` | 快速健康检查：有多少篇笔记、有没有失效的链接、上次更新是什么时候 |
| `llmw rebuild` | 把整个搜索索引从头重新建一遍 |
| `llmw index [--changed\|--all]` | 更新搜索索引(默认只更新有变化的部分) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | 搜索所有笔记——搜索具体是怎么工作的,参见 [docs/zh-Hans/commands.md](docs/zh-Hans/commands.md) |
| `llmw read <path\|title\|alias> [--full\|--brief]` | 打开一篇笔记;简短版会显示标题、摘要和链接 |
| `llmw links <target>` | 显示某篇笔记链接到了哪些其他笔记 |
| `llmw backlinks <target>` | 显示有哪些其他笔记链接到了这一篇 |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 推荐相关笔记,用的是简单规则(不涉及 AI 猜测) |
| `llmw ingest <raw/...>` | 把一份原始资料变成一篇草稿笔记,方便 AI 接着填写 |
| `llmw write <path> --reason "..." --stdin [--force]` | 创建一篇全新的笔记 |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 把一篇现有笔记里的某段文字精确替换掉 |
| `llmw patch <path> --reason "..." --stdin` | 对一篇笔记应用一组改动(会先备份,出问题时自动撤销) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | 把一篇旧笔记挪到一边而不是直接删掉,并留下一个指向新位置的提示 |
| `llmw lint [--brief\|--json]` | 检查各种问题——失效链接、缺信息、标题重复——但从不自动修复 |
| `llmw health [--brief]` | 检查后台的各项设置是否正常 |
| `llmw graph build` / `llmw graph export --format json\|html` | 生成或导出一张笔记之间链接关系的可视化地图 |

## 内置的安全规则

- `raw/` 里的原始资料永远不能被改动——工具会直接拒绝。
- 对笔记的每一次改动都必须附上一个简短的理由,这个理由会被永久记录在历史日志里。
- 没有"删除"这个操作——只有"归档",会把笔记挪到一边,并留下一个路标,确保什么都不会凭空消失。
- 应用一组改动时,总是会先备份,如果中途出了什么问题,会自动撤销。
- 一个简单的锁文件能防止工具的两个副本同时编辑同一篇笔记、互相冲突。

## 更多文档

| 文档 | 内容 |
|---|---|
| [docs/zh-Hans/installation.md](docs/zh-Hans/installation.md) | Windows、macOS、Linux 的完整安装说明;如何更新或卸载 |
| [docs/zh-Hans/hooks.md](docs/zh-Hans/hooks.md) | Claude Code 插件如何防止 AI 绕开 wiki,以及如何自动保持自身更新 |
| [docs/zh-Hans/commands.md](docs/zh-Hans/commands.md) | 搜索背后到底是怎么工作的 |
| [docs/zh-Hans/project-layout.md](docs/zh-Hans/project-layout.md) | wiki 文件夹的不同组织方式、如何接手你已有的 wiki、如何搭配笔记软件 Obsidian 使用 |
| [docs/zh-Hans/development.md](docs/zh-Hans/development.md) | 如何搭建开发环境来参与 `llmw` 本身的开发 |

## 许可证

MIT —— 见 [LICENSE](LICENSE)。
