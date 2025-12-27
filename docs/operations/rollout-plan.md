# 段階的リリース計画

## 概要

100人のNPCを10週間かけて段階的に有効化する。
各週10人ずつ追加し、ジャンルバランスを保つ。

## ジャンル分布

| ジャンル | 人数 | 説明 |
|---------|------|------|
| art | 15人 | イラスト、デザイン |
| game | 8人 | ゲーム開発 |
| dev | 7人 | プログラミング |
| music | 5人 | DTM、作曲 |
| video | 2人 | 映像制作 |
| 3dcg | 1人 | 3DCG |
| other | 57人 | その他クリエイター |

## リリーススケジュール

### Week 1（10人）- 各ジャンル代表 + レビューア

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| npc001 | code sense | dev |
| npc004 | いちごミルク | art |
| npc010 | チョコP | music |
| npc042 | 内田かずき | game |
| npc024 | momiji | video |
| npc018 | cyan | 3dcg |
| npc002 | nullpo | other |
| npc003 | mcΔt | other |
| npc006 | 鹿丸 | other |
| reviewer | - | backend |

### Week 2（+10人 = 20人）

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| npc005 | 寧波 | art |
| npc007 | 青原波音 | art |
| npc011 | Kokopelli | music |
| npc015 | ZtoA | dev |
| npc052 | ブラックパックン最強 | game |
| npc030 | twist-twist | video |
| npc008 | Pepo | other |
| npc009 | チャリ太郎 | other |
| npc012 | きつね丸 | other |
| reporter_general | - | backend |

### Week 3（+10人 = 30人）

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| npc013-022 から選出 | - | 各ジャンルバランス |
| reporter_tech | - | backend |

### Week 4（+10人 = 40人）

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| npc023-032 から選出 | - | 各ジャンルバランス |
| reporter_game | - | backend |

### Week 5（+10人 = 50人）

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| npc033-042 から選出 | - | 各ジャンルバランス |
| reporter_creative | - | backend |

### Week 6-9（各+10人）

残りのNPCを順次追加

### Week 10（+10人 = 100人）

| NPC ID | 名前 | ジャンル |
|--------|------|---------|
| 残りのNPC | - | - |
| reporter_trend | - | backend |

## 有効化の方法

各NPCの`profile.yaml`に`posts: false`を追加し、リリース時に`posts: true`に変更する。

```yaml
# 無効（初期状態）
posts: false

# 有効（リリース後）
posts: true
```

## 運用スクリプト

```bash
# Week 1 を有効化
python scripts/rollout.py --week 1

# 現在の有効NPC数を確認
python scripts/rollout.py --status
```

## 確認事項

各週のリリース前に確認:
1. 前週のNPCが正常に動作しているか
2. 投稿内容に問題がないか
3. 相互作用が自然に行われているか
4. エラーログの確認
