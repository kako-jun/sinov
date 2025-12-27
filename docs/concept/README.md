# 構想ドキュメント

このフォルダには**未実装**の構想・アイデアを残しています。
実装済みの仕様は `docs/` を参照してください。

## 未実装の構想一覧

### 1. 分散アーキテクチャ

`architecture.md` に詳細を記載。「天から見下ろさない」設計:

- 各NPCが自分のファイルだけを見て判断
- 中央コントローラーなし
- ファイルが「場」として機能

**現状**: tickコマンドで一括処理するアーキテクチャ

## ファイル一覧

| ファイル | 内容 |
|---------|------|
| `parameters.md` | パラメータ詳細仕様（実装済み参考） |
| `reporters.md` | 記者システム詳細（実装済み参考） |
| `architecture.md` | 分散アーキテクチャ構想 |
| `psychology-reference.md` | 心理学概念のパラメータ化案 |
| `character-ideas.md` | キャラクター名・職業・設定のアイデア |

## 実装済み（参考）

以下は `docs/` に仕様ドキュメントあり:

**性格パラメータ（17個）**:
activeness, curiosity, sociability, sensitivity, optimism,
creativity, persistence, expressiveness, expertise, intelligence,
feedback_sensitivity, event_enthusiasm, contrarian, eccentricity,
agreeableness, locus_of_control, self_efficacy

**状態パラメータ（7個）**:
mood, energy, focus, motivation, fatigue, excitement, mental_health

**状態パラメータの更新ロジック**:
- 反応受信時: motivation↑, excitement↑, mental_health↑
- 投稿時: energy↓, fatigue↑
- 時間経過: energy（昼間↑/深夜↓）, fatigue↓, excitement↓
- 無視時: motivation↓, mental_health↓
- 連作: focus（開始時↑/終了時↓）

**活動時間**:
- active_hours（時間のリスト）
- chronotype（朝型/夜型/中間）
- hourly_weight（時間帯別活動確率）
- rhythm_stability（生活リズム安定度）
- daily_schedule（時間帯別活動）

**制作物システム**:
- CreativeWork（進行中の作品）
- CreativeWorks（作品一覧）
- WORK_TYPES（職業別作品タイプ）
- PROGRESS_MESSAGES（進捗別発言テンプレート）
- CreativeWorksManager（進捗更新ロジック）
  - 投稿時30%確率で進捗更新
  - 通常+2%, 集中時+5%, ブレイクスルー+10%
  - 完成時は長期記憶に昇格

**記者システム**:
- reporter_tech: IT・テクノロジー（RSS）
- reporter_game: ゲーム（RSS）
- reporter_creative: 創作・アート（RSS）
- reporter_general: 一般時事（RSS）
- reporter_trend: Xトレンド（スクレイピング）

**その他**:
- アーキテクチャ（レイヤー構造）
- 記憶システム（短期・長期・連作）
- 関係性（グループ・ペア・ストーカー）
- 文章スタイル加工
- 投稿キュー・レビュー
- Nostr連携
