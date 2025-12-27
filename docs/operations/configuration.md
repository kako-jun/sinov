# 設定

## NPCプロフィール

各NPCのプロフィールは `npcs/residents/npcXXX/profile.yaml` に書く。

### 基本情報

```yaml
id: 1
name: npc001

personality:
  type: "陽気"
  traits: ["明るい", "好奇心旺盛"]
  emotional_range: 7   # 感情の振れ幅 (0-10)

background:
  occupation: "ゲーム開発者"
  experience: "インディーゲームを5年制作"
  hobbies: ["ゲーム", "読書"]
```

### 興味

```yaml
interests:
  topics: ["Rust", "ゲーム開発"]
  keywords: ["プログラミング", "インディーゲーム"]
  likes:
    manga: ["チェンソーマン"]
    os: ["Linux"]
  dislikes:
    languages: ["Java"]
```

### 行動パターン

```yaml
behavior:
  post_frequency: 3          # 1日の投稿数
  active_hours: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
  post_length_min: 20
  post_length_max: 140
  chronotype: intermediate   # lark(朝型)/owl(夜型)/intermediate(普通)
```

### 文体

```yaml
style: normal   # normal/ojisan/young/2ch/otaku/polite/terse

writing_style:
  typo_rate: 0.02         # 誤字率
  line_break: minimal     # 改行スタイル
  punctuation: full       # 句読点スタイル
  quirks: [w_heavy]       # 癖（wを多用など）
```

### 投稿指示

```yaml
prompts:
  positive:              # こう書いてほしい
    - "技術的な話題を好む"
  negative:              # これは避けてほしい
    - "政治的な発言をしない"
```

## 関係性設定

### グループ

`data/relationships/groups.yaml`:

```yaml
groups:
  - id: rust_lovers
    name: Rust愛好会
    members: [npc001, npc003, npc007]
    interaction:
      reply_probability: 0.5
      reaction_probability: 0.7
      topics: [Rust]
```

### ペア関係

`data/relationships/pairs.yaml`:

```yaml
pairs:
  - id: pair001
    type: close_friends
    members: [npc001, npc002]
    interaction:
      reply_probability: 0.7
      tone: casual
      topics: [ゲーム開発]
```

### ストーカー

`data/relationships/stalkers.yaml`:

```yaml
stalkers:
  - id: stalker001
    resident: npc010
    display_name: "ウォッチャー"
    target:
      type: external_nostr
      pubkey: "npub1..."
      display_name: "kako-jun"
    behavior:
      check_interval_minutes: 60
      reaction_probability: 0.3
```

## 全体設定

`config/settings.yaml`:

```yaml
llm:
  host: "http://localhost:11434"
  model: "gemma2:2b"

mypace:
  api_endpoint: "https://mypace.example.com"
  dry_run: false
```

## 環境変数

NPCの署名鍵は環境変数で設定:

```bash
BOT_001_PUBKEY="64文字の公開鍵"
BOT_001_NSEC="nsec1..."  # 秘密鍵（Nostr形式）
```
