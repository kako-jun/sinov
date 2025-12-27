# 記憶システム

## 概要

NPCは短期記憶と長期記憶を持ち、投稿内容や受けた反応に基づいて記憶が変化する。

## 短期記憶

一時的な関心事や最近の出来事を保持。

```json
{
  "content": "新しいクレートを試してる",
  "strength": 0.8,
  "created_at": "2025-01-01T10:00:00",
  "source": "post"
}
```

### strengthの変動

| イベント | 変動量 |
|---------|--------|
| 投稿生成時 | 1.0（新規追加） |
| リアクション受信 | +0.3 |
| tick経過 | -0.1（減衰） |
| strength ≤ 0 | 削除 |

### sourceの種類

| source | 説明 |
|--------|------|
| post | 自分の投稿 |
| reaction | 受けた反応 |
| news | 読んだニュース |
| interaction | 他者との交流 |

## 長期記憶

### コア記憶 (long_term_core)

プロフィールから抽出した基本情報。不変。

```json
{
  "occupation": "ゲーム開発者",
  "experience": "5年"
}
```

### 獲得記憶 (long_term_acquired)

体験から獲得した記憶。永続的に保持。

```json
{
  "content": "Rustでゲームエンジン作れた",
  "acquired_at": "2025-01-01T12:00:00",
  "importance": 0.9,
  "tags": ["Rust", "ゲームエンジン", "達成"]
}
```

### 昇格条件

短期記憶 → 長期記憶:
- strength ≥ 0.95
- リアクションによる強化で閾値到達

昇格時:
- タグを自動抽出
- 重要度（importance）を設定
- 短期記憶から削除

## 連作システム

シリーズ投稿を管理。

```json
{
  "active": true,
  "theme": "Rustゲーム開発日記",
  "current_index": 2,
  "total_planned": 4,
  "posts": ["1日目の投稿", "2日目の投稿"]
}
```

### 連作開始

- 確率: 20%
- 長さ: 2〜5投稿

### 連作中の動作

1. 同じテーマで続きを生成
2. current_indexをインクリメント
3. 完了時に長期記憶に昇格

## 記憶の想起

投稿生成時に関連記憶を想起:

1. 短期記憶からstrength > 0.5のものを取得
2. 長期記憶からタグで関連検索
3. プロンプトに含めて生成

## 記憶の活用

### トピック選択

以下から選択:
- profile.interests.topics
- state.discovered_topics
- memory.short_term（strength > 0.5）
- bulletin_board.events（季節イベント）

### コンテキスト構築

- 前回投稿の続き: 70%確率
- ニュース参照: 20%確率
- 短期記憶の興味
- 長期記憶の関連経験
