# 心理学からの知見

キャラクター設計に使える、心理学で確立された概念。

## ビッグファイブ（OCEAN）

最も科学的に支持されている性格モデル。5つの次元で性格を表す。

| 因子 | 英語 | 高い | 低い | 現パラメータとの対応 |
|------|------|------|------|---------------------|
| 開放性 | Openness | 好奇心旺盛、創造的 | 保守的、実用主義 | `curiosity`, `creativity` |
| 誠実性 | Conscientiousness | 計画的、自己規律 | 衝動的、柔軟 | `persistence` |
| 外向性 | Extraversion | 社交的、活動的 | 内向的、静か | `sociability`, `activeness` |
| 協調性 | Agreeableness | 協力的、信頼 | 競争的、懐疑的 | （新規追加候補） |
| 神経症傾向 | Neuroticism | 不安、情緒不安定 | 安定、冷静 | `sensitivity`（逆向き） |

### 追加候補: 協調性 (agreeableness)

```yaml
# 現状カバーされていない
agreeableness:
  high: 人を信じやすい、協力的、争いを避ける
  low: 懐疑的、競争的、自己主張が強い
```

```yaml
# 高協調性キャラ
name: gentle_artist
traits:
  agreeableness: 0.9
  contrarian: 0.1

# 発言例:
# 「それもいいと思う！」
# 「みんなすごいなあ」
# 「争いは嫌だな…」
```

```yaml
# 低協調性キャラ
name: competitive_dev
traits:
  agreeableness: 0.2
  contrarian: 0.6

# 発言例:
# 「いや、それは違うと思う」
# 「自分のやり方でやる」
# 「負けたくない」
```

## 愛着スタイル（Attachment Style）

人が他者と関係を築くパターン。幼少期の経験で形成される。

| スタイル | 特徴 | 発言例 |
|----------|------|--------|
| 安定型 | 信頼できる、適度な距離感 | 「いつもありがとう」 |
| 不安型 | 見捨てられ不安、過剰に求める | 「返事まだかな…」「嫌われた？」 |
| 回避型 | 親密さを避ける、自立志向 | 「一人で大丈夫」「深入りしない」 |
| 混乱型 | 矛盾した行動、近づきたいけど怖い | 日によって態度が変わる |

### パラメータ化

```yaml
attachment_style:
  type: anxious  # secure / anxious / avoidant / disorganized
  intensity: 0.7  # どの程度強いか

# 不安型キャラ
name: anxious_illustrator
attachment_style:
  type: anxious
  intensity: 0.8

# 発言例:
# 「リプライ来ないな…何かまずかったかな」
# 「みんな楽しそうでいいな」
# 「私のこと覚えてるかな」
```

## マズローの欲求階層

人の行動の動機を5段階で説明。下の欲求が満たされると上に移行。

```
    ┌────────────────┐
    │  自己実現欲求   │ ← 創作、表現、成長
    ├────────────────┤
    │   承認欲求     │ ← いいね、フォロワー、評価
    ├────────────────┤
    │   所属欲求     │ ← コミュニティ、仲間、グループ
    ├────────────────┤
    │   安全欲求     │ ← 収入、安定、健康
    ├────────────────┤
    │   生理的欲求   │ ← 睡眠、食事
    └────────────────┘
```

### パラメータ化: 主な動機

```yaml
primary_motivation:
  type: self_actualization  # 何を最も求めているか
  # 選択肢:
  # - self_actualization: 自己実現（創作そのもの）
  # - recognition: 承認（いいね、評価）
  # - belonging: 所属（仲間、コミュニティ）
  # - security: 安全（収入、安定）
  # - survival: 生存（とにかく生きる）
```

```yaml
# 自己実現型（創作そのものが目的）
name: pure_creator
primary_motivation: self_actualization
traits:
  feedback_sensitivity: 0.2  # 反応気にしない

# 発言例:
# 「描きたいから描いてる」
# 「評価より自分が満足できるかが大事」
```

```yaml
# 承認欲求型
name: approval_seeker
primary_motivation: recognition
traits:
  feedback_sensitivity: 0.9

# 発言例:
# 「今日の投稿、反応どうかな」
# 「フォロワー増えた！嬉しい」
# 「なんで伸びないんだろう…」
```

## 認知バイアス

人間の思考の「クセ」。キャラに適用すると人間らしくなる。

### 使いやすいバイアス

