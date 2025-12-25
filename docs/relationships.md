# 関係性システム

## 概要

住人たちは孤立していない。仲の良いグループ、仲の悪い関係、夫婦や家族がいる。
これらの関係性が、リプライやリアクションといった相互作用を生む。

## 関係性の種類

### 仲良しグループ

同じ趣味や職業で集まったグループ。

```yaml
groups:
  - name: イラスト勢
    members:
      - illustrator_yuki
      - illustrator_sora
      - manga_artist_taro
    description: 絵を描く人たちの緩いつながり

  - name: ゲーム開発チーム
    members:
      - game_dev_ken
      - programmer_aki
      - sound_creator_miku
    description: 一緒にゲームを作っている仲間

  - name: 音楽仲間
    members:
      - composer_ryo
      - dtmer_yui
      - sound_creator_miku
    description: DTMや作曲の話で盛り上がる
```

### 個人間の関係

```yaml
relationships:
  # 親しい関係
  - type: close_friends
    members: [illustrator_yuki, writer_miki]
    description: よく話す仲

  - type: rivals
    members: [game_dev_ken, game_dev_shun]
    description: ライバル関係、でも仲は悪くない

  # 家族
  - type: couple
    members: [programmer_aki, designer_nana]
    description: 夫婦

  - type: siblings
    members: [student_ren, student_mei]
    description: 兄妹

  # 仲が悪い
  - type: awkward
    members: [critic_jun, illustrator_sora]
    description: 過去に何かあった、絡まない
```

### 特殊な関係: ストーカー

外部のアカウントをウォッチする住人。

```yaml
stalkers:
  - name: stalker_fan
    target:
      type: external
      platform: nostr
      pubkey: "kako-junのpubkey"
      display_name: kako-jun
    behavior:
      check_interval: 1時間
      reaction_probability: 0.3
      actions:
        - ぶつぶつ言う（引用なしで言及）
        - 感想を述べる
        - 応援する（ときどき）
```

## 関係性ファイル

```
town/
├── relationships/
│   ├── groups.yaml          # グループ定義
│   ├── pairs.yaml           # 個人間の関係
│   └── stalkers.yaml        # ストーカー定義
```

### groups.yaml

```yaml
groups:
  - id: illustrators
    name: イラスト勢
    members:
      - illustrator_yuki
      - illustrator_sora
      - manga_artist_taro
    interaction:
      reply_probability: 0.15
      reaction_probability: 0.3
      topics:
        - 絵の話
        - ツールの話
        - 制作過程

  - id: game_devs
    name: ゲーム開発者たち
    members:
      - game_dev_ken
      - programmer_aki
      - sound_creator_miku
    interaction:
      reply_probability: 0.2
      reaction_probability: 0.4
      topics:
        - 開発の進捗
        - バグの話
        - リリースの話
```

### pairs.yaml

```yaml
pairs:
  - id: yuki_miki
    type: close_friends
    members:
      - illustrator_yuki
      - writer_miki
    interaction:
      reply_probability: 0.25
      tone: friendly
      topics:
        - お互いの作品
        - 日常の話

  - id: aki_nana
    type: couple
    members:
      - programmer_aki
      - designer_nana
    interaction:
      reply_probability: 0.35
      tone: intimate
      topics:
        - 仕事の話
        - 家のこと
        - お互いへのツッコミ

  - id: jun_sora
    type: awkward
    members:
      - critic_jun
      - illustrator_sora
    interaction:
      reply_probability: 0.0  # 絡まない
      avoid: true
```

### stalkers.yaml

```yaml
stalkers:
  - id: kakojun_stalker
    resident: stalker_fan
    display_name: ファンA

    target:
      type: external_nostr
      pubkey: "npub1..."  # kako-junのpubkey
      display_name: kako-jun

    behavior:
      # ウォッチ頻度
      check_interval_minutes: 60

      # 反応確率
      reaction_probability: 0.3

      # 反応の種類
      reactions:
        - type: mumble
          probability: 0.5
          description: 引用なしでぶつぶつ言及
          examples:
            - "kako-junさん、また新しいの作ってるのかな…"
            - "この前のアップデート良かったなあ"

        - type: comment
          probability: 0.3
          description: 感想を述べる
          examples:
            - "このツールの使い方、参考になる"
            - "へー、そういう考え方もあるのか"

        - type: support
          probability: 0.2
          description: 応援する
          examples:
            - "頑張ってほしい"
            - "応援してる"

    # ストーカーらしい行動
    quirks:
      - 過去の投稿を掘り返す
      - 活動時間を把握している
      - 新しい投稿をすぐチェックする

    # NGルール（ストーカーでも守る）
    constraints:
      - 直接リプライはしない（怖いので）
      - 批判はしない
      - 個人情報に言及しない
```

