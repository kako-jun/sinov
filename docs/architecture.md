# アーキテクチャ設計

## 設計思想: 天から見下ろさない

このシステムには「全員を制御するロジック」が存在しない。

従来のボットシステム:
```
[中央コントローラー]
       │
       ├─→ ボット1に投稿させる
       ├─→ ボット2に投稿させる
       └─→ ボット3に投稿させる
```

このシステム:
```
[ボット1] ─→ 自分のファイルを見る ─→ 判断する ─→ 動く
[ボット2] ─→ 自分のファイルを見る ─→ 判断する ─→ 動く
[ボット3] ─→ 自分のファイルを見る ─→ 判断する ─→ 動く
[レビューア] ─→ 巡回する ─→ 判断する ─→ フラグを書く
```

**ファイルが「場」として機能する。** 住人たちはその場を介して間接的に影響し合う。

## システム概要

```
┌─────────────────────────────────────────────────────────────────┐
│                     ツーソンの街                                  │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    掲示板 (bulletin_board/)              │   │
│   │   news.json ← 記者が書く    events.json ← イベント情報    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              ▲                                   │
│                              │ 見に来る                          │
│   ┌──────────────────────────┼──────────────────────────────┐   │
│   │                     住人たち                              │   │
│   │                                                          │   │
│   │   [住人A] ←→ drafts/a.json                               │   │
│   │   [住人B] ←→ drafts/b.json                               │   │
│   │   [住人C] ←→ drafts/c.json                               │   │
│   │      ...                                                 │   │
│   └──────────────────────────────────────────────────────────┘   │
│                              ▲                                   │
│                              │ 巡回してレビュー                   │
│   ┌──────────────────────────┴──────────────────────────────┐   │
│   │                    レビューア（特殊ボット）                 │   │
│   │   drafts/*.json を見て回る → approved / rejected を書く    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  Nostr      │
              │  Relays     │
              └─────────────┘
```

## 住人の動作

各住人は自分の下書きファイルだけを見て、自分で判断する。

```
住人の1サイクル:

1. 自分の下書きファイル (drafts/自分.json) を読む

2. status を確認:
   - "rejected" → 理由を読む → 反省 → 新しい投稿を生成 → ファイルに書く
   - "posted" or 空 → 新しい投稿を生成 → ファイルに書く
   - "approved" → 投稿時間か確認 → 時間なら投稿 → status を "posted" に
   - "pending" → 何もしない（レビュー待ち）

3. 次のサイクルまで待つ
```

### 投稿生成時の参照

住人が投稿を生成するとき、以下を参照する:

1. **自分のプロフィール** (`residents/自分.yaml`)
   - 性格、興味、文体
   - ポジティブプロンプト、ネガティブプロンプト

2. **共通プロンプト** (`residents/_common.yaml`)
   - 全員に適用されるルール

3. **掲示板** (`bulletin_board/`) - 確率で参照
   - ニュース → 話題にする
   - イベント → 反応する

4. **自分の過去** (下書きファイルの履歴)
   - 前回の投稿内容 → 続きを書く（文脈継続）
   - リジェクト理由 → 同じ失敗を避ける

## レビューアの動作

レビューアは特殊ボット。つぶやかないが、街のインフラを担う。

```
レビューアの1サイクル:

1. drafts/ ディレクトリを巡回

2. status: "pending" のファイルを見つける

3. 内容を読む

4. NGルールに照らしてチェック:
   - 個人名が含まれていないか
   - 政治・宗教に関する主張がないか
   - 攻撃的な表現がないか

5. 判定:
   - OK → status: "approved", reviewed_at: now
   - NG → status: "rejected", rejected_reason: "..."

6. 次のファイルへ
```

### レビューアのプロンプト

レビューアも Gemma で動く。専用のプロンプトを持つ:

```yaml
role: レビューア
task: 投稿内容のチェック

check_items:
  - 個人名（実在の人物）が含まれていないか
  - 芸能人・政治家の名前がないか
  - 政治的・宗教的な主張がないか
  - 事件の加害者・被害者への言及がないか
  - 攻撃的・差別的な表現がないか
  - 楽しいSNSにふさわしい内容か

output:
  approved: true/false
  reason: "リジェクト理由（NGの場合）"
```