| バイアス | 説明 | 発言例 |
|----------|------|--------|
| 確証バイアス | 自分の信念を支持する情報だけ集める | 「やっぱり〇〇が正しい」 |
| サンクコスト | 投資した分を取り戻そうとする | 「ここまでやったし…」 |
| ダニング・クルーガー | 初心者ほど自信過剰 | 「これ簡単じゃん」（初心者） |
| インポスター症候群 | 能力あるのに自信がない | 「運が良かっただけ」（上級者） |
| 可用性ヒューリスティック | 思い出しやすい例で判断 | 「最近〇〇多いよね」（実際は普通） |
| 後知恵バイアス | 結果を見て「わかってた」 | 「やっぱりこうなると思った」 |

### パラメータ化

```yaml
cognitive_biases:
  dunning_kruger: 0.7  # 高いと初心者なのに自信
  impostor: 0.8        # 高いと上級者なのに自信ない
  confirmation: 0.6    # 高いと自分の意見に固執
  sunk_cost: 0.5       # 高いと諦めが悪い
```

```yaml
# ダニング・クルーガー効果（初心者の自信）
name: overconfident_beginner
traits:
  expertise: 0.2       # 初心者
  dunning_kruger: 0.8  # でも自信満々

# 発言例:
# 「これ余裕でしょ」
# 「なんでみんな難しいって言うんだろ」
# 「俺ならもっとうまくやれる」
```

```yaml
# インポスター症候群（上級者の不安）
name: humble_expert
traits:
  expertise: 0.9       # 熟練者
  impostor: 0.8        # でも自信ない

# 発言例:
# 「まだまだ勉強中です」
# 「たまたまうまくいっただけ」
# 「自分なんかがアドバイスしていいのか」
```

## ローカス・オブ・コントロール（統制の所在）

出来事の原因を自分に求めるか、外部に求めるか。

| タイプ | 特徴 | 発言例 |
|--------|------|--------|
| 内的統制 | 自分次第、努力で変わる | 「もっと頑張ろう」「自分のせい」 |
| 外的統制 | 環境や運のせい、自分では変えられない | 「運が悪い」「時代が悪い」 |

```yaml
locus_of_control:
  internal: 0.7  # 高いと内的（自己責任思考）
                 # 低いと外的（環境のせい思考）
```

```yaml
# 内的統制キャラ
name: self_driven
locus_of_control:
  internal: 0.9

# 発言例:
# 「結果は自分次第」
# 「言い訳はしない」
# 「できないのは努力が足りない」（他人にも厳しい）
```

```yaml
# 外的統制キャラ
name: unlucky_artist
locus_of_control:
  internal: 0.2

# 発言例:
# 「運がないんだよなあ」
# 「アルゴリズムのせいで伸びない」
# 「時代が悪い」
```

## 制御焦点理論（Regulatory Focus）

目標達成のアプローチスタイル。

| タイプ | 特徴 | 発言例 |
|--------|------|--------|
| 促進焦点 | 利益を得ようとする、挑戦的 | 「やってみよう！」「チャンス！」 |
| 予防焦点 | 損失を避けようとする、慎重 | 「失敗したくない」「リスクは避けたい」 |

```yaml
regulatory_focus:
  promotion: 0.7  # 高いと促進焦点（攻め）
                  # 低いと予防焦点（守り）
```

## クロノタイプ（体内時計の型）

生物学的な活動リズム。性格というより体質。

| タイプ | 特徴 | 活動時間 |
|--------|------|----------|
| 朝型（ひばり） | 早起き、午前がピーク | 5:00-21:00 |
| 夜型（ふくろう） | 遅寝遅起き、夜がピーク | 12:00-4:00 |
| 中間型 | 一般的なリズム | 7:00-23:00 |

```yaml
chronotype:
  type: owl  # lark / owl / intermediate
  intensity: 0.8

# 発言例（夜型）:
# 「3時だけど絶好調」
# 「午前中は人権がない」
# 「みんな朝から元気だな…」
```

## フロー状態

完全に没頭している状態。挑戦と技術のバランスで発生。

```
        挑戦度
          ↑
      不安│     フロー
          │   ／
          │ ／
      退屈│───────→ 技術
```

### パラメータとして

```yaml
# focus（集中度）の拡張として
state:
  flow_tendency: 0.7  # フローに入りやすさ（固定特性）
  current_flow: 0.8   # 現在のフロー状態（変動）

# フローに入りやすいキャラ
# 発言例:
# 「気づいたら5時間経ってた」
# 「作業中は時間感覚なくなる」
```

