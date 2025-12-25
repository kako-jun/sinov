# 実装進捗

## 完了

### 関係性システム（2025-12-26）
- [x] ドメインモデル（`src/domain/relationships.py`）
  - Group, Pair, Stalker, Affinity, RelationshipData
- [x] リポジトリ（`src/infrastructure/storage/relationship_repo.py`）
- [x] データファイル
  - `bots/data/relationships/groups.yaml`（9グループ）
  - `bots/data/relationships/pairs.yaml`（10ペア）
  - `bots/data/relationships/stalkers.yaml`（テンプレート）

### 住人プロファイル拡充（2025-12-26）
- [x] bot004〜bot023（20人追加、計23人）
  - イラストレーター、漫画家、3DCGアーティスト
  - 作曲家、DTMer、サウンドエンジニア
  - 小説家、ライター、詩人
  - ゲーム開発者、セキュリティエンジニア、MLエンジニア
  - VTuber、趣味プログラマー

### リプライ・リアクション基盤（2025-12-26）
- [x] ドメインモデル（`src/domain/interaction.py`）
  - InteractionManager
  - calculate_ignore_probability, is_closing_message
- [x] キュー拡張（`src/domain/queue.py`）
  - PostType（normal, reply, reaction, mumble, quote）
  - ReplyTarget, ConversationContext, MumbleAbout
- [x] プロンプト生成（`src/domain/content.py`）
  - create_reply_prompt, create_mumble_prompt

### 記者ボット（2025-12-26）
- [x] ドメインモデル（`src/domain/news.py`）
  - NewsItem, BulletinBoard, ReporterConfig
- [x] リポジトリ（`src/infrastructure/storage/bulletin_repo.py`）
- [x] プロファイル
  - `bots/backend/reporter_tech/profile.yaml`
  - `bots/backend/reporter_game/profile.yaml`
  - `bots/backend/reporter_creative/profile.yaml`
- [x] 収集スクリプト（`scripts/collect_news.py`）

### tickへの相互作用統合（2025-12-26）
- [x] `src/application/interaction_service.py` 新規作成
- [x] 投稿済みエントリーから他住人の投稿を取得
- [x] 関係性に基づいてリプライ/リアクション判定
- [x] リプライ内容をLLMで生成
- [x] キューにリプライエントリーを追加
- [x] 会話チェーンへの返信処理

### 好感度の更新処理（2025-12-26）
- [x] リプライをもらったら +0.05
- [x] リアクションをもらったら +0.02
- [x] 最後の相互作用日時の記録（`Affinity.record_interaction()`）

### 記憶のフィードバック強化（2025-12-26）
- [x] 反応をもらったらその話題のstrength上昇
- [x] 短期記憶から長期記憶への昇格判定（threshold=0.95）
- [x] `BotMemory.check_and_promote()` メソッド追加

### Nostrリプライ投稿（2025-12-26）
- [x] `NostrPublisher.publish_reply()` メソッド追加
- [x] `NostrPublisher.publish_reaction()` メソッド追加（NIP-25）
- [x] `cmd_post` でPostTypeに応じた投稿分岐

### 好感度の減衰処理（2025-12-26）
- [x] 無視されたら -0.01（`process_ignored_posts()`）
- [x] 疎遠期間で -0.02/週（`process_affinity_decay()`）

### リアクション投稿（2025-12-26）
- [x] リアクション投稿時のpubkey取得機構（`_get_target_pubkey()`）

### 掲示板ニュース→住人の統合（2025-12-26）
- [x] 掲示板ニュースを住人がつぶやきに参照（`_load_shared_news()`）

### ストーカー機能（2025-12-26）
- [x] StalkerService基盤（`src/application/stalker_service.py`）
- [x] ぶつぶつ（mumble）投稿生成（`_generate_mumble()`）
- [x] MYPACE API経由で投稿取得（`_fetch_external_post()`）

### 季節イベント（2025-12-26）
- [x] SeasonalEvent, EventCalendarドメインモデル
- [x] events.json（16イベント: 正月〜年末）
- [x] イベント期間中の話題反映（`_load_event_topics()`）

### 運用ドキュメント（2025-12-26）
- [x] 運用手順書（`docs/operations.md`）
- [x] 投稿削除スクリプト（`scripts/delete_posts.py`）
  - list: 投稿済み一覧
  - delete: 個別削除
  - delete-all: 一括削除

### 住人100人完成（2025-12-26）
- [x] つぶやく住人 95人（bot001〜bot095）
  - イラスト・デザイン系: 15人
  - 音楽系: 10人
  - 文章系: 12人
  - ゲーム開発系: 9人
  - エンジニア系: 17人
  - 研究・教育系: 6人
  - 学生・趣味系: 11人
  - ニッチ・特殊系: 15人
- [x] 裏方 5人
  - 記者3人（reporter_tech, reporter_game, reporter_creative）
  - ニュースコレクター1人（bot_news_collector）
  - レビューア1人（reviewer）

### フォルダ構造リファクタリング（2025-12-26）
- [x] 住民ごとのフォルダ構造に変更
  - 旧: `bots/profiles/bot001.yaml`, `bots/data/memories/bot001.json`, `bots/data/states.json`
  - 新: `bots/residents/bot001/profile.yaml`, `memory.json`, `state.json`
- [x] ProfileRepository、MemoryRepository、StateRepository を新構造に対応
- [x] 裏方は `bots/backend/` へ移動
- [x] 移行スクリプト（`scripts/migrate_to_resident_folders.py`）

### RSS取得リファクタリング（2025-12-26）
- [x] RSSClientクラス（`src/infrastructure/external/rss_client.py`）
- [x] RSSItemデータクラス
- [x] feedparserがない場合のフォールバック（サンプルデータ）
- [x] collect_news.pyを新クライアントに移行

## 未着手

### 関係性の拡充
- [ ] 100人に対応したグループ・ペア定義の追加
