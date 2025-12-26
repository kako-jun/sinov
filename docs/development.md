# 開発ガイド

## 開発環境のセットアップ

### 必要なもの

- Python 3.11 以上
- uv（パッケージマネージャー）
- Ollama（LLM、必須）
- Git

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd sinov
```

### 2. uv のインストール

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# または pip で
pip install uv
```

### 3. 依存関係のインストール

```bash
uv sync
```

### 4. 環境設定

```bash
cp .env.example .env
cp .env.keys.example .env.keys
```

`.env`を編集：

```bash
# MYPACE APIエンドポイント
API_ENDPOINT=https://api.mypace.llll-ll.com

# Ollama設定（必須）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma2:2b

# 投稿チェック間隔（秒）
CHECK_INTERVAL=60
```

### 5. Ollama のセットアップ（必須）

```bash
# Ollamaのインストール
curl -fsSL https://ollama.com/install.sh | sh

# モデルのダウンロード
ollama pull gemma2:2b
# または他のモデル
ollama pull llama3.2:1b      # より軽量
ollama pull llama3.2:3b      # Meta製、バランス型
ollama pull qwen2.5:3b       # 日本語強め（中国語混入注意）

# Ollamaの起動
ollama serve
```

**モデル選択のポイント:**

- `gemma2:2b` - Google 製、日本語最適（推奨）
- `llama3.2:1b` - 最軽量、低スペックマシンに
- `llama3.2:3b` - Meta 製、バランス型
- `qwen2.5:3b` - 中国 Alibaba 製、日本語強いが中国語混入あり

### 6. NPCの鍵を生成

```bash
uv run python scripts/generate_keys.py
```

これで `.env.keys` に 100人分の鍵が追加されます。

**重要**: このファイルは絶対に git にコミットしないこと！

### 7. 共有ニュースの収集（オプション）

NPCが時事ネタを参照するため、定期的にニュースを収集します：

```bash
# 手動実行
uv run python scripts/collect_news.py

# またはcronで定期実行（4時間ごとなど）
0 */4 * * * cd /path/to/sinov && uv run python scripts/collect_news.py
```

これにより `bots/shared_news.json` に最新ニュースが保存され、全NPCが20%の確率で参照します。

### 8. NPCプロフィールの作成

最低 1 つの履歴書を作成：

```bash
cp bots/profiles/template.yaml bots/profiles/bot001.yaml
```

`bot001.yaml`を編集して ID と名前を変更。

## 開発ワークフロー

### ディレクトリ構造

```
src/
├── main.py                 # メインエントリーポイント
├── cli.py                  # CLIツール
├── config/                 # 設定層
│   └── settings.py         # Pydantic Settings
├── domain/                 # ドメイン層（純粋ビジネスロジック）
│   ├── models.py           # BotProfile, BotState 等
│   ├── scheduler.py        # スケジューリングロジック
│   ├── content.py          # プロンプト生成・コンテンツ戦略
│   └── queue.py            # キューエントリーモデル
├── infrastructure/         # インフラ層（外部システム連携）
│   ├── llm/
│   │   ├── base.py         # LLMProvider 抽象基底クラス
│   │   └── ollama.py       # Ollama 実装
│   ├── nostr/
│   │   └── publisher.py    # Nostr 投稿
│   └── storage/
│       ├── profile_repo.py # YAML プロフィール読み込み
│       ├── state_repo.py   # 状態永続化
│       └── queue_repo.py   # キュー管理
└── application/            # アプリケーション層
    └── bot_service.py      # メインサービス
```

### 型チェック

```bash
uv run mypy src/
```

### リンター

```bash
# チェックのみ
uv run ruff check src/

# 自動修正
uv run ruff check --fix src/

# フォーマット
uv run ruff format src/
```

### CLIコマンド

#### 投稿生成（キューに追加）

```bash
# 全NPCの投稿を生成（pending.json へ）
uv run python -m src.cli generate --all

# 特定NPCの投稿を生成
uv run python -m src.cli generate --bot bot001

# dry-run（dry_run.json へ、レビュー不要）
uv run python -m src.cli generate --all --dry-run
```

