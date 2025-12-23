# Sinov - MYPACE SNS Bot Management System

## プロジェクト概要

SinovはMYPACE SNS用の100体のボット管理システムです。各ボットが独自の性格、興味、行動パターンを持ち、自律的に投稿を行います。

## 主要な特徴

1. **100体のボット管理**: 各ボットに固有のNostr鍵ペア（nsec）
2. **YAML形式の履歴書**: 性格、興味、行動パターンを人間が編集可能
3. **ローカルLLM統合**: Ollamaで自然な投稿文を生成（オプション）
4. **常時稼働**: 1つのPythonプロセスで全ボット管理
5. **型安全**: Pydanticで完全な型チェックとバリデーション

## 技術スタック

- **言語**: Python 3.11+
- **Nostrライブラリ**: nostr-sdk (Rust製、Python bindings)
- **LLM**: Ollama (ローカルLLM、オプション)
- **型チェック**: Pydantic 2.x
- **設定管理**: YAML + JSON
- **プロトコル**: Nostr (分散型SNS)

## ディレクトリ構造

```
sinov/
├── src/
│   ├── main.py           # メインエントリーポイント
│   ├── bot_manager.py    # ボット管理・スケジューリング
│   ├── llm.py            # Ollama LLMクライアント
│   └── types.py          # Pydantic型定義
├── scripts/
│   └── generate_keys.py  # 100体の鍵生成
├── bots/
│   ├── keys.json         # ボットの秘密鍵（gitignore）
│   ├── states.json       # 実行時状態（gitignore）
│   └── profiles/         # YAML履歴書
│       ├── template.yaml
│       ├── bot001.yaml
│       └── ...
├── docs/                 # ドキュメント
└── pyproject.toml
```

## コアコンセプト

### 1. ボットの個性

各ボットはYAML形式の「履歴書」で定義されます：

- **性格**: 陽気、真面目、のんびりなど
- **興味**: 技術トピック、キーワード、プログラミング言語
- **行動パターン**: 投稿頻度、活動時間帯、文章の長さ
- **社交性**: 仲良しボット、返信/リポスト/いいねの確率（将来実装）
- **背景**: 職業、経験、趣味、好きな言葉

### 2. スケジューリング

- 各ボットは個別に**次回投稿時刻**を持つ
- 投稿頻度設定と「ばらつき」から次回投稿時刻をランダムに計算
- 1分ごとに全ボットをチェックし、投稿時刻が来たボットだけ投稿
- **5分の倍数に固まらない**ランダムスケジューリング

### 3. 投稿生成

**LLMあり（推奨）:**
- ボットの性格・興味に基づいたプロンプト生成
- Ollama経由でローカルLLM（llama3.2など）に投稿文生成を依頼
- 自然で多様な文章

**LLMなし:**
- シンプルなテンプレートベース
- キーワードや好きな言葉からランダム選択
- コードブロックも含められる

### 4. Nostr投稿

- クライアント側で署名（秘密鍵はローカルのみ）
- `#mypace`タグで投稿
- 複数リレー（nos.lol、relay.damus.io等）に同時配信

## 型安全性

Pydanticを使用した厳密な型チェック：

```python
class BotProfile(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    personality: Personality
    interests: Interests
    behavior: Behavior
    # ... バリデーションルール付き
```

- YAML読み込み時に型チェック
- 不正な設定は起動時にエラー
- フィールド間の整合性検証（例：post_length_max > post_length_min）

## 実行フロー

1. **起動**: `python -m src.main`
2. **初期化**:
   - `bots/keys.json`から鍵読み込み
   - `bots/profiles/*.yaml`から履歴書読み込み（Pydanticバリデーション）
   - `bots/states.json`から前回の状態復元（なければ初期化）
   - Nostrクライアント初期化（全リレーに接続）
3. **メインループ**（60秒ごと）:
   - 全ボットをチェック
   - 活動時間帯 & 次回投稿時刻に達したボットを抽出
   - LLMで投稿内容生成
   - Nostrに投稿
   - 次回投稿時刻を計算・更新
   - 状態を保存
4. **停止**: Ctrl+C で状態を保存して終了

## 設定ファイル

### .env
```bash
API_ENDPOINT=http://localhost:8787
NOSTR_RELAYS=wss://nos.lol,wss://relay.damus.io
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### bots/keys.json（自動生成）
```json
[
  {
    "id": 1,
    "name": "bot001",
    "pubkey": "abc123...",
    "nsec": "nsec1..."
  }
]
```

### bots/states.json（自動生成・更新）
```json
[
  {
    "id": 1,
    "last_post_time": 1703318400,
    "next_post_time": 1703325600,
    "total_posts": 42,
    "last_post_content": "..."
  }
]
```

## セキュリティ

- **秘密鍵はローカルのみ**: `bots/keys.json`は`.gitignore`
- **署名はクライアント側**: サーバーに秘密鍵を送信しない
- **Nostrプロトコル**: 分散型で単一障害点なし

## 拡張性

現在は投稿のみ実装。今後の拡張：

- [ ] ボット同士の交流（返信、リポスト、いいね）
- [ ] Nostrプロフィール設定（アイコン、自己紹介）
- [ ] Web UIでの履歴書編集
- [ ] 統計情報・ダッシュボード
- [ ] 投稿内容の多様化（画像、リンク埋め込み）
- [ ] 会話の文脈を考慮した返信生成

## 開発時の注意点

1. **型チェック**: Pydanticのバリデーションエラーを見逃さない
2. **YAML編集**: `active_hours`は0-23、`post_frequency_variance`は0-1など
3. **LLM**: Ollamaなしでも動作するが、投稿内容は単調
4. **リレー接続**: 初回接続時は少し時間がかかる
5. **状態保存**: Ctrl+Cで停止すると状態が保存される

## 詳細ドキュメント

- [アーキテクチャ設計](docs/architecture.md)
- [ボット履歴書仕様](docs/bot-profile.md)
- [開発ガイド](docs/development.md)
- [実行・デプロイ](docs/deployment.md)
