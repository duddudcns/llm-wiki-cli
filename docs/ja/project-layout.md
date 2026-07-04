# プロジェクトレイアウト、既存 wiki の採用、Obsidian 互換性

[English](../en/project-layout.md) · [한국어](../ko/project-layout.md) · **日本語** · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · [Français](../fr/project-layout.md)

## プロジェクトレイアウト：クラシック vs. `ai-wiki/`

デフォルト（`--layout classic`）では `raw/`、`wiki/`、`.llmw/` はプロジェクトルートに直接座ります。代わりに 1 レベル下にネストさせるために `--layout ai-wiki` を渡します。ルートをきれいに保ちます：

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # クラシックレイアウトと同じコンテンツ、ネスト
.claude/skills/llm-wiki/       # まだ実プロジェクトルートでスキャフォールド
.claude-plugin/plugin.json     # まだ実プロジェクトルートでスキャフォールド
```

すべてのコマンドはプロジェクトがどのレイアウトを使用するかを自動検出 — まずプロジェクトルートで `.llmw/` をチェック、その後 `ai-wiki/.llmw` にフォールバック。既存クラシックレイアウトプロジェクトは移行を必要としません。

プロジェクトが現在のディレクトリから自動検出できない場合（例えばスクリプトが別の場所から実行、または非標準チェックアウト）、`--root <path>` または `LLMW_ROOT` 環境変数で `llmw` を明示的に指します — どちらのレイアウトもチェック、したがって単一の値で十分（`raw/`/`wiki/`/`.llmw/` を個別に指定する必要なし）：

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## 既存 wiki を採用

`raw/`/`wiki/`（または `ai-wiki/` ネスト等価物）が既に独自の規約の下で実際のコンテンツを持つ場合 — 例えば `llmw` に先立つ手書き Karpathy パターン wiki — plain `init` の代わりに `--adopt` を使用：

```bash
llmw init --adopt                  # または: llmw init --layout ai-wiki --adopt
```

`--adopt` は最初の実行で `.llmw/` と `config.toml` を作成しますが、デフォルトコンテンツファイル（`raw/README.md`、`wiki/index.md`、`wiki/overview.md`、`wiki/log.md`）またはデフォルトタクソノミサブフォルダ（`entities/`、`concepts/`、`decisions/`、`syntheses/`、`projects/`、`glossary/`、`archived/`、`sources/`） — **`--force` でさえ** — を書き込みません。したがって既存のそれらのパスのコンテンツは一切触れられ、上書きされません。`config.toml` が存在するいったん、`--force` はそれもデフォルトに書き直しません。したがって採用したスキーマのための手調整オーバーライド（下記を参照）は再 `init --adopt --force` を生き残ります。plain `llmw init`（`--adopt` なし）はいつもそれらのデフォルトをスキャフォールド、`--force` で上書き、`--force` で `config.toml` もリセット。空白の（または既に llmw 管理）ディレクトリに対してのみ使用します。既存スキーマの癖（例えば `created`/`updated` の代わりに `last_updated` フィールド、または `wiki/` 外で根レベル `index.md`/`log.md` ファイル）は `.llmw/config.toml` の `lint.required_frontmatter` と `paths.extra_root_pages` を使用して処理 — 下記を参照。

## llmw を既存 wiki に適応

wiki が既に独自の規約を持つ場合（異なるフロントマターフィールド、根レベルで `wiki/` 外で座ったファイル）、その根に `llmw init --adopt` を指す（上記を参照）、wiki ファイルを再編成するのではなく `.llmw/config.toml` を調整：

```toml
[paths]
# wiki/**/*.md と一緒にインデックス付きされるべき追加個別 Markdown ファイル
# （プロジェクトルートに相対） — 例えば wiki/ 外で保持されたスキーマ/インデックス/ログファイル。
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# `llmw lint` がどのフロントマターキーを必須とするかオーバーライド。
# デフォルトは ["type", "status", "created", "updated"]；"updated" も
# `last_updated` キーを受け入れ。
required_frontmatter = ["type", "status", "last_updated"]
```

既存ページは変更を必要としません — `llmw rebuild` は次の実行時に新しい設定を受け取ります。

## Obsidian 互換性

`wiki/` は YAML フロントマターと `[[wikilinks]]` を持つプレーン Markdown — GUI でグラフビュー、バックリンク、検索を取得するために直接 Obsidian ボルトとして開いて、CLI 駆動エージェントワークフローの任意をあきらめません。

リンク解決は特に現実世界の Obsidian エクスポート癖を処理：

- `[[Page]]`、`[[Page|Alias]]`、`[[Page#Heading|Alias]]`、`[[#Heading]]`、`![[Embed]]` — 完全なウィキリンク文法。
- パスライクウィキリンクターゲット（`[[concepts/foo]]`）はボルトルート（`wiki/`）に相対的に解決、実際に `wiki/` をボルトとして開くとき Obsidian がそれらを解決する方法に一致 — リンクページ自身のフォルダにただ相対的ではなく。
- `related:` フロントマターはインラインウィキリンクと同じ第一級リンクソース — プレーンパス/タイトル（`related: [wiki/concepts/foo]`、いくつかの wiki が `llmw` の採用前に使用した規約）と Obsidian 自身のプロパティパネル形式（`related: ["[[Note]]"]`）両方正しく解決。
- URL エンコードターゲットを持つ Markdown リンク（`[Profile](Project%20Profile.md)`、ファイル名が空白を持つときに一般的）は オンディスクページに一致させる前にデコードされます。
- wiki/ 外を指すリラティブウィキリンク（例 `[[../notes/x]]`）は実ファイルシステムに対してチェック — ただ `llmw lint` でインデックス付き wiki ページではないため壊れたと報告、またはターゲットが プロジェクトの全体でどこかで本当に存在しないのみ。

**グラフが意図的に Obsidian 自身から発散する場所**：`related:` エッジと llmw のタイトルベースウィキリンク解決（`[[Exact Page Title]]` ファイル名に一致しない場合でさえ解決）両方 llmw 拡張で Obsidian 等価物なし — Obsidian 自身のグラフビューはそれらのエッジを表示しません。異なるフォルダで同じファイル名語幹を持つ 2 ページもまた両方の道具で曖昧に解決（最初の一致勝利）。`wiki/` を Obsidian で開くことはピクセル同等ではなく同じファイルの上で実用的で有用なグラフを取得します。