## 社会的比較

他者と自分を比較する傾向。

| 方向 | 対象 | 効果 |
|------|------|------|
| 上方比較 | 自分より上の人 | 動機づけ or 落ち込み |
| 下方比較 | 自分より下の人 | 安心 or 優越感 |

```yaml
social_comparison:
  tendency: 0.8       # 比較しやすさ（高いと比較しがち）
  direction: upward   # upward / downward / balanced
  effect: negative    # positive（刺激になる）/ negative（落ち込む）
```

```yaml
# 比較して落ち込むキャラ
name: comparison_victim
social_comparison:
  tendency: 0.9
  direction: upward
  effect: negative

# 発言例:
# 「〇〇さんすごいなあ…自分なんて」
# 「同期なのにあの人は…」
# 「才能の差を感じる」
```

## ヘドニック・アダプテーション（快楽適応）

良いことにも悪いことにも慣れる。

```yaml
hedonic_adaptation:
  rate: 0.7  # 高いとすぐ慣れる（感動が薄れやすい）
             # 低いと慣れにくい（喜びも悲しみも長続き）
```

```yaml
# 慣れにくいキャラ（感動し続ける）
name: always_amazed
hedonic_adaptation:
  rate: 0.2

# 発言例:
# 「まだあの時の嬉しさ思い出す」
# 「何度見ても感動する」
```

## 自己効力感（Self-Efficacy）

「自分にはできる」という信念。intelligenceやexpertiseとは別。

```yaml
self_efficacy:
  general: 0.6    # 全般的な自信
  domain:         # 分野別の自信
    illustration: 0.8
    programming: 0.3
    social: 0.4
```

```yaml
# 自己効力感が低いが能力は高い
name: capable_but_unsure
traits:
  expertise: 0.8
  self_efficacy: 0.3

# 発言例:
# 「できるかな…」（実際はできる）
# 「自分にできるか不安」
# 「失敗しそう」（失敗しない）
```

## 感情労働（Emotional Labor）

感情を管理・演技する負担。SNSでは特に関係。

```yaml
emotional_labor:
  public_persona: 0.8  # 外向けの自分と本当の自分の乖離
  burnout_risk: 0.6    # 疲弊しやすさ

# 発言例（public_personaが高い）:
# 表: 「今日も頑張ろう！」（いつもポジティブ）
# 裏: 「疲れた…」（たまに本音が漏れる）
```

## 既存パラメータへのマッピング

| 心理学概念 | 既存パラメータ | 追加候補 |
|------------|----------------|----------|
| ビッグファイブ 開放性 | curiosity, creativity | - |
| ビッグファイブ 誠実性 | persistence | - |
| ビッグファイブ 外向性 | sociability, activeness | - |
| ビッグファイブ 協調性 | - | `agreeableness` |
| ビッグファイブ 神経症傾向 | sensitivity | - |
| 愛着スタイル | - | `attachment_style` |
| マズロー欲求 | feedback_sensitivity | `primary_motivation` |
| 認知バイアス | - | `cognitive_biases` |
| 統制の所在 | - | `locus_of_control` |
| 制御焦点 | optimism（近い） | `regulatory_focus` |
| クロノタイプ | active_hours | `chronotype` |
| 社会的比較 | - | `social_comparison` |
| 自己効力感 | expertise + impostor | `self_efficacy` |

## 推奨: 追加すべきパラメータ

優先度順:

1. **agreeableness（協調性）**: ビッグファイブの欠落、人間関係に大きく影響
2. **locus_of_control（統制の所在）**: 発言の責任帰属に影響
3. **self_efficacy（自己効力感）**: 挑戦・回避行動に影響
4. **attachment_style（愛着スタイル）**: 対人関係の質に影響
5. **social_comparison（社会的比較）**: SNSで特に顕著

## 参考文献

- Costa, P. T., & McCrae, R. R. (1992). NEO-PI-R Professional Manual. (ビッグファイブ)
- Bowlby, J. (1969). Attachment and Loss. (愛着理論)
- Maslow, A. H. (1943). A Theory of Human Motivation. (欲求階層)
- Kahneman, D. (2011). Thinking, Fast and Slow. (認知バイアス)
- Bandura, A. (1977). Self-efficacy. (自己効力感)
- Csikszentmihalyi, M. (1990). Flow. (フロー理論)
