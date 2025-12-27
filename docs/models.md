# データモデル

## NpcProfile

NPCのプロフィール。`npcs/npc{ID}/profile.yaml` に保存。

```yaml
id: 1
name: npc001

personality:
  type: "陽気"           # 性格タイプ
  traits: ["明るい", "好奇心旺盛"]
  emotional_range: 7     # 感情の振れ幅 (0-10)

interests:
  topics: ["Rust", "ゲーム開発"]
  keywords: ["プログラミング", "インディーゲーム"]
  code_languages: ["Rust", "Python"]
  likes:
    manga: ["チェンソーマン"]
    os: ["Linux"]
  dislikes:
    languages: ["Java"]
  values: ["創作活動"]

behavior:
  post_frequency: 3      # 1日の投稿数
  post_frequency_variance: 0.3
  active_hours: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
  post_length_min: 20
  post_length_max: 140
  use_markdown: false
  use_code_blocks: false

social:
  friend_bot_ids: [2, 5]
  reply_probability: 0.3
  repost_probability: 0.1
  like_probability: 0.5

background:
  occupation: "ゲーム開発者"
  experience: "インディーゲームを5年制作"
  hobbies: ["ゲーム", "読書"]
  favorite_quotes: ["コードは詩だ"]

traits_detail:           # 詳細な性格パラメータ (0.0-1.0)
  activeness: 0.7        # 積極性
  curiosity: 0.8         # 好奇心
  sociability: 0.6       # 社交性
  sensitivity: 0.4       # 感受性
  optimism: 0.7          # 楽観性
  creativity: 0.8        # 創造性
  persistence: 0.6       # 粘り強さ
  expressiveness: 0.7    # 表現力
  expertise: 0.6         # 習熟度
  intelligence: 0.7      # 知性
  feedback_sensitivity: 0.5  # 反応への感度

style: normal            # normal/ojisan/young/2ch/otaku/polite/terse
habits: [wip_poster]     # news_summarizer/emoji_heavy/tip_sharer/wip_poster等

prompts:
  positive:
    - "技術的な話題を好む"
  negative:
    - "政治的な発言をしない"

writing_style:
  typo_rate: 0.02        # 誤字率 (0.0-0.1)
  line_break: minimal    # none/minimal/sentence/paragraph
  punctuation: full      # full/comma_only/period_only/none
  quirks: [w_heavy]      # 文章の癖
```

## NpcState

NPCの状態。`npcs/npc{ID}/state.json` に保存。

```json
{
  "id": 1,
  "last_post_time": 1703500000,
  "next_post_time": 1703528800,
  "total_posts": 42,
  "last_post_content": "Rustでゲーム作ってる",
  "last_event_id": "abc123...",
  "post_history": ["投稿1", "投稿2"],
  "discovered_topics": ["WebAssembly"],
  "mood": 0.3
}
```

| フィールド | 説明 |
|-----------|------|
| last_post_time | 最後の投稿時刻（Unix timestamp） |
| next_post_time | 次回投稿予定時刻 |
| total_posts | 累計投稿数 |
| post_history | 最新20件の投稿内容 |
| discovered_topics | 進化で獲得したトピック |
| mood | 気分 (-1.0〜1.0) |

## NpcMemory

NPCの記憶。`npcs/npc{ID}/memory.json` に保存。

```json
{
  "npc_id": 1,
  "long_term_core": {
    "occupation": "ゲーム開発者",
    "experience": "5年"
  },
  "long_term_acquired": [
    {
      "content": "Rustでゲームエンジン作れた",
      "acquired_at": "2025-01-01T12:00:00",
      "importance": 0.9,
      "tags": ["Rust", "ゲームエンジン", "達成"]
    }
  ],
  "short_term": [
    {
      "content": "新しいクレートを試してる",
      "strength": 0.8,
      "created_at": "2025-01-01T10:00:00",
      "source": "post"
    }
  ],
  "series": {
    "active": true,
    "theme": "Rustゲーム開発日記",
    "current_index": 2,
    "total_planned": 4,
    "posts": ["1日目", "2日目"]
  },
  "recent_posts": ["投稿1", "投稿2"],
  "last_updated": "2025-01-01T12:00:00"
}
```

### 記憶の種類

| 種類 | 説明 | 永続性 |
|------|------|--------|
| long_term_core | プロフィールから抽出した基本情報 | 不変 |
| long_term_acquired | 獲得した記憶 | 永続 |
| short_term | 一時的な関心事 | 減衰する |

### 記憶の流れ

1. 投稿生成 → 短期記憶に追加 (strength=1.0)
2. リアクション受信 → strength強化 (+0.3)
3. 時間経過 → strength減衰 (-0.1/tick)
4. strength ≥ 0.95 → 長期記憶に昇格

## QueueEntry

投稿キューエントリ。`data/queue/{status}.json` に保存。

```json
{
  "id": "abc12345",
  "npc_id": 1,
  "npc_name": "npc001",
  "content": "投稿内容",
  "created_at": "2025-01-01T12:00:00",
  "status": "pending",
  "post_type": "normal",
  "reply_to": null,
  "conversation": null,
  "mumble_about": null
}
```

### ステータス遷移

```
pending → approved → posted
       ↘ rejected
```

### 投稿タイプ

| タイプ | 説明 |
|--------|------|
| normal | 通常投稿 |
| reply | リプライ |
| reaction | リアクション（絵文字） |
| mumble | 引用なし言及 |
| quote | 引用投稿 |

## 関係性データ

### Group

`data/relationships/groups.yaml`

```yaml
groups:
  - id: rust_lovers
    name: Rust愛好会
    members: [npc001, npc003, npc007]
    interaction:
      reply_probability: 0.5
      reaction_probability: 0.7
      topics: [Rust, システムプログラミング]
```

### Pair

`data/relationships/pairs.yaml`

```yaml
pairs:
  - id: pair001
    type: close_friends  # close_friends/couple/siblings/rivals/mentor/awkward
    members: [npc001, npc002]
    interaction:
      reply_probability: 0.7
      tone: casual
      topics: [ゲーム開発]
      avoid: [仕事の愚痴]
```

### Stalker

`data/relationships/stalkers.yaml`

```yaml
stalkers:
  - resident: npc010
    target:
      type: external
      pubkey: "npub1..."
      display_name: "kako-jun"
    behavior:
      check_interval_minutes: 60
      reaction_probability: 0.3
      reactions: ["👀", "🔥"]
```

## Affinity

好感度データ。関係性リポジトリに保存。

```json
{
  "npc001": {
    "npc002": {
      "affinity": 0.7,
      "trust": 0.5,
      "familiarity": 0.6,
      "last_interaction": "2025-01-01T12:00:00"
    }
  }
}
```

| パラメータ | 説明 | 範囲 |
|-----------|------|------|
| affinity | 好感度 | -1.0〜1.0 |
| trust | 信頼度 | 0.0〜1.0 |
| familiarity | 親密度 | 0.0〜1.0 |
