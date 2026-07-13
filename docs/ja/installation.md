# インストール方法

[English](../en/installation.md) · [한국어](../ko/installation.md) · **日本語** · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · [Français](../fr/installation.md)

## おすすめ: Claude Codeのプラグイン

Claude Codeから `llmw` を使うなら、プラグインとしてインストールするのが一番おすすめです。これなら `pip`/`uv`/`pipx` といった別の手順は不要です。

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(コマンドを直接打ちたい場合はこちら: `claude plugin marketplace add duddudcns/llm-wiki-cli` と `claude plugin install llm-wiki@llm-wiki-cli`)

これを実行すると、4つの安全装置も一緒にインストールされます。1つはコマンドラインツール自体を自動的に最新の状態に保つもの、1つはAIがwikiを飛ばして直接ファイルを編集してしまうのを防ぐもの、そして残り2つは新しい作業を始める前にwikiを検索し、作業が終わったらwikiを更新するようAIに促すものです。それぞれが具体的に何をするか、そしてオフにしたい場合の方法は [hooks.md](hooks.md) を見てください。もしコマンドラインツールは自分で入れて、アップデートも自分で管理したいなら、これは飛ばして下の方法のどれかを使ってください。両方インストールしても問題ありません、干渉し合うことはありません。

## Codexプラグイン

GitHubのマーケットプレイスから直接インストールし、続いてプラグインをインストールします。

```powershell
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

`codex plugin list` で確認してください。プラグインはMCPサーバー経由でネイティブなwikiツールを提供し、`uvx` を使って固定されたGitHubリリースを自動取得します。`uvx --version` が使えない場合は、まず [uv](https://docs.astral.sh/uv/) をインストールしてください。Codexは Claude Codeプラグインのフックファイルを実行しません — 代わりに Codex 自体の別個の PreToolUse/Stop フック(検索前・更新後という同じ仕組みを Codex のツール体系に合わせて移植したもの)を使用します。これらのフックは初回使用時にバックグラウンドで固定バージョンの `llmw` CLI を自動インストールするため、直接ターミナルで使う場合にのみ下記の CLI インストール手順を追加で進めてください。

## コマンドラインツール単体でインストール(プラグインなし)

Claude Codeの外で `llmw` を使いたい場合(スクリプトの中で使う、自動処理の一部にする、他のエディターやツールと組み合わせるなど)は、こちらを選んでください。

`llmw` を動かすには **Python 3.11以降** が必要です。まだ一般公開のパッケージ置き場には登録されていないので、代わりにこの公開GitHubリポジトリから直接インストールします。リポジトリは公開されているため、GitHubへのログインやSSHキーの設定は不要です。

以下のどの方法でも、パソコン上の他のPythonプロジェクトに影響を与えずに、どこからでも実行できる `llmw` コマンドが手に入ります。

### Windows

まず、今使っているPythonのバージョンを確認します(PowerShellまたはGit Bashで)。

```powershell
python --version
```

3.11以降がまだ入っていない場合。

```powershell
winget install Python.Python.3.12
```

または [python.org/downloads](https://www.python.org/downloads/) からインストーラーをダウンロードしてください。

そのあと、[uv](https://docs.astral.sh/uv/) を使う場合(おすすめ。速いうえ、pipxを別に入れる必要もありません)。

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/) を使う場合。

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または普通のpipを使う場合(これは今パソコンで有効になっているPython環境にそのまま入ります。それでよいと分かっている場合だけにしてください)。

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Codeプラグインの安全装置の機能([hooks.md](hooks.md) 参照)を使うには、Windowsで「Git Bash」がインストールされている必要があります。もし入っていなければ、その追加機能だけが動かなくなります。`llmw` 自体は問題なく動きますし、`llmw` 自身の安全チェックはどちらにしてもきちんと働きます。

### macOS

まず、今使っているPythonのバージョンを確認します。

```bash
python3 --version
```

3.11以降がまだ入っていない場合。

```bash
brew install python@3.12
```

そのあと、[uv](https://docs.astral.sh/uv/) を使う場合(おすすめ)。

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/) を使う場合。

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または普通のpipを使う場合。

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

まず、今使っているPythonのバージョンを確認します。

```bash
python3 --version
```

3.11以降がまだ入っていない場合。

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

そのあと、[uv](https://docs.astral.sh/uv/) を使う場合(おすすめ)。

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または [pipx](https://pipx.pypa.io/) を使う場合。

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

または普通のpipを使う場合。

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### `llmw` そのものの開発に参加する

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # すべてのテストが通るはずです
```

開発への参加についてもっと詳しくは [development.md](development.md) を見てください。

### 正しく入ったか確認する

```bash
llmw --version
llmw --help
```

### アップデートする

```bash
uv tool upgrade llmw           # uvでインストールした場合
pipx upgrade llmw              # pipxでインストールした場合
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # 普通のpipの場合
```

(Claude Codeのプラグインをインストールしている場合は、マーケットプレイスからプラグインを更新するだけで、コマンドラインツールも自動的に一緒に更新されます。詳しくは [hooks.md](hooks.md) を参照してください。)

### 削除する

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
