# 開発ガイド

## 開発環境のセットアップ

### 必要なもの

- Python 3.11以上
- Ollama（オプション、推奨）
- Git

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd sinov
```

### 2. Python環境のセットアップ

#### 仮想環境の作成（推奨）

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate  # Windows
```

#### 依存関係のインストール

```bash
# 本番用
pip install nostr-sdk pyyaml python-dotenv httpx ollama pydantic pydantic-settings

# 開発用（追加）
pip install ruff mypy types-pyyaml
```

または

```bash
pip install -e .
```

### 3. 環境設定

```bash
cp .env.example .env
```

`.env`を編集：

```bash
# MYPACE APIエンドポイント（現在は未使用）
API_ENDPOINT=http://localhost:8787

# Nostrリレー
NOSTR_RELAYS=wss://nos.lol,wss://relay.damus.io,wss://relay.nostr.band

# Ollama設定（オプション）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### 4. Ollamaのセットアップ（オプション）

```bash
# Ollamaのインストール
curl -fsSL https://ollama.com/install.sh | sh

# モデルのダウンロード
ollama pull llama3.2:3b
# または他のモデル
ollama pull llama3.2:1b      # より軽量
ollama pull gemma2:2b        # Google製
ollama pull qwen2.5:3b       # 日本語強め

# Ollamaの起動
ollama serve
```

**モデル選択のポイント:**
- `llama3.2:1b` - 最軽量、低スペックマシンに
- `llama3.2:3b` - バランス型（推奨）
- `gemma2:2b` - Google製、品質高め
- `qwen2.5:3b` - 日本語が得意

### 5. ボットの鍵を生成

```bash
python scripts/generate_keys.py
```

これで`bots/keys.json`に100体分の鍵が生成されます。

**重要**: このファイルは絶対にgitにコミットしないこと！

### 6. ボット履歴書の作成

最低1つの履歴書を作成：

```bash
cp bots/profiles/template.yaml bots/profiles/bot001.yaml
```

`bot001.yaml`を編集してIDと名前を変更。

## 開発ワークフロー

### コードの編集

```
src/
├── main.py           # メインエントリーポイント
├── bot_manager.py    # コア機能
├── llm.py            # LLM連携
└── types.py          # 型定義
```

### 型チェック

```bash
mypy src/
```

### リンター

```bash
# チェックのみ
ruff check src/

# 自動修正
ruff check --fix src/

# フォーマット
ruff format src/
```

### 実行

```bash
# 通常実行
python -m src.main

# デバッグモード（詳細ログ）
PYTHONUNBUFFERED=1 python -m src.main
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
✅ Ollama is available (model: llama3.2:3b)

🤖 Starting bot manager (checking every 60s)...
Press Ctrl+C to stop

📝 bot001 posted: TypeScriptで新しいプロジェクト始めた！... (next: 15:23:45)
```

### よくある問題

#### 1. ボットが読み込まれない

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
- YAMLファイルの該当フィールドを修正
- [ボット履歴書仕様](bot-profile.md)を参照

#### 3. Ollama接続エラー

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

#### 4. Nostr接続エラー

**症状:**
- 投稿が送信されない
- タイムアウト

**解決:**
- リレーが正しく設定されているか確認（`.env`）
- ネットワーク接続を確認
- リレーのステータスを確認: https://nostr.watch/

### 単一ボットでテスト

開発中は1体だけテストすることを推奨：

```bash
# bots/profiles/ に bot001.yaml だけ置く
rm bots/profiles/bot002.yaml
rm bots/profiles/bot003.yaml

# 実行
python -m src.main
```

### 投稿頻度を上げてテスト

```yaml
# bot001.yaml
behavior:
  postFrequency: 100        # 1日100回 = 約15分に1回
  postFrequencyVariance: 0.5
  activeHours: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
```

## コードスタイル

### 命名規則

```python
# クラス: PascalCase
class BotManager:
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

## テストの追加

### ユニットテスト

```python
# tests/test_bot_manager.py
import pytest
from src.bot_manager import BotManager
from src.types import BotProfile, Behavior

def test_calculate_next_post_time():
    # テスト実装
    pass

def test_should_post_now():
    # テスト実装
    pass
```

実行：

```bash
pytest tests/
```

### モックの使用

```python
from unittest.mock import Mock, patch

def test_with_mock_llm():
    with patch('src.llm.LLMClient') as mock_llm:
        mock_llm.generate.return_value = "test content"
        # テスト実装
```

## パフォーマンス測定

### 投稿速度

```python
import time

start = time.time()
await manager.run_once()
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

### nostr-sdkのインストールエラー

**症状:**
```
error: failed to compile `nostr-sdk`
```

**解決:**
- Rustがインストールされているか確認
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### YAMLパースエラー

**症状:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**解決:**
- YAMLの文法を確認
- インデントはスペース2個または4個で統一
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
python -m src.main
```

## デバッグツール

### IPython

```bash
pip install ipython

# インタラクティブシェルで実行
ipython
>>> from src.bot_manager import BotManager
>>> manager = BotManager(...)
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
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env

# 鍵生成
python scripts/generate_keys.py

# 実行
python -m src.main

# 型チェック
mypy src/

# リンター
ruff check src/

# フォーマット
ruff format src/

# 状態をリセット
rm bots/states.json

# 全クリーン（鍵も削除）
rm bots/keys.json bots/states.json
```
