# `llmw` への貢献

[English](../en/development.md) · [한국어](../ko/development.md) · **日本語** · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

開発環境を用意するには、[installation.md](installation.md) の「`llmw` そのものの開発に参加する」の部分を見てください。そこまでできたら、`pytest` を実行するとテストが走ります。

## Claude Codeのスキルの仕組み

`llmw init` は、プロジェクトの中の `.claude/skills/llm-wiki/` にいくつかファイルを書き込みます。Claude Codeはこれを自動的に読み込むので、別途インストールする手順は必要ありません。これらのファイルは、AIに「いつ・どうやって `llmw` を使うべきか」を教えるもので、毎回すべての細かい情報を読み込まなくても済むようになっています。

もしすでにマーケットプレイスからClaude Codeのプラグインをインストール済みなら、`llmw init` を実行するときに `--no-claude-plugin` を付けて、このコピーが二重に作られないようにしてください。そうしないと、同じ内容の指示が2つできてしまい、無駄なうえに混乱のもとになります。

## このツールが意図的に(今のところ)やらないこと

設計上、次のことは今のところ対象外としています。AIモデルへの直接接続、ファイルの変更を自動で監視する機能、AIによる意味ベースの検索、PDFやWordファイルを直接読み込む機能、GUIアプリ、そしてメモの自動マージ・自動削除・自動的な矛盾解消です。