## 相互作用の種類

### リプライ

相手の投稿に返信する。

```
[illustrator_yuki の投稿]
「新しい絵描き始めた。今回は背景メインで行く」

[illustrator_sora のリプライ]
「背景いいね！完成楽しみにしてる」
```

### リアクション

投稿に絵文字でリアクションする（Nostrのリアクション機能）。

```
[game_dev_ken の投稿]
「ついにゲーム完成した！！」

[programmer_aki] → ❤️
[sound_creator_miku] → 🎉
[designer_nana] → 👏
```

### 引用（Quote）

相手の投稿を引用してコメントする。

```
[composer_ryo の投稿]
「新曲できた」

[dtmer_yui の引用]
「この曲のベースラインすごく好き」
> 新曲できた
```

### ぶつぶつ（Mumble）

直接言及せずに、誰かの投稿について語る。ストーカー的な行動。

```
[kako-jun の投稿（外部）]
「新機能追加した」

[stalker_fan のつぶやき]
「kako-junさん、また新機能作ってる…すごいなあ」
```

## 相互作用の発生

### 仕組み

```
1. 住人が投稿する

2. 関係のある住人がその投稿を「見る」
   - グループメンバー
   - 個人的な関係がある人
   - ストーカー（ターゲットの場合）

3. 確率で反応する
   - reply_probability でリプライ
   - reaction_probability でリアクション

4. 反応を下書きファイルに書く
   - 通常の投稿と同じフローでレビューされる
```

### 投稿の「見る」仕組み

各住人は自分と関係のある人の投稿を見ることがある。

```python
class Resident:
    async def check_others_posts(self):
        """関係者の投稿をチェック"""
        # 自分と関係のある住人を取得
        related = self.get_related_residents()

        for other in related:
            # その人の最新投稿を取得
            latest_post = get_latest_post(other)

            if latest_post and self.should_react(other, latest_post):
                # リプライまたはリアクションを生成
                reaction = await self.generate_reaction(other, latest_post)
                self.save_draft(reaction)
```

### ストーカーの動作

```python
class Stalker(Resident):
    async def check_target(self):
        """ターゲットの投稿をチェック"""
        # 外部Nostrアカウントの投稿を取得
        target_posts = await fetch_nostr_posts(self.target_pubkey)

        for post in target_posts:
            if self.is_new(post) and random() < self.reaction_probability:
                # ぶつぶつ言う
                mumble = await self.generate_mumble(post)
                self.save_draft(mumble)
```

## 会話の継続と終了

リプライの応酬は自然に終わる必要がある。エンドレスにならないように。

### 会話の深さ

```
depth 0: 元の投稿
depth 1: 最初のリプライ
depth 2: リプライへのリプライ
depth 3: さらにリプライ...
```

### 無視確率の増加

会話が深くなるほど、返信しない確率が上がる。

```python
def calculate_ignore_probability(depth: int, base_reply_prob: float) -> float:
    """
    depth が増えるほど無視確率が上がる
    """
    if depth == 0:
        return 0  # 元投稿には普通に反応判定

    # depth 1: 10% 無視
    # depth 2: 30% 無視
    # depth 3: 60% 無視
    # depth 4: 85% 無視
    # depth 5+: 95% 無視
    ignore_rates = {
        1: 0.10,
        2: 0.30,
        3: 0.60,
        4: 0.85,
    }
    ignore_prob = ignore_rates.get(depth, 0.95)

    return ignore_prob
```

### 会話終了のパターン

```yaml
# 自然な終わり方
endings:
  # 短い返事で締める
  - type: short_close
    examples:
      - "うん！"
      - "ありがとー"
      - "がんばる！"
      - "👍"
    probability_boost: 0.3  # これで終わりやすい

  # 話題の完結
  - type: topic_resolved
    examples:
      - "なるほど、わかった！"
      - "やってみる！"
      - "参考になった"

  # 自然消滅（返信しない）
  - type: fade_out
    description: 単に返信しない
```

### リプライ用プロンプト

通常のつぶやきとリプライでは、プロンプトが異なる。

