# 开发

[English](../en/development.md) · [한국어](../ko/development.md) · [日本語](../ja/development.md) · **简体中文** · [Español](../es/development.md) · [Français](../fr/development.md)

参见 [installation.md](installation.md) 的"本地克隆、可编辑安装"部分来设置开发环境；`pytest` 从那里运行测试套件。

## Claude Code 技能

`llmw init` 写 `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}` 到项目中。Claude Code 自动发现这作为纯技能 —— 无安装步骤。它告诉智能体何时使用 `llmw`、核心搜索优先工作流，并指向 `reference.md`/`examples.md` 获取完整细节，所以总是加载的 `SKILL.md` 保持简短。

如果 llm-wiki Claude Code 插件已从市场安装，传递 `--no-claude-plugin` 来跳过此项目本地副本 —— 否则项目最终有相同技能的两个副本（市场插件的，和这个），这是冗余且当 Claude Code 加载两个时可能令人困惑。

## MVP 范围

故意排除：MCP 服务器、daemon/watch 模式、嵌入/向量搜索、直接 PDF/DOCX 解析、Obsidian 插件、web UI 和任何自动合并/自动删除/矛盾检测逻辑。
