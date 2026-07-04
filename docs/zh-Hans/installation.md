# 安装

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · **简体中文** · [Español](../es/installation.md) · [Français](../fr/installation.md)

## 推荐：Claude Code 插件

如果从 Claude Code 使用 `llmw`，将其作为插件安装 —— 这是推荐的方式，不需要单独的 `pip`/`uv`/`pipx` 步骤：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

（非交互式等效命令：`claude plugin marketplace add duddudcns/llm-wiki-cli` 和 `claude plugin install llm-wiki@llm-wiki-cli`）

这会安装 Claude Code 技能加上两个钩子，这些钩子会自动保持独立的 `llmw` 二进制文件安装和同步，并防止智能体绕过它 —— 参见 [hooks.md](hooks.md) 了解这些钩子的具体作用和配置方式。如果你想自己管理 CLI 安装，跳过这个，改用下面的方法之一 —— 它们不冲突，你也可以同时安装两个。

## 独立 CLI

如果想在 Claude Code 之外的 PATH 上使用 `llmw`（脚本编写、CI、其他编辑器/智能体），或者想手动控制升级而不是使用插件的自愈钩子，选择这个。

`llmw` 需要 **Python 3.11 或更高版本**，且尚未在 PyPI 上，所以直接从此仓库安装而不是从包索引。**此仓库目前是私有的** —— 安装它（任何下面的方法）需要您自己的身份验证 `git`（例如已通过 `gh auth login` 登录，或在 GitHub 账户上有 SSH 密钥）；没有仓库访问权限的人会得到获取错误，而不是部分安装。

下面的所有方法都能让您获得全局 `llmw` 命令，不会接触任何其他 Python 项目的依赖。

### Windows

首先检查您的 Python 版本（PowerShell 或 Git Bash）：

```powershell
python --version
```

没有 3.11+ 版本？

```powershell
winget install Python.Python.3.12
```

或从 [python.org/downloads](https://www.python.org/downloads/) 下载安装程序。

然后，使用 [uv](https://docs.astral.sh/uv/)（推荐 —— 快速，无需单独的 pipx 安装）：

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或 [pipx](https://pipx.pypa.io/)：

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或纯 pip（安装到当前活跃的 Python 环境 —— 除非你知道想要全局，否则使用 venv）：

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Code 插件的钩子（参见 [hooks.md](hooks.md)）在 Windows 上需要 Git Bash —— 当未安装 Git Bash 时，Claude Code 回退到 PowerShell，这些 shell 形式的钩子不支持。`llmw` 自身的安全门仍然有效；只是钩子的额外便利受到影响。

### macOS

首先检查您的 Python 版本：

```bash
python3 --version
```

没有 3.11+ 版本？

```bash
brew install python@3.12
```

然后，使用 [uv](https://docs.astral.sh/uv/)（推荐）：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或 [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或纯 pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

首先检查您的 Python 版本：

```bash
python3 --version
```

没有 3.11+ 版本？

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

然后，使用 [uv](https://docs.astral.sh/uv/)（推荐）：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或 [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或纯 pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### 本地克隆、可编辑安装（用于为 `llmw` 本身贡献）

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # 应显示所有测试通过
```

参见 [development.md](development.md) 了解其余开发工作流。

### 验证

```bash
llmw --version
llmw --help
```

### 更新

```bash
uv tool upgrade llmw           # 如果通过 uv 安装
pipx upgrade llmw              # 如果通过 pipx 安装
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # 纯 pip
```

（如果使用 Claude Code 插件，从市场更新插件也会自动保持独立 CLI 同步 —— 参见 [hooks.md](hooks.md)。）

### 卸载

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
