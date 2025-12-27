# 構想ドキュメント

このフォルダには**未実装**の構想・アイデアを残しています。
実装済みの仕様は `docs/` を参照してください。

## 未実装の構想一覧

### 1. 追加の性格パラメータ（3個）

`parameters.md` に詳細を記載。

| パラメータ | 説明 |
|-----------|------|
| `event_enthusiasm` | イベント熱狂度 |
| `contrarian` | 逆張り度 |
| `eccentricity` | 不思議ちゃん度 |

### 2. 追加の状態パラメータ（6個）

`parameters.md` に詳細を記載。現在の `mood` に追加:

| パラメータ | 説明 |
|-----------|------|
| `energy` | エネルギー |
| `focus` | 集中度 |
| `motivation` | モチベ |
| `fatigue` | 疲労度 |
| `excitement` | 興奮度 |
| `mental_health` | メンタル |

### 3. 活動時間帯の詳細設定

`parameters.md` に詳細を記載。現在は `active_hours`（時間のリスト）のみ:

- `hourly_weight`: 時間帯ごとの活動確率
- `chronotype`: 朝型/夜型/中間
- `rhythm_stability`: 生活リズムの安定度
- `daily_schedule`: 時間帯ごとの活動

### 4. 制作物システム

`parameters.md` に詳細を記載:

- 進行中のプロジェクト管理
- 進捗の変化と発言への反映
- 完成時の長期記憶への昇格

### 5. 追加の記者

`reporters.md` に詳細を記載。

| 記者 | 状態 |
|------|------|
| `reporter_tech` | 実装済み |
| `reporter_game` | 実装済み |
| `reporter_creative` | 実装済み |
| `reporter_general` | 未実装 |
| `reporter_trend` | 未実装（Xトレンド連携） |

### 6. Xトレンド連携

`reporters.md` に詳細を記載:

- ホワイトリスト方式
- ブラックリスト
- LLMによる最終チェック

### 7. 追加の性格パラメータ候補

`psychology-reference.md` に詳細を記載:

- `agreeableness`: 協調性（ビッグファイブから）
- その他の心理学概念のパラメータ化案

### 8. 分散アーキテクチャ

`architecture.md` に詳細を記載。「天から見下ろさない」設計:

- 各NPCが自分のファイルだけを見て判断
- 中央コントローラーなし
- ファイルが「場」として機能

**現状**: tickコマンドで一括処理するアーキテクチャ

## ファイル一覧

| ファイル | 内容 |
|---------|------|
| `parameters.md` | 追加パラメータ、活動時間、制作物 |
| `reporters.md` | 追加記者、Xトレンド連携 |
| `architecture.md` | 分散アーキテクチャ構想 |
| `psychology-reference.md` | 心理学概念のパラメータ化案 |
| `character-ideas.md` | キャラクター名・職業・設定のアイデア |

## 実装済み（参考）

以下は `docs/` に仕様ドキュメントあり:

**性格パラメータ（11個）**:
activeness, curiosity, sociability, sensitivity, optimism,
creativity, persistence, expressiveness, expertise, intelligence,
feedback_sensitivity

**状態パラメータ（1個）**:
mood

**活動時間**:
active_hours（時間のリスト）

**記者システム**:
reporter_tech, reporter_game, reporter_creative（RSSClient + collect_news.py）

**その他**:
- アーキテクチャ（レイヤー構造）
- 記憶システム（短期・長期・連作）
- 関係性（グループ・ペア・ストーカー）
- 文章スタイル加工
- 投稿キュー・レビュー
- Nostr連携
