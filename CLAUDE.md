# Sinov - MYPACE SNS Bot Management System

## プロジェクト概要

Sinov は MYPACE SNS 用の 100 体のボット管理システムです。各ボットが独自の性格、興味、行動パターンを持ち、自律的に投稿を行います。

### 「100人の村」コンセプト

このプロジェクトは、100体のボットが一つの「村」を形成し、互いに影響し合う生態系を目指します：

- **自律性**: 各ボットは独立して行動し、中央集権的な制御はない
- **相互作用**: 共有ニュースを参照し、同じ話題で盛り上がる
- **成長**: 時間とともに興味が広がり、個性が変化する
- **創発**: 人間が予想しない偶然の相互作用が生まれる
- **文脈**: 前回の投稿を記憶し、続きを書く（会話の流れ）

## 主要な特徴

1. **100 体のボット管理**: 各ボットに固有の Nostr 鍵ペア（nsec）
2. **YAML 形式の履歴書**: 性格、興味、行動パターンを人間が編集可能
3. **ローカル LLM 統合**: Ollama で自然な投稿文を生成（**必須**）
4. **常時稼働**: 1 つの Python プロセスで全ボット管理
5. **型安全**: Pydantic で完全な型チェックとバリデーション
6. **Dry run モード**: 本番環境に投稿せずテスト可能
7. **文脈継続**: 前回投稿を記憶し、続きを書く（70%）
8. **共有ニュース**: 全員が時事ネタを参照（20%）
9. **成長要素**: 10投稿ごとに新しい興味を発見

## 技術スタック

- **言語**: Python 3.11+
- **Nostr ライブラリ**: nostr-sdk (Rust 製、Python bindings)
- **LLM**: Ollama (gemma2:2b - Google 製、日本語最適)
- **型チェック**: Pydantic 2.x
- **設定管理**: YAML + JSON
- **プロトコル**: Nostr (分散型 SNS)

## ディレクトリ構造

```
sinov/
├── src/
│   ├── main.py           # メインエントリーポイント
│   ├── bot_manager.py    # ボット管理・スケジューリング
│   ├── llm.py            # Ollama LLMクライアント
│   └── types.py          # Pydantic型定義
├── scripts/
│   ├── generate_keys.py  # 100体の鍵生成
│   └── collect_news.py   # ニュース収集（定期実行）
├── bots/
│   ├── keys.json         # ボットの秘密鍵（gitignore）
│   ├── states.json       # 実行時状態（gitignore）
│   ├── shared_news.json  # 共有ニュース（gitignore）
│   └── profiles/         # YAML履歴書
│       ├── template.yaml
│       ├── bot001.yaml
│       └── ...
├── docs/                 # ドキュメント
└── pyproject.toml
```

## コアコンセプト

### 1. ボットの個性

各ボットは YAML 形式の「履歴書」で定義されます：

- **性格**: 陽気、真面目、のんびりなど
- **興味**: 技術トピック、キーワード、プログラミング言語
- **行動パターン**: 投稿頻度、活動時間帯、文章の長さ
- **社交性**: 仲良しボット、返信/リポスト/いいねの確率（将来実装）
- **背景**: 職業、経験、趣味、好きな言葉

### 2. スケジューリング

- 各ボットは個別に**次回投稿時刻**を持つ
- 投稿頻度設定と「ばらつき」から次回投稿時刻をランダムに計算
- 1 分ごとに全ボットをチェックし、投稿時刻が来たボットだけ投稿
- **5 分の倍数に固まらない**ランダムスケジューリング

### 3. 投稿生成

**LLM による生成（必須）:**

- ボットの性格・興味に基づいたプロンプト生成
- Ollama 経由でローカル LLM（gemma2:2b）に投稿文生成を依頼
- 自然で多様な日本語の文章
- **文脈継続**: 70%の確率で前回投稿の続きを書く
- **共有ニュース**: 20%の確率で時事ネタを参照
- **過去投稿履歴**: 最新20件を保持し、重複を防止
- **成長要素**: 10投稿ごとに新しいトピックに興味
- **プロンプト最適化**: 短文・カジュアルな投稿を重視
- マークダウン記号（`###`, ` ``` `）や説明文の排除

### 4. Nostr 投稿

- クライアント側で署名（秘密鍵はローカルのみ）
- `#mypace`タグで投稿
- 複数リレー（nos.lol、relay.damus.io 等）に同時配信

## 型安全性

Pydantic を使用した厳密な型チェック：

```python
class BotProfile(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    personality: Personality
    interests: Interests
    behavior: Behavior
    # ... バリデーションルール付き
```

- YAML 読み込み時に型チェック
- 不正な設定は起動時にエラー
- フィールド間の整合性検証（例：post_length_max > post_length_min）

## 実行フロー

1. **起動**: `python -m src.main`
2. **初期化**:
   - `bots/keys.json`から鍵読み込み
   - `bots/profiles/*.yaml`から履歴書読み込み（Pydantic バリデーション）
   - `bots/states.json`から前回の状態復元（なければ初期化）
   - Nostr クライアント初期化（全リレーに接続）
3. **メインループ**（60 秒ごと）:
   - 全ボットをチェック
   - 活動時間帯 & 次回投稿時刻に達したボットを抽出
   - LLM で投稿内容生成
   - Nostr に投稿
   - 次回投稿時刻を計算・更新
   - 状態を保存
4. **停止**: Ctrl+C で状態を保存して終了

## 設定ファイル

### .env

```bash
API_ENDPOINT=https://api.mypace.llll-ll.com
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma2:2b
DRY_RUN=false  # true: 本番投稿しない、false: 本番投稿する
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
    "last_post_content": "...",
    "last_event_id": "abc123..."  # 投稿削除用のイベントID
  }
]
```

## セキュリティ

- **秘密鍵はローカルのみ**: `bots/keys.json`は`.gitignore`
- **署名はクライアント側**: サーバーに秘密鍵を送信しない
- **Nostr プロトコル**: 分散型で単一障害点なし

## 拡張性

現在は投稿のみ実装。今後の拡張：

- [ ] ボット同士の交流（返信、リポスト、いいね）
- [ ] Nostr プロフィール設定（アイコン、自己紹介）
- [ ] Web UI での履歴書編集
- [ ] 統計情報・ダッシュボード
- [ ] 投稿内容の多様化（画像、リンク埋め込み）
- [ ] 会話の文脈を考慮した返信生成

## 開発時の注意点

1. **型チェック**: Pydantic のバリデーションエラーを見逃さない
2. **YAML 編集**: `active_hours`は 0-23、`post_frequency_variance`は 0-1 など
3. **LLM**: Ollama なしでも動作するが、投稿内容は単調
4. **リレー接続**: 初回接続時は少し時間がかかる
5. **状態保存**: Ctrl+C で停止すると状態が保存される

## 詳細ドキュメント

- [アーキテクチャ設計](docs/architecture.md)
- [ボット履歴書仕様](docs/bot-profile.md)
- [開発ガイド](docs/development.md)
- [実行・デプロイ](docs/deployment.md)
