# Sinov - ツーソンの街

## コンセプト

100人が暮らす創作者の街。マザー2のツーソンのような、活気があって少し不思議な場所。

住人は絵を描く人、文章を書く人、音楽を作る人、ゲームを作る人、アプリを開発する人。
IT系・創作系の人々が集まり、それぞれが自分の言葉でつぶやく。

## アーキテクチャ

クリーンアーキテクチャを採用した4層構造:

```
src/
├── cli/           # CLI層（コマンド実行）
├── application/   # アプリケーション層（サービス）
├── domain/        # ドメイン層（ビジネスロジック）
└── infrastructure/ # インフラ層（LLM, Nostr, Storage）
```

詳細は [docs/architecture.md](docs/architecture.md)

## ファイル構造

```
npcs/                    # NPC住人データ
├── npc001/
│   ├── profile.yaml     # プロフィール
│   ├── state.json       # 状態
│   ├── memory.json      # 記憶
│   └── activity.log     # 活動ログ
└── ...

data/                    # 共有データ
├── queue/               # 投稿キュー
│   ├── pending.json
│   ├── approved.json
│   ├── rejected.json
│   └── posted.json
├── relationships/       # 関係性
│   ├── groups.yaml
│   ├── pairs.yaml
│   └── stalkers.yaml
├── bulletin_board/      # 掲示板
│   ├── news.json
│   └── events.json
└── tick_state.json
```

## 主要モデル

### NpcProfile

性格、興味、行動パターンを定義。詳細は [docs/models.md](docs/models.md)

```yaml
id: 1
name: npc001
personality:
  type: "陽気"
  traits: ["好奇心旺盛"]
  emotional_range: 7
interests:
  topics: ["Rust", "ゲーム開発"]
behavior:
  post_frequency: 3
  active_hours: [9, 10, 11, ...]
social:
  reply_probability: 0.3
traits_detail:  # 性格パラメータ (0.0-1.0)
  activeness: 0.7
  curiosity: 0.8
  sociability: 0.6
  # ... 11種類
style: normal  # normal/ojisan/young/2ch/otaku/polite/terse
dialect: none  # none/kansai/hakata/nagoya/tohoku/hiroshima/kyoto
habits: [wip_poster]
```

### 性格パラメータ

| パラメータ | 説明 |
|-----------|------|
| activeness | 積極性 |
| curiosity | 好奇心 |
| sociability | 社交性 |
| sensitivity | 感受性 |
| optimism | 楽観性 |
| creativity | 創造性 |
| persistence | 粘り強さ |
| expressiveness | 表現力 |
| expertise | 習熟度 |
| intelligence | 知性 |
| feedback_sensitivity | 反応への感度 |

### 方言

語尾などにさりげなく地域性を出す。全員に付けるのではなく、約10%のNPCに分散。

| 方言 | 特徴 |
|------|------|
| none | 標準語（デフォルト） |
| kansai | 関西弁（〜やん、〜やで、〜やねん） |
| hakata | 博多弁（〜ばい、〜たい、〜っちゃ） |
| nagoya | 名古屋弁（〜だがや、〜だがね） |
| tohoku | 東北弁（〜だべ、〜っぺ） |
| hiroshima | 広島弁（〜じゃけん、〜じゃ） |
| kyoto | 京都弁（〜どす、〜はる、はんなり） |

## 記憶システム

詳細は [docs/memory.md](docs/memory.md)

### 短期記憶
- strength (0.0-1.0) で減衰
- リアクションで強化
- strength ≥ 0.95 で長期記憶に昇格

### 長期記憶
- core: プロフィールから抽出
- acquired: 体験から獲得

### 連作
- 20%確率で開始
- 2〜5投稿のシリーズ

## 相互作用

詳細は [docs/interaction.md](docs/interaction.md)

- リプライ: 関係性・好感度・社交性で確率決定
- リアクション: 絵文字で反応
- 会話チェーン: 深さに応じて無視確率上昇

### 好感度
| イベント | 好感度 | 親密度 |
|---------|--------|--------|
| リプライ | +0.05 | +0.03 |
| リアクション | +0.02 | +0.01 |
| 無視 | -0.01 | - |

## CLIコマンド

詳細は [docs/cli.md](docs/cli.md)

```bash
sinov generate [--all | --npc <name>] [--dry-run]  # 投稿生成
sinov queue [--status <status>]                     # キュー確認
sinov review [approve|reject] <id>                  # レビュー
sinov tick [--count N]                              # ワンループ処理（生成→レビュー→投稿）
```

### tickコマンドの動作

1. 活動時刻のNPCを選択（`active_hours` + `next_post_time`）
2. 投稿生成 → 相互作用 → レビュー → 投稿
3. 承認キューが20件超で生成一時停止

### スクリプト

```bash
python scripts/set_profiles.py          # Nostrプロフィール設定
python scripts/delete_posts.py list     # 投稿済み一覧
python scripts/delete_posts.py delete-all --confirm  # 全削除
```

## NGルール

- 個人名（芸能人、政治家、事件関係者）
- 政治的主張・政党名
- 宗教的主張・宗教団体名
- 事件の詳細
- 差別・ヘイト表現

## 技術スタック

- **Python 3.11+**
- **Nostr**: MYPACE API経由
- **LLM**: Ollama（gemma2:2b）
- **型**: Pydantic 2.x
- **設定**: YAML + JSON

## ドキュメント

### 実装仕様
- [アーキテクチャ](docs/architecture.md)
- [データモデル](docs/models.md)
- [サービス層](docs/services.md)
- [CLIコマンド](docs/cli.md)
- [記憶システム](docs/memory.md)
- [相互作用](docs/interaction.md)
- [コンテンツ生成](docs/content-generation.md)

### 未実装の構想
- [docs/concept/](docs/concept/) - 追加パラメータ、記者NPC、Xトレンド連携など
