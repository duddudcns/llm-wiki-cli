# 安装

[English](../en/installation.md) · [한국어](../ko/installation.md) · [日本語](../ja/installation.md) · **简体中文** · [Español](../es/installation.md) · [Français](../fr/installation.md)

## 推荐做法：Claude Code 插件

如果你是在 Claude Code 里使用 `llmw`,建议直接把它装成插件——这是推荐的方式,完全不用另外走 `pip`/`uv`/`pipx` 那一套步骤：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(非交互式的写法：`claude plugin marketplace add duddudcns/llm-wiki-cli`
和 `claude plugin install llm-wiki@llm-wiki-cli`)

这样装还会附带四个安全保障机制：一个负责自动让命令行工具本身保持最新,一个负责防止 AI 绕开 wiki、直接改文件,另外两个会提醒 AI 在开始新工作前先去搜一搜 wiki、做完之后再去更新 wiki——具体是怎么做的、以及不想要的话怎么关掉,可以看 [hooks.md](hooks.md)。如果你更想自己安装命令行工具、自己手动管理更新,可以跳过这一步,改用下面的方法——两者不会冲突,你可以两个都装。

## 单独安装命令行工具(不装插件)

如果你想在 Claude Code 之外使用 `llmw`——比如写脚本、搭自动化流程,或者配合别的编辑器/工具——就选这个方式。

`llmw` 需要 **Python 3.11 或更高版本**。它目前还没有发布到公共的包索引上,所以是直接从这个 GitHub 仓库安装的。**这个仓库目前是私有的**——不管用下面哪种方法安装,都需要你自己的 GitHub 账号已经给 `git` 配置好了(比如已经用 `gh auth login` 登录过,或者给你的 GitHub 账号加了 SSH key)。如果没配置好,安装会直接报一个清楚的错误,而不会装出一个坏掉的东西。

下面每一种方法安装完,你都会得到一个随处可用的 `llmw` 命令,而且不会影响你电脑上其他的 Python 项目。

### Windows

先看看你现在的 Python 版本是多少(PowerShell 或 Git Bash 里都行)：

```powershell
python --version
```

还没有 3.11 以上的版本?

```powershell
winget install Python.Python.3.12
```

或者直接去 [python.org/downloads](https://www.python.org/downloads/) 下载安装包。

然后,用 [uv](https://docs.astral.sh/uv/)(推荐——速度快,也不用另外装 pipx)：

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者用 [pipx](https://pipx.pypa.io/)：

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者直接用 pip(这会装到你电脑当前正在用的那个 Python 环境里——只有在你确定自己想这么做的时候才用这种方式)：

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Code 插件的安全保障功能(见 [hooks.md](hooks.md))在 Windows 上需要装了"Git Bash"才能运行。如果没装,这些额外功能就是不会跑而已——`llmw` 本身照样能正常工作,它自带的安全检查也一样会生效。

### macOS

先看看你现在的 Python 版本是多少：

```bash
python3 --version
```

还没有 3.11 以上的版本?

```bash
brew install python@3.12
```

然后,用 [uv](https://docs.astral.sh/uv/)(推荐)：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者用 [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者直接用 pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

先看看你现在的 Python 版本是多少：

```bash
python3 --version
```

还没有 3.11 以上的版本?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

然后,用 [uv](https://docs.astral.sh/uv/)(推荐)：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者用 [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

或者直接用 pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### 参与 `llmw` 自身的开发

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # 应该会显示所有测试都通过
```

想了解更多关于参与开发的内容,可以看 [development.md](development.md)。

### 确认安装成功

```bash
llmw --version
llmw --help
```

### 获取更新

```bash
uv tool upgrade llmw           # 如果是用 uv 装的
pipx upgrade llmw              # 如果是用 pipx 装的
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # 普通 pip
```

(如果你装的是 Claude Code 插件,从应用市场更新插件时也会自动一并更新命令行工具——见 [hooks.md](hooks.md)。)

### 卸载

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
