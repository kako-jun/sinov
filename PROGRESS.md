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
  - `bots/profiles/reporter_tech.yaml`
  - `bots/profiles/reporter_game.yaml`
  - `bots/profiles/reporter_creative.yaml`
- [x] 収集スクリプト（`scripts/collect_news.py`）

## 未着手

### tickへの相互作用統合
- [ ] 投稿済みエントリーから他住人の投稿を取得
- [ ] 関係性に基づいてリプライ/リアクション判定
- [ ] リプライ内容をLLMで生成
- [ ] キューにリプライエントリーを追加

### 好感度の更新処理
- [ ] リプライをもらったら +0.05
- [ ] リアクションをもらったら +0.02
- [ ] 無視されたら -0.01
- [ ] 疎遠期間で -0.02/週

### 記憶のフィードバック強化
- [ ] 反応をもらったらその話題のstrength上昇
- [ ] 短期記憶から長期記憶への昇格判定

### Nostrリプライ投稿
- [ ] reply_toのevent_idを使ったリプライ投稿
- [ ] リアクション投稿（NIP-25）

### 掲示板ニュース→住人の統合
- [ ] 掲示板ニュースを住人がつぶやきに参照
- [ ] 現在のshared_news.jsonとの統合

### ストーカー機能
- [ ] 外部Nostrアカウントの投稿取得
- [ ] ぶつぶつ（mumble）投稿生成

### 季節イベント
- [ ] events.jsonの作成
- [ ] イベント期間中の話題反映

### 住人100人
- [ ] 残り約75人のプロファイル作成