#### キュー確認

```bash
# サマリー表示
uv run python -m src.cli queue --summary

# 特定ステータスのリスト
uv run python -m src.cli queue --status pending
uv run python -m src.cli queue --status approved
uv run python -m src.cli queue --status rejected
uv run python -m src.cli queue --status posted
uv run python -m src.cli queue --status dry_run
```

#### レビュー

```bash
# 承認
uv run python -m src.cli review approve <entry_id>
uv run python -m src.cli review approve <entry_id> --note "OK"

# 拒否
uv run python -m src.cli review reject <entry_id>
uv run python -m src.cli review reject <entry_id> --note "修正必要"

# ペンディングリスト表示
uv run python -m src.cli review list
```

#### 投稿

```bash
# 承認済みエントリーを投稿
uv run python -m src.cli post

# 投稿内容の確認（dry-run）
uv run python -m src.cli post --dry-run
```

### 常時稼働モード

```bash
# 通常実行（スケジュールに従って自動投稿）
uv run python -m src.main

# デバッグモード（詳細ログ）
PYTHONUNBUFFERED=1 uv run python -m src.main
```

### 停止

```
Ctrl+C
```

状態は自動的に`bots/states.json`に保存されます。

## デバッグ

### ログの確認

デフォルトのログ出力：

```
Loading bot keys...
Loading bot profiles and states...
✅ Loaded 3 bots
Initializing Nostr clients...
✅ Connected 3 bots to relays
✅ Ollama is available (model: gemma2:2b)

🤖 Starting bot manager (checking every 60s)...
Press Ctrl+C to stop

📝 bot001 posted: TypeScriptで新しいプロジェクト始めた！... (next: 15:23:45)
```

### よくある問題

#### 1. NPCが読み込まれない

**症状:**

```
⚠️  Profile not found for bot001, skipping...
```

**解決:**

- `bots/profiles/bot001.yaml`が存在するか確認
- ファイル名が`bot<name>.yaml`の形式か確認

#### 2. バリデーションエラー

**症状:**

```
ValidationError: emotional_range must be between 0 and 10
```

**解決:**

- YAML ファイルの該当フィールドを修正
- [NPCプロフィール仕様](bot-profile.md)を参照

#### 3. Ollama 接続エラー

**症状:**

```
⚠️  Could not connect to Ollama: Connection refused
```

**解決:**

```bash
# Ollamaを起動
ollama serve

# モデルがダウンロード済みか確認
ollama list
```

#### 4. Nostr 接続エラー

**症状:**

- 投稿が送信されない
- タイムアウト

**解決:**

- リレーが正しく設定されているか確認（`.env`）
- ネットワーク接続を確認
- リレーのステータスを確認: https://nostr.watch/

### 単一NPCでテスト

開発中は 1人だけテストすることを推奨：

```bash
# bots/profiles/ に bot001.yaml だけ置く
rm bots/profiles/bot002.yaml
rm bots/profiles/bot003.yaml

# 投稿を生成してプレビュー
uv run python -m src.cli generate --bot bot001 --dry-run

# 結果を確認
uv run python -m src.cli queue --status dry_run
```

### 投稿頻度を上げてテスト

```yaml
# bot001.yaml
behavior:
  postFrequency: 100 # 1日100回 = 約15分に1回
  postFrequencyVariance: 0.5
  activeHours: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
```

## コードスタイル

### 命名規則

```python
# クラス: PascalCase
class BotService:
    pass

# 関数・変数: snake_case
def calculate_next_post_time():
    bot_id = 1

# 定数: UPPER_SNAKE_CASE
MAX_BOTS = 100

# プライベート: 先頭アンダースコア
def _internal_method():
    pass
```

### 型ヒント

```python
# 必須
def calculate(value: int) -> float:
    return value * 1.5

# Pydantic使用
from pydantic import BaseModel

class Config(BaseModel):
    name: str
    count: int
```

### docstring

