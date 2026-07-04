# 開発

[English](../en/development.md) · [한국어](../ko/development.md) · **日本語** · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

dev 環境をセットアップするため [installation.md](installation.md) の「ローカルクローン、編集可能インストール」セクションを参照してください。そこから `pytest` がテストスイートを実行します。

## Claude Code スキル

`llmw init` はプロジェクト内に `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}` を書き込みます。Claude Code はこれをプレーンスキルとして自動検出 — インストール ステップなし。それはエージェントにいつ `llmw` に手を伸ばすか、コア検索最初のワークフロー、そして `reference.md`/`examples.md` に完全な詳細を指しているため常にロードされた `SKILL.md` は短く保たれます。

llm-wiki Claude Code プラグインがマーケットプレイスからまずインストール済みの場合、このプロジェクトローカルコピーをスキップするために `--no-claude-plugin` を渡す — さもなければプロジェクト同じスキルの 2 コピーで終わり（マーケットプレイスプラグインのこれ）、冗長で Claude Code が両方ロードするときに混乱できます。

## MVP スコープ

意図的に除外：MCP サーバー、デーモン/ウォッチモード、埋め込み/ベクトル検索、ダイレクト PDF/DOCX パース、Obsidian プラグイン、ウェブ UI、自動マージ/自動削除/矛盾検出ロジック。
