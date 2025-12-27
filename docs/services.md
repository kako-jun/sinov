# サービス層

## NpcService

NPC投稿の生成・投稿を担当。

### メソッド

| メソッド | 説明 |
|---------|------|
| `load_bots()` | 全NPCのプロフィール・状態・鍵を読み込み |
| `generate_post_content(npc_id)` | LLMで投稿を生成 |
| `post(npc_id, content)` | Nostrに投稿 |
| `review_content(content)` | LLMでNGルールチェック |

### 投稿生成フロー

1. 連作判定（20%確率で開始）
2. 短期記憶減衰
3. トピック選択
4. プロンプト生成
5. LLM呼び出し（最大3回リトライ）
6. コンテンツ加工（Markdown除去、文字数調整）
7. 文章スタイル適用（誤字、改行、句読点）
8. 記憶更新
9. キューに追加

## InteractionService

NPC間の相互作用を処理。

### メソッド

| メソッド | 説明 |
|---------|------|
| `process_interactions(target_npc_ids)` | リプライ・リアクション生成 |
| `process_reply_chains(target_npc_ids)` | スレッド内返信処理 |
| `process_affinity_decay()` | 好感度減衰 |
| `process_ignored_posts()` | 無視された投稿の処理 |

### 相互作用判定

1. 自分自身の投稿は除外
2. 避ける関係は除外
3. リプライ確率を計算
   - ベース確率: 関係性から取得
   - 好感度調整: >0.7で1.3倍、<0.3で0.7倍
   - 社交性調整: 0.5+sociability倍
4. 判定実行

### 会話チェーン

深さに応じて無視確率が上昇:

| 深さ | 無視確率 |
|------|----------|
| 1 | 10% |
| 2 | 30% |
| 3 | 60% |
| 4 | 85% |
| 5+ | 95% |

## ExternalReactionService

外部ユーザー投稿への反応を処理。

### メソッド

| メソッド | 説明 |
|---------|------|
| `process_external_reactions(target_npc_ids, max_posts_per_bot)` | 外部投稿に反応 |

### 処理フロー

1. MYPACE APIからタイムライン取得（50件）
2. 内部NPC投稿をフィルタ
3. 興味が合致する投稿を選定
4. リプライまたはいいねを生成

## AffinityService

好感度・親密度・気分を管理。

### メソッド

| メソッド | 説明 |
|---------|------|
| `update_on_interaction(from_id, to_id, type)` | 相互作用時の更新 |
| `process_decay(target_ids, npcs)` | 週次減衰 |
| `process_ignored_posts(target_ids)` | 無視時の減衰 |

### 更新量

| 相互作用 | 好感度 | 親密度 | 気分 |
|---------|--------|--------|------|
| リプライ | +0.05 | +0.03 | +0.1 |
| リアクション | +0.02 | +0.01 | +0.05 |
| 無視 | -0.01 | - | - |
| 週次減衰 | -0.02 | - | - |

## StalkerService

ストーカー機能を処理。

### メソッド

| メソッド | 説明 |
|---------|------|
| `process_stalking(target_npc_ids)` | ストーカー行動を実行 |

### 処理フロー

1. ストーカー設定を読み込み
2. ターゲットの投稿を取得
3. 確率に基づいてリアクション生成
4. ぶつぶつ言及（引用なし）を生成

## ServiceFactory

依存関係を注入してサービスを構築。

```python
factory = ServiceFactory(settings, llm_provider)
npc_service = factory.create_npc_service()
interaction_service = factory.create_interaction_service()
```