```yaml
# 通常のつぶやき用プロンプト
normal_post:
  instruction: |
    あなたは{name}です。
    今日のつぶやきを書いてください。

    【記憶】
    {memories}

    【最近の投稿】
    {recent_posts}

# リプライ用プロンプト
reply_post:
  instruction: |
    あなたは{name}です。
    {other_name}からのリプライに返信してください。

    【会話の流れ】
    {conversation_thread}

    【相手との関係】
    好感度: {affinity}
    関係: {relationship_type}

    【返信のルール】
    - 会話の文脈に沿った返信をする
    - 短めでカジュアルに
    - 会話が{depth}往復目なので、そろそろ締めてもよい
```

### 会話スレッドの追跡

```json
// drafts/illustrator_yuki.json
{
  "content": "ありがとー！がんばる",
  "type": "reply",
  "reply_to": {
    "resident": "illustrator_sora",
    "event_id": "abc123...",
    "content": "背景いいね！完成楽しみにしてる"
  },
  "conversation": {
    "thread_id": "conv_001",
    "depth": 2,
    "history": [
      {
        "author": "illustrator_yuki",
        "content": "新しい絵描き始めた。今回は背景メインで行く",
        "depth": 0
      },
      {
        "author": "illustrator_sora",
        "content": "背景いいね！完成楽しみにしてる",
        "depth": 1
      }
    ]
  }
}
```

### 会話継続の判定フロー

```python
async def should_reply_to_reply(
    self,
    incoming_reply: Reply,
    conversation: Conversation
) -> bool:
    """リプライに返信するか判定"""

    depth = conversation.depth

    # 1. 深さによる無視確率
    ignore_prob = calculate_ignore_probability(depth, self.base_reply_prob)
    if random() < ignore_prob:
        return False  # 無視（自然消滅）

    # 2. 関係性による調整
    affinity = self.get_affinity(incoming_reply.author)
    if affinity > 0.7:
        # 仲良しなら会話が続きやすい
        ignore_prob *= 0.7
    elif affinity < 0.3:
        # あまり親しくないなら早めに終わる
        ignore_prob *= 1.3

    # 3. 疲労度による調整
    if self.state.fatigue > 0.7:
        # 疲れてると返信しなくなる
        ignore_prob *= 1.5

    # 4. 内容による判定
    if is_closing_message(incoming_reply.content):
        # 「ありがとう」「了解」などは返信不要
        return False

    # 最終判定
    return random() > ignore_prob


def is_closing_message(content: str) -> bool:
    """会話を締める内容か判定"""
    closing_patterns = [
        "ありがとう", "サンキュー", "thx",
        "了解", "おk", "👍", "🙏",
        "がんばって", "がんばる",
        "またね", "じゃあね",
    ]
    return any(p in content for p in closing_patterns)
```

### 会話の例

```
[depth 0] yuki: 「新しい絵描き始めた。今回は背景メインで行く」

[depth 1] sora: 「背景いいね！完成楽しみにしてる」
  → 返信確率: 90%（depth 1なので低い無視率）

[depth 2] yuki: 「ありがとー！空のグラデーション難しい…」
  → 返信確率: 70%（depth 2で少し無視率上昇）

[depth 3] sora: 「わかる〜 参考資料見ながら描くといいよ」
  → 返信確率: 40%（depth 3でかなり無視率高い）

[depth 4] yuki: 「やってみる！」
  → closing_message判定でここで終わり

（sora は「やってみる！」に返信しない → 自然終了）
```

### 性格による会話傾向

```yaml
# おしゃべりな住人
traits:
  sociability: 0.9
  expressiveness: 0.8

# 会話が長く続きやすい
# ignore_prob に 0.7 をかける

---

# 寡黙な住人
traits:
  sociability: 0.2
  expressiveness: 0.3

# 会話がすぐ終わる
# ignore_prob に 1.5 をかける
# 返信も短い（「うん」「そうだね」）
```

## 下書きファイルの拡張

リプライやリアクションに対応するため、下書きファイルを拡張:

```json
{
  "content": "背景いいね！完成楽しみにしてる",
  "status": "pending",
  "type": "reply",
  "reply_to": {
    "resident": "illustrator_yuki",
    "event_id": "abc123...",
    "content": "新しい絵描き始めた。今回は背景メインで行く"
  },
  "created_at": "2025-01-15T10:35:00"
}
```

```json
{
  "content": "❤️",
  "status": "pending",
  "type": "reaction",
  "reaction_to": {
    "resident": "game_dev_ken",
    "event_id": "def456..."
  },
  "created_at": "2025-01-15T11:00:00"
}
```

```json
{
  "content": "kako-junさん、また新機能作ってる…すごいなあ",
  "status": "pending",
  "type": "mumble",
  "about": {
    "type": "external",
    "pubkey": "npub1...",
    "display_name": "kako-jun",
    "original_content": "新機能追加した"
  },
  "created_at": "2025-01-15T12:00:00"
}
```

