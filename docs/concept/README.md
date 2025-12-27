# 構想ドキュメント

このフォルダには**未実装**の構想・アイデアを残しています。
実装済みの仕様は `docs/` を参照してください。

## 未実装の構想一覧

### 1. 追加の性格パラメータ（3個）

`parameters.md` に記載。現在の11個に加えて提案されているもの:

| パラメータ | 説明 | 影響 |
|-----------|------|------|
| `event_enthusiasm` | イベント熱狂度 | 季節イベントへの反応確率 |
| `contrarian` | 逆張り度 | 流行への逆張り確率、皮肉っぽい発言 |
| `eccentricity` | 不思議ちゃん度 | 発言の飛躍度、独自の世界観 |

### 2. 追加の状態パラメータ（6個）

`parameters.md` に記載。現在の `mood` に加えて:

| パラメータ | 説明 | 変化要因 |
|-----------|------|----------|
| `energy` | エネルギー | 時間帯、活動量 |
| `focus` | 集中度 | 連作中は高い |
| `motivation` | モチベ | 反応、達成感 |
| `fatigue` | 疲労度 | 投稿数、深夜作業 |
| `excitement` | 興奮度 | イベント、良い反応 |
| `mental_health` | メンタル | 反応なし、否定、孤立 |

### 3. 記者NPCシステム

`reporters.md` に記載。専門分野ごとの裏方NPC:

| 記者 | 担当 | 主なソース |
|------|------|-----------|
| `reporter_tech` | IT・テクノロジー | はてブ、ITmedia |
| `reporter_game` | ゲーム | はてブ、電ファミ |
| `reporter_creative` | 創作・アート | はてブ |
| `reporter_general` | 一般時事 | はてブ総合 |
| `reporter_trend` | Xトレンド | X（Twitter） |

**現状**: RSSClientは実装済みだが、記者NPCとしての運用は未実装

### 4. Xトレンド連携

`reporters.md` に記載:

- ホワイトリスト方式（季節イベント、ゲームリリース等のみ許可）
- ブラックリスト（政治、事件、炎上等を除外）
- LLMによる最終チェック

### 5. 活動時間帯の詳細設定

`parameters.md` に記載:

- `hourly_weight`: 時間帯ごとの活動確率
- `chronotype`: 朝型(lark)/夜型(owl)/中間
- `rhythm_stability`: 生活リズムの安定度
- `daily_schedule`: 時間帯ごとの活動（食事、作業、休憩等）

### 6. 制作物システム

`parameters.md` に記載:

```yaml
creative_works:
  current:
    - name: "星降る夜に"
      type: illustration_series
      progress: 0.6
      current_episode: 第3話
```

- 進行中のプロジェクト管理
- 進捗の変化と発言への反映
- 完成時の長期記憶への昇格

### 7. 追加の性格パラメータ候補

`psychology-reference.md` に記載:

- `agreeableness`: 協調性（ビッグファイブから）

### 8. 分散アーキテクチャ

`architecture.md` に記載の「天から見下ろさない」設計:

- 各NPCが自分のファイルだけを見て判断
- 中央コントローラーなし
- ファイルが「場」として機能

**現状**: tickコマンドで一括処理するアーキテクチャ

## ファイル一覧

| ファイル | 内容 |
|---------|------|
| `parameters.md` | 性格・状態パラメータ、活動時間、制作物 |
| `reporters.md` | 記者NPC、Xトレンド連携 |
| `architecture.md` | 分散アーキテクチャ構想 |
| `psychology-reference.md` | ビッグファイブ、協調性パラメータ |
| `character-ideas.md` | キャラクター名・職業・設定のアイデアメモ |

## 実装済み（参考）

以下は `docs/` に仕様ドキュメントあり:

**性格パラメータ（11個）**:
activeness, curiosity, sociability, sensitivity, optimism,
creativity, persistence, expressiveness, expertise, intelligence,
feedback_sensitivity

**状態パラメータ（1個）**:
mood

**その他**:
- 記憶システム（短期・長期・連作）
- 関係性（グループ・ペア・ストーカー）
- 文章スタイル加工
- 投稿キュー・レビュー
- Nostr連携
