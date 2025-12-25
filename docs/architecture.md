# アーキテクチャ設計

## システム概要

```
┌─────────────────────────────────────────────────────────────────┐
│                      Sinov Bot System                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CLI (src/cli.py)                       │   │
│  │   generate | queue | review | post                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Application Layer                            │   │
│  │                BotService                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────┬─────────────┬─────────────┬────────────────┐   │
│  │   Domain    │   Domain    │   Domain    │    Domain      │   │
│  │   Models    │  Scheduler  │  Content    │    Queue       │   │
│  └─────────────┴─────────────┴─────────────┴────────────────┘   │
│                              │                                   │
│  ┌─────────────┬─────────────┬─────────────┬────────────────┐   │
│  │     LLM     │    Nostr    │   Profile   │    State       │   │
│  │  Provider   │  Publisher  │    Repo     │    Repo        │   │
│  └─────────────┴─────────────┴─────────────┴────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│  Ollama Server  │  │  MYPACE API  │  │  Local Files    │
│  (localhost:    │  │              │  │  - profiles/    │
│   11434)        │  │  → Nostr     │  │  - states.json  │
└─────────────────┘  │    Relays    │  │  - queue/       │
                     └──────────────┘  └─────────────────┘
```

## レイヤード アーキテクチャ

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

## コンポーネント

### 1. Config Layer (`src/config/`)

**責務:**

- 環境変数からの設定読み込み
- Pydantic Settings による型安全な設定管理
- デフォルト値の提供

**主要クラス:**

```python
class Settings(BaseSettings):
    profiles_dir: Path
    states_file: Path
    api_endpoint: str
    dry_run: bool
    ollama_host: str
    ollama_model: str
    check_interval: int
    content: ContentSettings
    topic_pool: list[str]

class ContentSettings(BaseSettings):
    context_continuation_probability: float  # 0.7
    news_reference_probability: float        # 0.2
    evolution_interval: int                  # 10
    llm_retry_count: int                     # 3
    history_check_count: int                 # 5
    max_history_size: int                    # 20
```

### 2. Domain Layer (`src/domain/`)

**責務:**

- ビジネスロジックの実装
- 外部依存なしの純粋な処理
- 型定義とバリデーション

**主要クラス:**

```python
# models.py
BotKey          # 鍵情報（id, name, pubkey, nsec）
BotProfile      # 履歴書（性格、興味、行動、社交性、背景）
  ├─ Personality
  ├─ Interests
  ├─ Behavior
  ├─ Social
  └─ Background
BotState        # 実行時状態

# scheduler.py
class Scheduler:
    @staticmethod
    def should_post_now(profile, state) -> bool
    @staticmethod
    def calculate_next_post_time(profile) -> int

# content.py
class ContentStrategy:
    def create_prompt(profile, state, shared_news) -> str
    def clean_content(content) -> str
    def validate_content(content) -> bool
    def adjust_length(content, min, max) -> str

# queue.py
class QueueStatus(Enum):
    PENDING, APPROVED, REJECTED, POSTED, DRY_RUN

class QueueEntry(BaseModel):
    id, bot_id, bot_name, content, created_at, status, ...
```

### 3. Infrastructure Layer (`src/infrastructure/`)

**責務:**

- 外部システムとの連携
- 副作用を持つ処理
- 抽象化によるテスタビリティ確保

**主要クラス:**

```python
# llm/base.py
class LLMProvider(ABC):
    async def generate(prompt, max_length) -> str
    def is_available() -> bool

# llm/ollama.py
class OllamaProvider(LLMProvider):
    # Ollama 実装

# nostr/publisher.py
class NostrPublisher:
    async def publish(keys, content, bot_name) -> str | None

# storage/profile_repo.py
class ProfileRepository:
    def load_all() -> list[BotProfile]
    def load(profile_file) -> BotProfile

# storage/state_repo.py
class StateRepository:
    def load_all() -> dict[int, BotState]
    def save_all(states) -> None

# storage/queue_repo.py
class QueueRepository:
    def add(entry) -> None
    def get_all(status) -> list[QueueEntry]
    def approve(entry_id, note) -> QueueEntry | None
    def reject(entry_id, note) -> QueueEntry | None
    def mark_posted(entry_id, event_id) -> QueueEntry | None
```

### 4. Application Layer (`src/application/`)

**責務:**

- ユースケースの実装
- 依存関係の調整
- ワークフローの制御

**主要クラス:**

```python
class BotService:
    async def load_bots() -> None
    async def initialize_keys() -> None
    async def generate_post_content(bot_id) -> str
    async def post(bot_id, content) -> None
    async def run_once() -> None
    async def run_forever() -> None
```

### 5. CLI (`src/cli.py`)

**責務:**

- ユーザーインターフェース
- コマンドライン引数の解析
- サービス層の呼び出し

**コマンド:**

```bash
# 投稿生成
uv run python -m src.cli generate --all
uv run python -m src.cli generate --bot bot001
uv run python -m src.cli generate --all --dry-run

# キュー確認
uv run python -m src.cli queue --summary
uv run python -m src.cli queue --status pending

# レビュー
uv run python -m src.cli review approve <id>
uv run python -m src.cli review reject <id>

# 投稿
uv run python -m src.cli post
```

## データフロー

### 投稿キューシステム

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
bots/
├── profiles/           # ボット履歴書（YAML）
│   ├── bot001.yaml
│   └── ...
├── states.json         # 実行時状態
└── queue/              # 投稿キュー
    ├── pending.json    # レビュー待ち
    ├── approved.json   # 承認済み
    ├── rejected.json   # 拒否
    ├── posted.json     # 投稿済み
    └── dry_run.json    # プレビュー
```

## 依存性注入

```python
# main.py
async def main():
    settings = Settings()

    # 依存関係の構築
    llm_provider = OllamaProvider(settings.ollama_host, settings.ollama_model)
    publisher = NostrPublisher(settings.api_endpoint, settings.dry_run)
    profile_repo = ProfileRepository(settings.profiles_dir)
    state_repo = StateRepository(settings.states_file)

    # サービスに注入
    service = BotService(
        settings=settings,
        llm_provider=llm_provider,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
    )
```

## 拡張ポイント

### LLM プロバイダーの追加

```python
# infrastructure/llm/openai.py
class OpenAIProvider(LLMProvider):
    async def generate(self, prompt: str, max_length: int | None = None) -> str:
        # OpenAI API 実装
        ...

    def is_available(self) -> bool:
        ...
```

### 新しいコマンドの追加

```python
# cli.py
def main():
    # 新しいサブコマンド
    new_parser = subparsers.add_parser("new-command", help="...")
    new_parser.add_argument(...)
```

## セキュリティ

### 秘密鍵の保護

- `.env.keys` に nsec を保存
- `.gitignore` で除外
- `BotKey.from_env()` で環境変数から読み込み

### 投稿フロー

- 生成 → レビュー → 投稿の段階的プロセス
- レビューなしの直接投稿は不可
- dry-run で事前確認可能