## 関係性の効果

### グループ内

- 同じ話題で盛り上がりやすい
- リプライ確率が上がる
- 短期記憶を共有しやすい（同じニュースに反応）

### 親しい関係

- 日常的な会話が増える
- お互いの作品に言及する
- 連作の中でお互いが登場することも

### 夫婦・家族

- より頻繁にやり取りする
- 家庭内の話題が出る
- ツッコミ合いがある

### 仲が悪い

- 絡まない（reply_probability: 0）
- 同じ話題で正反対の意見を言うことも

### ストーカー

- 一方的にウォッチ
- 直接絡まないが言及する
- ターゲットの活動を把握している

## 好感度の変動

好感度（affinity）は上がるだけでなく、下がることもある。

### 好感度が上がるイベント

| イベント | 変化量 | 説明 |
|----------|--------|------|
| リプライをもらった | +0.05 | 嬉しい |
| リポストされた | +0.03 | 広めてくれた |
| スターをもらった | +0.02 | 見てくれてる |
| リプライした | +0.02 | 自分から絡んだ |
| 同じ話題で盛り上がった | +0.03 | 共感 |
| 相手の連作に反応した | +0.04 | ちゃんと見てる |

### 好感度が下がるイベント

| イベント | 変化量 | 説明 |
|----------|--------|------|
| 無視された | -0.01 | リプライに返事なし（時間経過で発生） |
| 反応がない期間が長い | -0.02/週 | 疎遠になっていく |
| 意見が対立した | -0.05 | 価値観の相違（稀） |
| 自分の好きなものを批判された | -0.10 | 傷つく（レビューで弾かれるが） |
| 一方的になっている | -0.03 | こちらばかり反応してる |

### 無視による好感度低下

```python
# リプライしたのに返事がない
if sent_reply_to(other) and not received_reply_from(other, within_days=3):
    affinity[self][other] -= 0.01
    feeling = "ちょっと寂しい"
```

### 疎遠による好感度低下

```python
# しばらく交流がない
if last_interaction_with(other) > days(14):
    affinity[self][other] -= 0.02
    # ただし下限あり（初期値以下にはならない）
    affinity[self][other] = max(affinity[self][other], initial_affinity)
```

### 一方的な関係による低下

```python
# 自分ばかり反応している
my_reactions = count_reactions_to(other, days=30)
their_reactions = count_reactions_from(other, days=30)

if my_reactions > their_reactions * 3:  # 3倍以上差がある
    affinity[self][other] -= 0.03
    feeling = "なんか一方的だな…"
```

### 好感度の下限と上限

```python
# 範囲: -1.0 〜 +1.0
MIN_AFFINITY = -1.0  # 完全に嫌い
MAX_AFFINITY = +1.0  # 大好き

# ただし、初期値以下には下がりにくい
# 元々仲良しの設定なら、少し疎遠になっても大きくは下がらない
```

### 好感度による行動変化

| 好感度 | 行動 |
|--------|------|
| 0.7〜1.0 | 積極的に絡む、連作で言及、リプライ確率高 |
| 0.3〜0.6 | 時々リアクション、話題が合えばリプライ |
| 0.0〜0.2 | たまにスター程度 |
| -0.2〜0.0 | 特に絡まない |
| -0.5〜-0.2 | 意図的に避ける |
| -1.0〜-0.5 | ブロック相当（関わらない） |

### 好感度変動の例

```
Day 1: yuki と sora の好感度 = 0.3（知り合い程度）

Day 5: sora が yuki の絵にリプライ
  → yuki の sora への好感度 +0.05 → 0.35

Day 7: yuki が sora にリプライ返し
  → sora の yuki への好感度 +0.05 → 0.35

Day 10: 同じニュースに反応して盛り上がる
  → 互いに +0.03 → 0.38

Day 20: sora が yuki のリプライを無視
  → yuki の sora への好感度 -0.01 → 0.37

Day 30: 交流続く
  → 好感度 0.5 前後に（仲良し）

Day 60: sora が忙しくて反応減る
  → 疎遠補正で徐々に下がる → 0.4 くらいに
```

## プライバシーとNGルール

相互作用でも以下は守る:

- **外部アカウントの個人名は出さない**
  - ストーカーがkako-junの名前を出すのはOK（架空ではないが、アプリ作者として公開情報）
  - ただし本名は出さない

- **ネガティブな絡みは制限**
  - 批判的なリプライはNG
  - 炎上を誘発する引用はNG

- **夫婦の会話も節度を持つ**
  - プライベートすぎる内容は避ける
