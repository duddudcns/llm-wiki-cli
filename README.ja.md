# llmw

[English](README.md) · [한국어](README.ko.md) · **日本語** · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · [Français](README.fr.md)

AIコーディングアシスタントに、プロジェクト専用の「メモ帳(wiki)」を持たせるためのシンプルなコマンドラインツールです。これがあれば、AIは会話をまたぐたびに全部忘れてしまう代わりに、決め事や事実、経緯を覚えておけます。

## なぜ使うのか

多くのAIツールは、毎回のメッセージに大量の指示やデータを詰め込むやり方をしています。これはスペースの無駄遣いになるうえ、動作も遅くなります。`llmw` はやり方が違います。本当に何かを調べたり書き留めたりする必要があるときだけ、AIがちょっと呼び出す小さくてシンプルな道具です。ツール自体が「考えたり」文章を作ったりすることは一切ありません。メモを保存し、あとで見つけ出し、正しく書けているか確認するだけです。何を書くか、どうまとめるかといった実際の「考える」部分は、すべてAI側が担当します。

## 基本的な考え方

- **2つのフォルダ、2つの役割** — `raw/` には、あとから変わることのない元の資料(アップロードした文書など)が入ります。`wiki/` はAIが自分でメモを書く場所で、学ぶたびに内容を更新していきます。だから、この「メモ帳」は一度きりの検索結果ではなく、時間とともにどんどん役立つものになっていきます。
- **お互いにリンクし合うメモ** — ページ同士がリンクでつながるので(Wikipediaのリンクのように)、AIは関連するメモをたどっていけます。人気のメモアプリ [Obsidian](https://obsidian.md/) でも同じ仕組みが使えるので、同じメモを自分の目で見て回りたい場合にも便利です。
- **すべてただのテキストファイル** — メモはどれも普通のMarkdownファイルなので、自分で開いて読むこともできます。特別なデータベースは不要です。検索用の小さなインデックスファイルもありますが、これはあくまで補助であり、必要ならメモから何度でも作り直せます。
- **書くのはAI、確認と整理はツールの仕事** — 検索したり、関連するメモを探したり、メモが正しく書けているか確認したりするのは、AIが関わらないシンプルで予測可能な処理です。何を書き残す価値があるか判断し、それをうまく書くのはAIの仕事です。
- **作業中に出てきた好みも自動的に拾う** — 作業のついでにコーディングの流儀や訂正をちらっと口にするだけで、「覚えておいて」「wikiを更新して」と言わなくてもAIがwikiか専用のルールファイルに書き残します。毎回そう言わないと機能しないようでは、良いツールとは言えません。

## インストール

**おすすめ: Claude Codeのプラグインとして入れる** — コマンド2つだけで、他に準備は不要です。

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

これにより、放っておいても物事が正しく動き続けるようにしてくれる、便利な安全装置もいくつか設定されます。詳しくは [docs/ja/hooks.md](docs/ja/hooks.md) を見てください。

コマンドラインツールそのものを直接インストールしたい場合(たとえばClaude Code以外の場所で使いたい場合)は、[docs/ja/installation.md](docs/ja/installation.md) にWindows・macOS・Linux向けの手順があります。両方インストールしても構いません。お互い邪魔し合うことはありません。

## クイックスタート

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init` を実行すると、次のようなフォルダ構成が作られます。

```text
raw/                          # 元の資料 — 絶対に編集しない
wiki/                         # AI自身のメモ。中身は随時更新される
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 裏側の検索インデックス(いつでも作り直せる)
.claude/skills/llm-wiki/      # Claude Codeにこのツールの使い方を教えるファイル
.claude/rules/llm-wiki.md     # 作業前の検索・作業後の更新を自動で促すルール
.claude-plugin/plugin.json    # このプロジェクト用のプラグイン情報(任意)
```

プロジェクトのフォルダをもっとすっきりさせたくて、これらを全部サブフォルダにまとめたいですか? あるいは、すでに自分で作ったwikiを `llmw` に読み込ませたいですか? [docs/ja/project-layout.md](docs/ja/project-layout.md) を見てください。

## AIによる典型的な使い方の流れ

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## コマンド一覧

どのコマンドも `--json` に対応しており、プログラムが読み取れる形式で結果を出力できます。「読む」系のコマンドはたいてい、デフォルトでは短い要約だけを表示します(全部見たいときは `--full`/`--no-brief` を付けてください)。

| コマンド | 何をするか |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | 新しいプロジェクト用に `raw/`、`wiki/`、検索インデックスを用意する(既存プロジェクトの場合は `--adopt` を使う。詳しくは [docs/ja/project-layout.md](docs/ja/project-layout.md)) |
| `llmw status [--brief\|--json]` | 手早い状態チェック: メモの数、リンク切れの有無、最終更新日時 |
| `llmw rebuild` | 検索インデックスを最初から丸ごと作り直す |
| `llmw index [--changed\|--all]` | 検索インデックスを更新する(デフォルトでは変更分だけ) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | 全メモを検索する(検索の仕組みは [docs/ja/commands.md](docs/ja/commands.md) 参照) |
| `llmw read <path\|title\|alias> [--full\|--brief]` | メモを開く。短縮版はタイトル・要約・リンクを表示する |
| `llmw links <target>` | このメモがどこにリンクしているかを表示する |
| `llmw backlinks <target>` | このメモに他のどのメモがリンクしているかを表示する |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 関連しそうなメモを、シンプルなルールに基づいて提案する(AIによる推測は一切なし) |
| `llmw ingest <raw/...>` | 元の資料を、AIが書き込める下書きメモに変換する |
| `llmw write <path> --reason "..." --stdin [--force]` | 新しいメモを作成する |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 既存メモの中の、一致する箇所をひとつ置き換える |
| `llmw patch <path> --reason "..." --stdin` | メモに一連の変更をまとめて適用する(先にバックアップを取り、途中で失敗したら自動的に元に戻す) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | 古いメモを削除せず脇によけて、移動先を示す案内メモを残す |
| `llmw lint [--brief\|--json]` | 問題(リンク切れ、情報の不足、タイトルの重複など)をチェックする。ただし自動修正はしない |
| `llmw health [--brief]` | 裏側の仕組みがきちんと設定されているか確認する |
| `llmw graph build` / `llmw graph export --format json\|html` | メモ同士のつながりを図にして作成・書き出しする |

## 組み込みの安全ルール

- `raw/` にある元の資料は変更できません。ツールが単純に拒否します。
- メモへの変更には必ず短い理由が必要で、その理由は消えない履歴ログに残ります。
- 「削除」はありません。「アーカイブ」だけです。メモを脇によけて、移動先を示す案内を残すので、何かが跡形もなく消えることはありません。
- 一連の変更をまとめて適用するときは、必ず先にバックアップを取り、途中で何か問題が起きたら自動的に元に戻します。
- 簡単なロックファイルの仕組みにより、ツールの2つのコピーが同時に同じメモを編集してぶつかり合うことを防ぎます。

## その他のドキュメント

| ドキュメント | 内容 |
|---|---|
| [docs/ja/installation.md](docs/ja/installation.md) | Windows・macOS・Linux向けの詳しいインストール手順、アップデートや削除の方法 |
| [docs/ja/hooks.md](docs/ja/hooks.md) | Claude Codeプラグインが、AIにwikiを迂回させないようにする仕組みと、ツール自体を自動で最新に保つ仕組み |
| [docs/ja/commands.md](docs/ja/commands.md) | 検索が裏側で実際にどう動いているか |
| [docs/ja/project-layout.md](docs/ja/project-layout.md) | wikiフォルダの整理の仕方いろいろ、すでにあるwikiを取り込む方法、メモアプリObsidianと一緒に使う方法 |
| [docs/ja/development.md](docs/ja/development.md) | `llmw` 自体を開発するための環境構築 |

## ライセンス

MIT — 詳しくは [LICENSE](LICENSE) を参照してください。
