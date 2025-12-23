# Quick Start

## セットアップ（初回のみ）

```bash
# 1. uv で依存関係をインストール
uv sync

# 2. 環境変数ファイルをコピー
cp .env.example .env
cp .env.keys.example .env.keys

# 3. .env を編集
# API_ENDPOINT=https://api.mypace.llll-ll.com (MYPACE APIのURL)
# OLLAMA_HOST=http://localhost:11434 (必須)
# OLLAMA_MODEL=gemma2:2b (必須 - Google製、日本語最適)
# DRY_RUN=true (テスト時はtrue、本番投稿時はfalse)

# 4. ボットの鍵を生成
uv run python scripts/generate_keys.py
# → .env.keys に100体分の鍵が生成される

# 5. ボット履歴書を作成（サンプルは既に3体分ある）
# bots/profiles/bot001.yaml, bot002.yaml, bot003.yaml
```

## 実行

```bash
# 1. Ollama を起動（必須）
ollama serve
# → http://localhost:11434
# 別ターミナルで:
ollama pull gemma2:2b

# 2. Dry run モードでテスト実行
cd /path/to/sinov
# .envでDRY_RUN=trueに設定
uv run python -m src.main
# → 本番投稿せず、LLMで生成した文章をログに出力

# 3. 本番投稿
# .envでDRY_RUN=falseに設定
uv run python -m src.main
```

## 停止

```
Ctrl+C
```

状態は自動的に `bots/states.json` に保存されます。

## ファイル構造

```
sinov/
├── src/                      # ソースコード
│   ├── main.py              # エントリーポイント
│   ├── bot_manager.py       # ボット管理
│   ├── llm.py               # LLM連携
│   └── types.py             # 型定義
├── scripts/
│   └── generate_keys.py     # 鍵生成スクリプト
├── bots/
│   ├── profiles/            # ボット履歴書（YAML）
│   │   ├── template.yaml
│   │   ├── bot001.yaml
│   │   └── ...
│   └── states.json          # 実行状態（自動生成）
├── docs/                    # ドキュメント
├── .env                     # 環境設定（gitignore）
├── .env.keys                # ボット秘密鍵（gitignore）
└── pyproject.toml           # 依存関係
```

## 主要コマンド

```bash
# 鍵生成
uv run python scripts/generate_keys.py

# Ollama起動（必須）
ollama serve
ollama pull gemma2:2b

# テスト実行（Dry runモード）
# .envでDRY_RUN=trueに設定してから:
uv run python -m src.main

# 本番実行
# .envでDRY_RUN=falseに設定してから:
uv run python -m src.main

# 型チェック
uv run mypy src/

# リンター
uv run ruff check src/

# フォーマット
uv run ruff format src/

# 状態をリセット
rm bots/states.json
```
