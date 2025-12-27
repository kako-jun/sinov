# アーキテクチャ

## レイヤー構造

```
src/
├── cli/                 # CLI層
│   ├── main.py          # エントリーポイント
│   └── commands/        # 各コマンド実装
│
├── application/         # アプリケーション層
│   ├── npc_service.py   # NPC投稿生成・投稿
│   ├── interaction_service.py  # NPC間相互作用
│   ├── external_reaction_service.py  # 外部投稿への反応
│   ├── affinity_service.py  # 好感度管理
│   ├── stalker_service.py   # ストーカー機能
│   └── factory.py       # サービスファクトリ
│
├── domain/              # ドメイン層
│   ├── models/          # データモデル
│   ├── content/         # コンテンツ生成戦略
│   ├── memory.py        # 記憶システム
│   ├── interaction.py   # 相互作用ロジック
│   ├── relationships.py # 関係性データ
│   ├── scheduler.py     # 投稿スケジューリング
│   └── text_processor.py  # 文章スタイル加工
│
├── infrastructure/      # インフラ層
│   ├── llm/             # LLM連携（Ollama）
│   ├── nostr/           # Nostr投稿
│   ├── storage/         # ファイルリポジトリ
│   └── external/        # 外部API（RSS等）
│
└── config/              # 設定
    └── settings.py
```

## 依存関係

```
CLI → Application → Domain
         ↓
    Infrastructure
```

- CLI層はApplication層のサービスを呼び出す
- Application層はDomain層のロジックとInfrastructure層のリポジトリを使用
- Domain層は外部依存なし（純粋なビジネスロジック）
- Infrastructure層はDomain層のモデルを永続化

## ファイル構造

```
npcs/                    # NPC住人データ
├── npc001/
│   ├── profile.yaml     # プロフィール
│   ├── state.json       # 状態
│   ├── memory.json      # 記憶
│   └── activity.log     # 活動ログ
├── npc002/
│   └── ...
└── ...

data/                    # 共有データ
├── queue/               # 投稿キュー
│   ├── pending.json     # 審査待ち
│   ├── approved.json    # 承認済み
│   ├── rejected.json    # 却下
│   ├── posted.json      # 投稿済み
│   └── dry_run.json     # テスト用
├── relationships/       # 関係性
│   ├── groups.yaml      # グループ
│   ├── pairs.yaml       # ペア関係
│   └── stalkers.yaml    # ストーカー
├── bulletin_board/      # 掲示板
│   ├── news.json        # ニュース
│   └── events.json      # イベント
└── tick_state.json      # tick状態
```
