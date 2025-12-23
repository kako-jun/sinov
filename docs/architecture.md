# アーキテクチャ設計

## システム概要

```
┌─────────────────────────────────────────────────────────────┐
│                     Sinov Bot Manager                        │
│                    (Single Python Process)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Bot Manager                           │ │
│  │                                                        │ │
│  │  - 100 Bot Profiles (YAML)                            │ │
│  │  - 100 Bot States (JSON)                              │ │
│  │  - 100 Nostr Keys                                     │ │
│  │  - Scheduler (60s loop)                               │ │
│  └────┬───────────────────────────────────────────────┬───┘ │
│       │                                               │     │
│       ▼                                               ▼     │
│  ┌─────────────┐                              ┌──────────┐  │
│  │ LLM Client  │                              │  Nostr   │  │
│  │  (Ollama)   │                              │ Clients  │  │
│  └─────────────┘                              │  (100)   │  │
│                                               └──────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                           │
         ▼                                           ▼
┌─────────────────┐                    ┌──────────────────────┐
│ Ollama Server   │                    │   Nostr Relays       │
│ (localhost:     │                    │  - wss://nos.lol     │
│  11434)         │                    │  - wss://relay.      │
│                 │                    │    damus.io          │
│ Model:          │                    │  - wss://relay.      │
│  llama3.2:3b    │                    │    nostr.band        │
└─────────────────┘                    └──────────────────────┘
```

## コンポーネント

### 1. Bot Manager (`src/bot_manager.py`)

**責務:**
- ボットの鍵・プロフィール・状態の管理
- Nostrクライアントの初期化と管理
- スケジューリング（どのボットがいつ投稿するか）
- 投稿内容の生成
- 投稿の実行
- 状態の永続化

**主要メソッド:**

```python
class BotManager:
    async def load_bots() -> None
        # 鍵・プロフィール・状態を読み込み
    
    async def initialize_clients() -> None
        # 100個のNostrクライアントを作成・接続
    
    def should_post_now(bot_id: int) -> bool
        # このボットが今投稿すべきか判定
    
    def _calculate_next_post_time(bot_id: int) -> int
        # 次回投稿時刻をランダムに計算
    
    async def generate_post_content(bot_id: int) -> str
        # LLMまたはテンプレートで投稿内容生成
    
    async def post(bot_id: int, content: str) -> None
        # Nostrに投稿
    
    async def run_once() -> None
        # 全ボットをチェックして必要なら投稿
    
    async def run_forever(check_interval: int) -> None
        # メインループ
```

### 2. LLM Client (`src/llm.py`)

**責務:**
- Ollamaとの通信
- プロンプトから投稿文の生成
- エラーハンドリング（LLM利用不可時のフォールバック）

**主要メソッド:**

```python
class LLMClient:
    async def generate(prompt: str, max_length: int) -> str
        # プロンプトから文章生成
    
    def is_available() -> bool
        # Ollamaが利用可能かチェック
```

### 3. Type Definitions (`src/types.py`)

**責務:**
- 全データ構造の型定義
- Pydanticによるバリデーション
- YAMLとJSONのシリアライズ

**モデル:**

```python
BotKey          # 鍵情報（id, name, pubkey, nsec）
BotProfile      # 履歴書（性格、興味、行動、社交性、背景）
  ├─ Personality
  ├─ Interests
  ├─ Behavior
  ├─ Social
  └─ Background
BotState        # 実行時状態（投稿時刻、カウント）
```

### 4. Main Entry Point (`src/main.py`)

**責務:**
- 環境変数の読み込み
- Bot Managerの初期化
- メインループの開始

## データフロー

### 起動時（初期化）