```python
def complex_function(param1: str, param2: int) -> bool:
    """
    複雑な処理の説明

    Args:
        param1: パラメータ1の説明
        param2: パラメータ2の説明

    Returns:
        処理結果の説明
    """
    pass
```

## キューワークフロー

投稿は必ずレビュープロセスを経てから本番投稿されます：

```
┌─────────────────────────────────────────────────────────────┐
│                    Queue Workflow                            │
│                                                              │
│   generate           generate --dry-run                      │
│       │                      │                               │
│       ▼                      ▼                               │
│  ┌─────────┐           ┌──────────┐                         │
│  │ pending │           │ dry_run  │                         │
│  └────┬────┘           └──────────┘                         │
│       │                                                      │
│       │ review approve                                       │
│       ├──────────────────┐                                  │
│       │                  │ review reject                     │
│       ▼                  ▼                                   │
│  ┌──────────┐      ┌──────────┐                             │
│  │ approved │      │ rejected │                             │
│  └────┬─────┘      └──────────┘                             │
│       │                                                      │
│       │ post                                                 │
│       ▼                                                      │
│  ┌─────────┐                                                │
│  │ posted  │                                                │
│  └─────────┘                                                │
└─────────────────────────────────────────────────────────────┘
```

### ファイル構造

```
bots/queue/
├── pending.json    # レビュー待ち
├── approved.json   # 承認済み（投稿待ち）
├── rejected.json   # 拒否
├── posted.json     # 投稿済み
└── dry_run.json    # プレビュー用
```

## パフォーマンス測定

### 投稿速度

```python
import time

start = time.time()
await service.run_once()
elapsed = time.time() - start

print(f"Processed all bots in {elapsed:.2f}s")
```

### メモリ使用量

```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.2f} MB")
```

## トラブルシューティング

### nostr-sdk のインストールエラー

**症状:**

```
error: failed to compile `nostr-sdk`
```

**解決:**

- Rust がインストールされているか確認

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### YAML パースエラー

**症状:**

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**解決:**

- YAML の文法を確認
- インデントはスペース 2 個または 4 個で統一
- タブ文字は使わない
- コロン（:）の後にスペースを入れる

### 状態ファイルの破損

**症状:**

```
JSONDecodeError: Expecting value
```

**解決:**

```bash
# 状態ファイルを削除して再生成
rm bots/states.json
uv run python -m src.main
```

## デバッグツール

### IPython

```bash
uv add --dev ipython

# インタラクティブシェルで実行
uv run ipython
>>> from src.application import BotService
>>> from src.config import Settings
```

### Python Debugger (pdb)

```python
# コード内にブレークポイント
import pdb; pdb.set_trace()

# または（Python 3.7+）
breakpoint()
```

## 貢献ガイドライン

### ブランチ戦略

```bash
# 機能追加
git checkout -b feature/add-reply-function

# バグ修正
git checkout -b fix/profile-validation

# ドキュメント
git checkout -b docs/update-readme
```

### コミットメッセージ

```bash
# 良い例
git commit -m "feat: Add reply functionality to bots"
git commit -m "fix: Validate active_hours range in BotProfile"
git commit -m "docs: Update bot-profile.md with examples"

# 悪い例
git commit -m "update"
git commit -m "fixed bug"
```

### プルリクエスト

1. フォークする
2. ブランチを作る
3. 変更をコミット
4. テストを追加
5. プルリクエストを作成

## よく使うコマンド

```bash
# 開発セットアップ
uv sync
cp .env.example .env

# 鍵生成
uv run python scripts/generate_keys.py

# 投稿生成（プレビュー）
uv run python -m src.cli generate --all --dry-run

# キュー確認
uv run python -m src.cli queue --summary

# レビュー
uv run python -m src.cli review list
uv run python -m src.cli review approve <id>

# 投稿
uv run python -m src.cli post

# 常時稼働
uv run python -m src.main

# 型チェック
uv run mypy src/

# リンター
uv run ruff check src/

# フォーマット
uv run ruff format src/

# 状態をリセット
rm bots/states.json

# キューをクリア
rm -rf bots/queue/*.json
```
