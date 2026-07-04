# インストール

[English](../en/installation.md) · [한국어](../ko/installation.md) · **日本語** · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · [Français](../fr/installation.md)

## 推奨：Claude Code プラグイン

Claude Code から `llmw` を使用する場合、プラグインとしてインストールしてください — これは推奨パスであり、別の `pip`/`uv`/`pipx` ステップが不要です：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

（非対話型等価物：`claude plugin marketplace add duddudcns/llm-wiki-cli` と `claude plugin install llm-wiki@llm-wiki-cli`）

これは Claude Code スキルと、スタンドアロン `llmw` バイナリをインストール状態に保ち自動的に同期し、エージェントがそれをバイパスするのを防ぐ 2 つのフックをインストールします — [hooks.md](hooks.md) を参照してそれらのフックが正確に何をするか、どのように設定するかを確認。別の方法で CLI インストール自体を管理したい場合は、これをスキップして下記の方法の 1 つを使用してください — それらは競合しません。両方もインストールできます。

## スタンドアロン CLI

Claude Code の外で PATH に `llmw` を欲しい場合（スクリプティング、CI、別のエディター/エージェント）、または CLI インストール自体をプラグインの自己修復フックの代わりに手動で制御したい場合、これを選んでください。

`llmw` には **Python 3.11 以上** が必要であり、PyPI にはまだないため、パッケージインデックスではなくこのレポから直接インストールします。**このリポジトリは現在プライベート** です — インストール（下記の任意の方法）には認証済みの `git`（例えば既に `gh auth login` でログインしている、または GitHub アカウントに SSH キーがある）が必要です。レポアクセスがない者は部分的なインストール ではなく、取得エラーを取得します。

以下のすべての方法は、他の Python プロジェクトの依存関係に触れないグローバル `llmw` コマンドを与えます。

### Windows

最初に Python バージョンをチェック（PowerShell または Git Bash）：

```powershell
python --version
```

3.11+ をまだ持っていませんか？

```powershell
winget install Python.Python.3.12
```

または [python.org/downloads](https://www.python.org/downloads/) からインストーラをダウンロード。

その後、[uv](https://docs.astral.sh/uv/) を使用（推奨 — 高速、別の pipx インストール不要）：

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/)：

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または plain pip（現在アクティブな Python 環境にインストール — venv を使用しない限り）：

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Code プラグインのフック（[hooks.md](hooks.md) を参照）は Windows 上で Git Bash を必要とします — Claude Code は Git Bash がインストールされていない場合 PowerShell に戻り、これらのシェル形式フックはサポートされません。`llmw` 自身のセーフティゲートはいずれにしても保持されます。フックの追加の利便性だけが影響を受けます。

### macOS

最初に Python バージョンをチェック：

```bash
python3 --version
```

3.11+ をまだ持っていませんか？

```bash
brew install python@3.12
```

その後、[uv](https://docs.astral.sh/uv/) を使用（推奨）：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または plain pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

最初に Python バージョンをチェック：

```bash
python3 --version
```

3.11+ をまだ持っていませんか？

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

その後、[uv](https://docs.astral.sh/uv/) を使用（推奨）：

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/)：

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または plain pip：

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### ローカルクローン、編集可能インストール（`llmw` 自体に貢献する場合）

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # すべてのテストが成功するはずです
```

dev ワークフローの残りは [development.md](development.md) を参照。

### 検証

```bash
llmw --version
llmw --help
```

### 更新

```bash
uv tool upgrade llmw           # uv でインストールした場合
pipx upgrade llmw              # pipx でインストールした場合
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # plain pip
```

（Claude Code プラグインを使用している場合、マーケットプレイスからプラグインを更新することも、スタンドアロン CLI を自動的に同期して保ちます — [hooks.md](hooks.md) を参照。）

### アンインストール

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