```
1. .env 読み込み
   ↓
2. bots/keys.json 読み込み
   ├─ Pydanticでバリデーション → BotKey[]
   ↓
3. bots/profiles/*.yaml 読み込み
   ├─ Pydanticでバリデーション → BotProfile[]
   ↓
4. bots/states.json 読み込み（存在すれば）
   ├─ Pydanticでバリデーション → BotState[]
   └─ 存在しない → 初期値で作成
   ↓
5. 各ボットのNostrクライアント作成
   ├─ Keys.parse(nsec)
   ├─ Client(keys)
   ├─ add_relay() × N
   └─ connect()
   ↓
6. Ollama接続テスト（オプション）
   ├─ 成功 → LLMClient作成
   └─ 失敗 → None（テンプレート生成）
```

### メインループ（60秒ごと）

```
1. run_once()
   ↓
2. for each bot:
   ├─ should_post_now(bot_id)?
   │  ├─ 活動時間帯チェック
   │  └─ next_post_time <= 現在時刻?
   ↓
3. 投稿すべきボットが見つかる
   ↓
4. generate_post_content(bot_id)
   ├─ LLMあり:
   │  ├─ _create_prompt() → プロンプト生成
   │  └─ llm_client.generate() → 文章生成
   └─ LLMなし:
      └─ _generate_simple_content() → テンプレート選択
   ↓
5. post(bot_id, content)
   ├─ Tag作成（#mypace, client:sinov）
   ├─ EventBuilder(kind:1, content, tags)
   ├─ client.send_event_builder()
   ├─ state更新:
   │  ├─ last_post_time = now
   │  ├─ next_post_time = _calculate_next_post_time()
   │  └─ total_posts += 1
   └─ ログ出力
   ↓
6. _save_states()
   └─ bots/states.json に保存
   ↓
7. sleep(60)
```

### 投稿時刻の計算

```python
# 1日の投稿頻度から平均間隔を計算
avg_interval = 86400 / post_frequency  # 秒

# ばらつきを考慮したランダム間隔
variance = post_frequency_variance  # 0.0 ~ 1.0
actual_interval = avg_interval * random.uniform(1 - variance, 1 + variance)

# 次回投稿時刻
next_time = current_time + int(actual_interval)
```

**例:**
- `post_frequency = 5` → 平均4.8時間間隔
- `post_frequency_variance = 0.3` → ±30%のばらつき
- 実際の間隔: 3.36時間 ~ 6.24時間

## 並行処理

### 現在の実装（シングルスレッド）

```python
async def run_forever():
    while True:
        await run_once()  # 全ボットを順番にチェック
        await asyncio.sleep(60)
```

- 1つのイベントループで全ボット管理
- Nostr送信は非同期（`await client.send_event_builder()`）
- LLM生成も非同期（`await llm_client.generate()`）

### 将来の拡張（並列化）

投稿数が増えた場合、複数ボットを並列処理可能：

```python
async def run_once():
    tasks = []
    for bot_id in self.bots.keys():
        if self.should_post_now(bot_id):
            task = self.process_bot(bot_id)
            tasks.append(task)
    
    await asyncio.gather(*tasks)
```

## エラーハンドリング

### レベル1: 起動時バリデーション

```python
# YAML読み込み時
try:
    profile = BotProfile.model_validate(data)
except ValidationError as e:
    print(f"Invalid profile: {e}")
    continue  # このボットはスキップ
```

### レベル2: 投稿時エラー

```python
async def run_once():
    for bot_id in self.bots.keys():
        try:
            if self.should_post_now(bot_id):
                content = await self.generate_post_content(bot_id)
                await self.post(bot_id, content)
        except Exception as e:
            print(f"Error for {bot_id}: {e}")
            # 他のボットは継続
```

### レベル3: LLMフォールバック

```python
if self.llm_client:
    try:
        content = await self.llm_client.generate(prompt)
    except Exception:
        content = self._generate_simple_content(profile)
else:
    content = self._generate_simple_content(profile)
```

## 状態管理

### ステートフルなデータ

**メモリ内:**
- `self.bots: dict[int, tuple[BotKey, BotProfile, BotState]]`
- `self.clients: dict[int, Client]`

