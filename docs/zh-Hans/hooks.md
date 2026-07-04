# 钩子：让智能体诚实，让 CLI 同步

[English](../en/hooks.md) · [한국어](../ko/hooks.md) · [日本語](../ja/hooks.md) · **简体中文** · [Español](../es/hooks.md) · [Français](../fr/hooks.md)

Claude Code 插件（参见 [installation.md](installation.md)）安装两个钩子。两者都不是使用 `llmw` 的必需 —— 它们是便利性的提升，层叠在一个无论钩子是否运行都已强制执行自身安全规则的 CLI 之上。

## PreToolUse：wiki 守卫

没有什么能阻止智能体忽略 Claude Code 技能，改用自己的文件编辑工具直接编辑 `wiki/*.md` 或 `raw/**` —— 这会跳过 `--reason` 审计日志、前置元数据验证和自动备份，当一个*不同的*、相互竞争的指令集生效且从未提到 `llmw` 时，这在实践中发生。

作为 Claude Code 插件安装时（不是裸露的 `llmw init` 项目技能），一个 `PreToolUse` 钩子在工具支架级别关闭了这个漏洞：针对 `wiki/*.md` 或 `raw/**` 的原生 `Edit`/`Write`/`NotebookEdit` 调用被拒绝（或根据配置，转成确认提示），拒绝消息命名了确切的 `llmw` 命令来运行 —— 所以智能体的下一个动作是一行重写，而不是死胡同。

守卫仅关注 `Edit`/`Write`/`NotebookEdit` 调用，其目标解析（通过从文件向上走，与 `llmw` 查找自身项目根的方式相同）到真实的 llmw 项目的 `wiki/*.md` 或 `raw/**` —— 其他所有东西，包括纯 `Read`，无需改变通过，它从不检查 `Bash` 命令（shell 字符串监管有自己的假阳性雷区，所以 `wiki/log.md` 中的审计跟踪加上 `llmw lint` 仍然是那个漏洞的检测层，而不是一个钩子试图阻止它）。

在每个项目的 `.llmw/config.toml` 中配置或禁用：

```toml
[hooks]
wiki_guard = "deny"  # 默认：阻止，带一条消息命名 llmw 修复
# wiki_guard = "ask"   # 改为提示确认
# wiki_guard = "off"   # 为此项目禁用守卫
```

两个钩子在 Windows 上都需要 Git Bash（当未安装 Git Bash 时，Claude Code 回退到 PowerShell，这些 shell 形式的钩子不支持）—— 其他地方，`llmw` 自身的安全门（需要原因、路径限制、前置元数据验证、写前备份）仍然有效，无论钩子是否运行。

也在每个会话中留下一个短 `SessionStart` 注释到上下文中："此项目有一个 llmw wiki"（带页面计数）当 `.llmw` 已存在时，或一个单行"运行 `llmw init`"提示当它还不存在时 —— 所以一个空白环境，无项目 `CLAUDE.md`，根本没有初始化 wiki，仍然在第一轮发现 `llmw`。

## SessionStart：自愈 CLI 安装

`plugin/bin/llmw` 是一个薄分派器，不是捆绑的 Python 分发 —— 它调用 PATH 上的真实 `llmw`。从市场更新插件仅更新插件自身的文件（技能、钩子）；它**不**接触那个独立的二进制文件。放任不管，那意味着安装插件更新可以悄悄让你运行旧 CLI。

一个 `SessionStart` 钩子（`plugin/hooks/session-start.sh`，通过 `plugin/hooks/hooks.json` 接通）关闭了那个漏洞：每个会话，它比较已安装的 `llmw --version` 与此插件包声明的版本（`plugin/.claude-plugin/plugin.json`）。不匹配时 —— 包括"根本没安装" —— 它通过 `uv tool install --force` 重新安装（回退到 `pip install --user --force-reinstall`），固定到匹配的 `git` 标签（`git+...@v<version>`），所以插件市场更新也带来独立 CLI 二进制文件同步，无需单独手动 `uv tool upgrade llmw`。

当版本已经匹配时，检查只是每个会话的一个本地 `llmw --version` 调用（无网络） —— 重新安装路径仅在真实版本不匹配时运行，大约每个发行版一次。
