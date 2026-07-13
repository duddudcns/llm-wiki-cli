# 参与 `llmw` 的开发

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · **简体中文** · [Español](../es/development.md) · [Français](../fr/development.md)

参考 [installation.md](installation.md) 里"参与 `llmw` 自身的开发"这一节来搭建开发环境;搭好之后在里面跑 `pytest` 就能运行测试。

## Claude Code 技能是怎么工作的

`llmw init` 会在你项目的 `.claude/skills/llm-wiki/` 目录下写入几个文件。Claude Code 会自动识别这些文件——不需要另外单独安装。这些文件教会 AI 什么时候该用 `llmw`、该怎么用,而不需要每次都把所有细节都加载进来。

如果你已经从应用市场装了 Claude Code 插件,那运行 `llmw init` 的时候加上 `--no-claude-plugin`,跳过再创建这一份多余的副本——不然你就会有两份一模一样的说明,既多余又可能造成混乱。

不管加没加 `--no-claude-plugin`,`llmw init` 都会一直写入 `.claude/rules/llm-wiki.md`。Claude Code 的插件清单能分发 hooks 和 skills,却没办法分发 `.claude/rules/` 里的内容,所以这是唯一能把"开工前搜索、收工后更新"这条提醒自动加载进每次会话上下文的途径,也不会跟应用市场版插件产生重复。

`llmw init` 同样也会在 `.codex/rules/llm-wiki.md` 里写入相同的指导,每次都写,不管你实际用不用这个插件(或者两个都不用)——Codex 的插件清单跟 Claude Code 一样,也是能分发 hooks 和 skills 但没办法分发 `.codex/rules/` 里的内容。这个文件是无条件创建的,而不是被某个只针对 Codex 的开关控制:一个项目里没人用的平台的空规则文件是无害的,而一个同时用 Claude Code 和 Codex 的团队可以一次初始化就把两个都配好,不用额外折腾。

## 这个工具目前刻意不做的事

按照设计,以下这些暂时都不在这个工具的范围之内：直接连接 AI 模型、自动监控文件变化、AI 驱动的语义搜索、直接读取 PDF/Word 文件、图形界面应用,以及任何自动合并/删除/解决笔记冲突的功能。