**永続化:**
- `bots/states.json` - 60秒ごと & 終了時に保存

### ステートレスなデータ

**起動時のみ読み込み:**
- `bots/keys.json` - 鍵は変更されない
- `bots/profiles/*.yaml` - 履歴書は変更されない（手動編集後は再起動）

### 状態の復元

```python
# 前回の実行状態を復元
if states_file.exists():
    state = BotState.model_validate(state_dict)
else:
    # 新規作成
    state = BotState(
        id=bot_id,
        last_post_time=0,
        next_post_time=0,  # 初回は即座に投稿
        total_posts=0,
    )
```

## セキュリティ考慮

### 秘密鍵の保護

- `bots/keys.json`は`.gitignore`に追加
- ファイルパーミッションは`600`推奨
- 秘密鍵は外部に送信しない（Nostr署名はローカル）

### Nostr署名

```python
keys = Keys.parse(nsec)  # nostr-sdk内部で秘密鍵を管理
client = Client(keys)    # クライアントに紐付け
event_builder = EventBuilder(kind, content, tags)
await client.send_event_builder(event_builder)  # 内部で署名して送信
```

### LLMプロンプト

- ボットの履歴書情報のみ送信
- ユーザー入力は含まれない（自律型）
- プロンプトインジェクションのリスクは低い

## スケーラビリティ

### 現在のスペック

- ボット数: 100体
- 平均投稿頻度: 5回/日/ボット → 500投稿/日
- チェック間隔: 60秒
- メモリ使用量: ~100MB（100クライアント + 状態）

### ボトルネック

1. **Nostr接続数**: 100個のWebSocket接続
2. **LLM生成速度**: 1投稿あたり数秒
3. **メモリ**: 各クライアントがリレー接続を保持

### スケーリング戦略

**ボット数を増やす（1000体など）:**
- 複数プロセスに分割（bot001-300, bot301-600...）
- 各プロセスは独立して動作
- 状態ファイルも分割

**投稿頻度を上げる:**
- 並列投稿（`asyncio.gather()`）
- LLMのバッチ生成

**リレー分散:**
- ボットごとに異なるリレーセット
- ロードバランシング

## モニタリング

### ログ出力

```
Loading bot keys...
Loading bot profiles and states...
✅ Loaded 100 bots
Initializing Nostr clients...
✅ Connected 100 bots to relays
✅ Ollama is available (model: llama3.2:3b)

🤖 Starting bot manager (checking every 60s)...
Press Ctrl+C to stop

📝 bot001 posted: TypeScriptで新しいプロジェクト始めた！... (next: 15:23:45)
📝 bot042 posted: アルゴリズムの勉強中... (next: 18:07:12)
```

### 将来の拡張

- [ ] 構造化ログ（JSON）
- [ ] メトリクス収集（投稿数、成功率）
- [ ] Prometheusエクスポーター
- [ ] ダッシュボード（Grafana）

## テスト戦略

### ユニットテスト

```python
# 次回投稿時刻の計算
def test_calculate_next_post_time():
    manager = BotManager(...)
    next_time = manager._calculate_next_post_time(bot_id=1)
    assert next_time > time.time()

# プロンプト生成
def test_create_prompt():
    manager = BotManager(...)
    prompt = manager._create_prompt(profile)
    assert "陽気" in prompt
    assert "TypeScript" in prompt
```

### 統合テスト

```python
# ボット読み込み
async def test_load_bots():
    manager = BotManager(...)
    await manager.load_bots()
    assert len(manager.bots) == 100

# Nostr投稿（テストリレー）
async def test_post():
    manager = BotManager(test_relays=[...])
    await manager.initialize_clients()
    await manager.post(bot_id=1, content="test")
```

### E2Eテスト

- テスト用の履歴書（1体のみ）
- テスト用リレー
- 実際に起動して投稿を確認
