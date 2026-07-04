# llmw

[English](README.md) · [한국어](README.ko.md) · **日本語** · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · [Français](README.fr.md)

AI エージェント向けのヘッドレス Obsidian ライクな LLM Wiki CLI。

## なぜ llmw か

MCP ツールは便利ですが、ツールスキーマと長い説明はターン毎にコンテキストを消費します。`llmw` は異なるアプローチをとります：小さく決定的な CLI と Claude Code スキル。エージェントは必要な時だけ wiki を呼び出し、CLI 自体はモデルを呼び出さず、インデックス、検索、検証だけを行います。

## コンセプト

- **Karpathy LLM Wiki** — `raw/` は不変のソース材料を保持し、`wiki/` は AI エージェントが書いて管理する永続的な知識層です。これは通常の RAG ではなく、wiki は複合アーティファクトです。
- **Obsidian スタイルのウィキリンク** — `[[Page]]`、`[[Page|Alias]]`、`[[Page#Heading]]`、`![[Embed]]`、バックリンク、タグ、YAML フロントマター。`wiki/` は有効な Obsidian ボルトです。必要に応じて開いて、同じファイルの上に人間用の視覚的 IDE を置くことができます。
- **Markdown がソースオブトゥルース** — `.llmw/index.sqlite` と `.llmw/graph.json` は派生、再構築可能なデータです。`llmw rebuild` は `wiki/*.md` だけから両者を再生成します。
- **AI エージェントが wiki を書き、CLI がインデックスして検証する** — 検索 (SQLite FTS5)、バックリンク、関連ページスコアリング、lint はすべて決定的、ルールベース、モデルフリーです。ソースの要約、ページの執筆、アーカイブすべきものの判断はエージェントの仕事です。

## インストール

**推奨：Claude Code プラグイン** — 別の `pip`/`uv`/`pipx` ステップ不要：

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

これは CLI 自体の同期を自動的に保ち、エージェントがそれをバイパスするのを防ぐフックもインストールします — [docs/ja/hooks.md](docs/ja/hooks.md) を参照。

スタンドアロン CLI を直接欲しい場合（スクリプティング、CI、別のエディター）、またはアップグレードを自分で管理したい場合は、[docs/ja/installation.md](docs/ja/installation.md) を参照してください。そこには Windows/macOS/Linux 全体の完全な uv/pipx/pip/dev インストールマトリックスがあります。2 つは競合しません — 両方をインストールできます。

## クイックスタート

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` がスキャフォールドします：

```text
raw/                          # 不変のソース材料
wiki/                         # エージェント管理の知識層
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 派生インデックス/キャッシュ/バックアップ/ロック (再構築可能)
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # このプロジェクト用の任意プラグインメタデータ
```

`--layout ai-wiki` を渡して `raw/`/`wiki/`/`.llmw/` を `ai-wiki/` フォルダの下にネストさせる（その後のすべてのコマンドで自動検出）、`--adopt` を渡して既に実際のコンテンツを持つ wiki に llmw を指し示す（それ自身の規約の下で、それをスキャフォールドの上に置かずに）— [docs/ja/project-layout.md](docs/ja/project-layout.md) を参照。

## エージェント ワークフロー

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## コマンドリファレンス

すべてのコマンドは `--json` でマシン読み取り可能な出力を受け入れます。ほとんどの読み取りはデフォルトで簡潔なコンテキスト安価なビュー (`--full`/`--no-brief` でより多く)。

| コマンド | 目的 |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | `raw/`、`wiki/`、`.llmw/` をスキャフォールド (`--layout ai-wiki` で `ai-wiki/` の下にネスト)、デフォルトで Claude Code スキル/プラグイン。`--adopt` はデフォルトコンテンツ/タクソノミスキャフォールドをスキップし、`--force` から `config.toml` を保護して既存 wiki コンテンツとその設定オーバーライドを保持 |
| `llmw status [--brief\|--json]` | ページ数、壊れたリンク、孤立、最後のインデックス時刻、ダーティページ |
| `llmw rebuild` | `wiki/**/*.md` を最初から完全に再インデックス |
| `llmw index [--changed\|--all]` | インクリメンタル（デフォルト）または完全な再インデックス |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | タイトル/概要/本文上の SQLite FTS5 検索 — 検索セマンティクスは [docs/ja/commands.md](docs/ja/commands.md) を参照 |
| `llmw read <path\|title\|alias> [--full\|--brief]` | ページを検索。brief はタイトル/タイプ/概要/キーポイント/リンク/バックリンク数を表示 |
| `llmw links <target>` | 発信リンク、壊れた状態付き |
| `llmw backlinks <target>` | 着信リンク |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 決定的な関連ページ候補（モデル呼び出しなし） |
| `llmw ingest <raw/...>` | `.md`/`.txt` ソースを `wiki/sources/<slug>.md` ドラフトとして登録 |
| `llmw write <path> --reason "..." --stdin [--force]` | stdin から新しい wiki ページを作成 |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 既存ページ内の完全一致文字列置換（ネイティブ Edit ツールと同じセマンティクス） |
| `llmw patch <path> --reason "..." --stdin` | 既存ページに統一形式の diff を適用（先にバックアップ、失敗時にロールバック） |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | ページを `wiki/archived/YYYY/MM/` に移動、アーカイブフロントマターをスタンプ、変更をログ |
| `llmw lint [--brief\|--json]` | 壊れたリンク、孤立、重複したタイトル/エイリアス、不正なフロントマター、ぶら下がった raw refs、アーカイブページリンク — レポートのみ、自動修正しない |
| `llmw health [--brief]` | システムチェック：設定、インデックス db、スキーマバージョン、ディレクトリ、ロック |
| `llmw graph build` / `llmw graph export --format json\|html` | リンクグラフを再生成/エクスポート |

## セーフティ ルール

- `raw/` は不変。`write`/`patch`/`archive` はその下の任意のパスを拒否。
- すべての `write`/`patch`/`archive` は `--reason` を必須とし、`wiki/log.md` と `log_entries` テーブルに記録。
- `delete` はない — `archive` を使用。デフォルトは元の場所を新しい場所に指す短いスタブを保持。
- `patch` はファイルを diff 適用前にバックアップし、diff がクリーンに適用されない場合（コンテキストミスマッチ）元のファイルは変更されないままにします。
- 簡単なアドバイザリロック (`.llmw/locks/write.lock`) は 2 つの `llmw` プロセスが同時に wiki を変更するのを保護。

## ドキュメンテーション

| ドキュメント | カバー |
|---|---|
| [docs/ja/installation.md](docs/ja/installation.md) | 完全なスタンドアロン CLI インストールマトリックス (Windows/macOS/Linux)、更新、アンインストール |
| [docs/ja/hooks.md](docs/ja/hooks.md) | Claude Code プラグインの `PreToolUse` wiki ガード、自己修復 `SessionStart` バージョン同期フック |
| [docs/ja/commands.md](docs/ja/commands.md) | 検索セマンティクス (3 段階フォールバック、韓国語粒子語幹処理) |
| [docs/ja/project-layout.md](docs/ja/project-layout.md) | クラシックvs. `ai-wiki/` レイアウト、`--root`/`LLMW_ROOT`、`--adopt`、llmw を既存 wiki の規約に適応させる、Obsidian 互換性メモ |
| [docs/ja/development.md](docs/ja/development.md) | Dev セットアップ、Claude Code スキル、MVP スコープ |

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