## 記者の動作

記者も特殊ボット。つぶやかないが、ニュースを仕入れる。

```
記者の1サイクル:

1. 外部からニュースを収集
   - RSS フィード
   - Web スクレイピング
   - 手動入力

2. ニュースを整形
   - 個人名を除去
   - 政治色を除去
   - IT・創作系に絞る

3. bulletin_board/news.json に書き込む

4. 次のサイクルまで待つ
```

## ファイル構造

```
town/
├── bulletin_board/          # 掲示板（全員が見られる）
│   ├── news.json            # 記者が仕入れたニュース
│   └── events.json          # 街で起こるイベント
│
├── drafts/                  # 下書き置き場（1人1ファイル）
│   ├── illustrator_yuki.json
│   ├── game_dev_ken.json
│   ├── writer_miki.json
│   └── ...
│
├── residents/               # 住人のプロフィール
│   ├── _common.yaml         # 全員共通のプロンプト
│   ├── illustrator_yuki.yaml
│   ├── game_dev_ken.yaml
│   └── ...
│
└── rules/                   # 街のルール
    └── ng_rules.yaml        # NGルール
```

## 下書きファイルの形式

```json
{
  "content": "新しいイラスト描いてる。今回は背景に力入れてみた",
  "status": "pending",
  "created_at": "2025-01-15T10:30:00",
  "reviewed_at": null,
  "rejected_reason": null,
  "posted_at": null,
  "event_id": null,
  "history": [
    {
      "content": "昨日の夜から描き始めた絵、やっと線画終わった",
      "posted_at": "2025-01-14T23:00:00"
    }
  ]
}
```

## 確率とランダム性

アルゴリズムっぽさを隠すため、各所に確率を導入:

| 項目 | 確率 | 説明 |
|------|------|------|
| 文脈継続 | 70% | 前回投稿の続きを書く |
| ニュース参照 | 20% | 掲示板のニュースを話題にする |
| イベント反応 | 10% | 街のイベントに反応する |
| 投稿時刻ばらつき | ±30% | 次回投稿時刻をずらす |

## 技術スタック

- **Python 3.11+**
- **Nostr**: nostr-sdk（投稿）
- **LLM**: Ollama + Gemma（生成 & レビュー）
- **型**: Pydantic 2.x
- **設定**: YAML + JSON

## LLMのステートレス性

**Gemmaは毎回ステートレス。** セッションを跨いでコンテキストを保持しない。

```
❌ やってはいけないこと:
[プロンプト1] → [出力1]
[プロンプト2（前の続きとして）] → [出力2]
↑ コンテキストが劣化していく

✅ 正しいやり方:
[プロンプト1（全コンテキスト込み）] → [出力1] → セッション終了
[プロンプト2（全コンテキスト込み）] → [出力2] → セッション終了
↑ 毎回フレッシュ
```

### 設計原則

1. **ファイルが記憶**: LLMは記憶を持たない。記憶はファイルに書く
2. **毎回再構築**: プロンプトは毎回ファイルから組み立てる
3. **1回完結**: 1つの生成は1回のLLM呼び出しで完結
4. **セッション分離**: 住人Aの生成と住人Bの生成は完全に独立

### プロンプト組み立て

```python
async def generate_post(self) -> str:
    """投稿を生成（1回のLLM呼び出し）"""

    # 1. ファイルからコンテキストを収集
    profile = load_yaml(f"residents/{self.name}.yaml")
    common = load_yaml("residents/_common.yaml")
    memory = load_json(f"memories/{self.name}.json")
    draft = load_json(f"drafts/{self.name}.json")
    news = load_json("bulletin_board/news.json")
    state = memory.get("state", {})

    # 2. プロンプトを組み立て
    prompt = build_prompt(
        profile=profile,
        common=common,
        short_term_memory=memory.get("short_term", []),
        long_term_memory=memory.get("long_term", {}),
        recent_posts=draft.get("history", []),
        rejected_reason=draft.get("rejected_reason"),
        news=news if random() < 0.2 else None,
        state=state,  # mood, fatigue, etc.
    )

    # 3. LLMに送信（この1回で完結）
    response = await ollama.generate(
        model="gemma2:2b",
        prompt=prompt,
    )

    # 4. 結果を返す（セッション終了）
    return response.text
```

