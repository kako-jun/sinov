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

詳細は [content-generation.md](content-generation.md) を参照。

## InteractionService

NPC間の相互作用を処理。

### メソッド

| メソッド | 説明 |
|---------|------|
| `process_interactions(target_npc_ids)` | リプライ・リアクション生成 |
| `process_reply_chains(target_npc_ids)` | スレッド内返信処理 |
| `process_affinity_decay()` | 好感度減衰 |
| `process_ignored_posts()` | 無視された投稿の処理 |

### 詳細

リプライ確率、会話チェーン、好感度システムの詳細は [interaction.md](interaction.md) を参照。

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

更新量の詳細は [interaction.md](interaction.md) の「好感度システム」を参照。

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
