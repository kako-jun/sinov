# Quick Start

## セットアップ（初回のみ）

```bash
# 1. uv で依存関係をインストール
uv sync

# 2. 環境変数ファイルをコピー
cp .env.example .env
cp .env.keys.example .env.keys

# 3. .env を編集
# API_ENDPOINT=http://localhost:8787 (MYPACE APIのURL)
# OLLAMA_HOST=http://localhost:11434 (オプション)
# OLLAMA_MODEL=llama3.2:3b (オプション)

# 4. ボットの鍵を生成
uv run python scripts/generate_keys.py
# → .env.keys に100体分の鍵が生成される

# 5. ボット履歴書を作成（サンプルは既に3体分ある）
# bots/profiles/bot001.yaml, bot002.yaml, bot003.yaml
```

## 実行

```bash
# 1. MYPACE API を起動（別ターミナル）
cd /path/to/mypace/apps/api
pnpm dev
# → http://localhost:8787

# 2. Ollama を起動（使う場合、別ターミナル）
ollama serve
# → http://localhost:11434

# 3. sinov を実行
cd /path/to/sinov
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

# 実行
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