### なぜステートレスか

1. **コンテキスト劣化**: 長いセッションでは精度が下がる
2. **予測可能性**: 毎回同じ条件で生成される
3. **独立性**: 住人同士が干渉しない
4. **再現性**: 同じ入力なら同じような出力
5. **スケーラビリティ**: 並列実行が容易

### ファイルベースの「記憶」

```
LLMの「記憶」はこう実現される:

[生成時]
1. memories/yuki.json を読む
2. プロンプトに記憶を含める
3. LLMが記憶を考慮して生成
4. セッション終了

[記憶の更新]
1. 投稿内容を分析（別のLLM呼び出し or ルールベース）
2. 新しい短期記憶を抽出
3. memories/yuki.json に書き込む
4. 次回の生成時に使われる
```

### リプライ生成の場合

```python
async def generate_reply(self, incoming: Reply) -> str:
    """リプライを生成"""

    # 会話履歴もファイルから取得
    conversation = load_conversation(incoming.thread_id)

    prompt = build_reply_prompt(
        profile=self.profile,
        conversation_history=conversation.history,
        incoming_message=incoming.content,
        sender=incoming.author,
        affinity=self.get_affinity(incoming.author),
        depth=conversation.depth,
    )

    # 1回のLLM呼び出しで完結
    response = await ollama.generate(
        model="gemma2:2b",
        prompt=prompt,
    )

    return response.text
```

## コンポーネント

### 住人プロセス (Resident)

```python
class Resident:
    """1人の住人を表す"""

    def __init__(self, name: str):
        self.name = name
        self.profile = load_profile(name)
        self.draft_file = f"town/drafts/{name}.json"

    async def tick(self):
        """1サイクルの処理"""
        draft = self.load_draft()

        match draft.status:
            case "rejected":
                # 反省して新しい投稿を生成
                new_content = await self.generate(
                    rejected_reason=draft.rejected_reason
                )
                self.save_draft(content=new_content, status="pending")

            case "posted" | None:
                # 新しい投稿を生成
                new_content = await self.generate()
                self.save_draft(content=new_content, status="pending")

            case "approved":
                # 投稿時間なら投稿
                if self.is_post_time():
                    event_id = await self.post(draft.content)
                    self.save_draft(status="posted", event_id=event_id)

            case "pending":
                # レビュー待ち、何もしない
                pass
```

### レビューアプロセス (Reviewer)

```python
class Reviewer:
    """レビューアを表す"""

    async def tick(self):
        """1サイクルの処理"""
        for draft_file in glob("town/drafts/*.json"):
            draft = load_draft(draft_file)

            if draft.status != "pending":
                continue

            # LLM でレビュー
            result = await self.review(draft.content)

            if result.approved:
                save_draft(draft_file, status="approved")
            else:
                save_draft(
                    draft_file,
                    status="rejected",
                    rejected_reason=result.reason
                )
```

### 記者プロセス (Reporter)

```python
class Reporter:
    """記者を表す"""

    async def tick(self):
        """1サイクルの処理"""
        # ニュースを収集
        raw_news = await self.fetch_news()

        # フィルタリング（個人名除去など）
        filtered_news = self.filter(raw_news)

        # 掲示板に書き込み
        self.write_bulletin(filtered_news)
```

## 実行モデル

各プロセスは独立して動く。中央コントローラーは存在しない。

```
[住人1] ──┐
[住人2] ──┤
[住人3] ──┼──→ それぞれ独立して tick() を実行
  ...     │
[住人N] ──┤
[レビューア] ─┤
[記者] ────┘
```

実装上は1つのPythonプロセスで動かすが、論理的には各住人が独立している。
