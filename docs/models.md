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
  chronotype: intermediate  # lark/owl/intermediate
  hourly_weight:            # 時間帯別活動確率（オプション）
    10: 0.8
    22: 1.0
  rhythm_stability: 0.7     # 生活リズム安定度
  daily_schedule: {}        # 時間帯別活動（オプション）

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
  event_enthusiasm: 0.5  # イベント熱狂度
  contrarian: 0.3        # 逆張り度
  eccentricity: 0.2      # 不思議ちゃん度
  # 心理学由来
  agreeableness: 0.6     # 協調性（高:協力的、低:競争的）
  locus_of_control: 0.7  # 統制の所在（高:内的、低:外的）
  self_efficacy: 0.5     # 自己効力感（高:自信あり、低:不安）

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

creative_works:           # 制作物（オプション）
  current:
    - id: work001
      name: "星降る夜に"
      type: illustration_series
      progress: 0.6
      current_task: "第3話の背景"
  completed: []
  planned: []
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
  "mood": 0.3,
  "energy": 0.5,
  "focus": 0.5,
  "motivation": 0.5,
  "fatigue": 0.0,
  "excitement": 0.0,
  "mental_health": 0.7
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
| energy | エネルギー (0.0〜1.0) |
| focus | 集中度 (0.0〜1.0) |
| motivation | モチベーション (0.0〜1.0) |
| fatigue | 疲労度 (0.0〜1.0) |
| excitement | 興奮度 (0.0〜1.0) |
| mental_health | メンタル (0.0〜1.0) |

## NpcMemory

NPCの記憶。`npcs/npc{ID}/memory.json` に保存。

詳細は [memory.md](memory.md) を参照。

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
