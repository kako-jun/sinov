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
  - 記者4人（reporter_tech, reporter_game, reporter_creative, reporter_general）
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

### コードベースリファクタリング（2025-12-26）
- [x] ボットIDユーティリティ（`src/domain/bot_utils.py`）
  - `format_bot_name()`: ID→名前変換（14箇所の重複を解消）
  - `extract_bot_id()`: 名前→ID変換（3箇所の重複を解消）
- [x] ベースリポジトリ（`src/infrastructure/storage/base_repo.py`）
  - `ResidentJsonRepository`: JSON操作の共通化
  - MemoryRepository, StateRepositoryが継承
- [x] 設定の拡充（`src/config/settings.py`）
  - `AffinitySettings`: 好感度変動値（delta_reply, delta_reaction等）
  - `MemorySettings`: 記憶関連（max_short_term, promotion_threshold等）
  - `ContentSettings.series_start_probability`: 連作開始確率

### プロンプトシステム（2025-12-26 完了）
- [x] 共通プロンプト（`bots/_common.yaml`）の作成
  - positive: 6件（日本語、カジュアル口語体、140文字以内、創作・技術中心）
  - negative: 12件（個人名禁止、政治・宗教禁止、マークダウン禁止）
- [x] 各住人のpositive/negativeプロンプト追加
  - `src/domain/models.py`: `Prompts`クラス追加
  - profile.yamlに `prompts.positive`, `prompts.negative` フィールド追加
  - 職業・性格に応じた個別指示
- [x] プロンプト生成時に共通+個人プロンプトをマージする処理
  - `ProfileRepository.get_merged_prompts()`
  - `ContentStrategy.create_prompt(merged_prompts=...)`

### 性格パラメータシステム（2025-12-26 完了）
- [x] 詳細な性格パラメータ（11種、0.0〜1.0）の実装
  - `PersonalityTraits`クラス（`src/domain/models.py`）
  - activeness, curiosity, sociability, sensitivity, optimism
  - creativity, persistence, expressiveness, expertise, intelligence
  - feedback_sensitivity
- [x] BotProfileモデルの拡張
  - `traits_detail: PersonalityTraits | None`
- [x] 性格パラメータに基づく行動確率の調整
  - sociabilityが高い→リプライ確率UP（`InteractionManager.should_react_to_post`）
  - feedback_sensitivityが高い→反応もらうとstrength大きく上昇（`BotMemory.reinforce_short_term`）

### 文体・習慣システム（2025-12-26 完了）
- [x] 文体スタイル（style）の実装
  - `StyleType`列挙型: normal, ojisan, young, 2ch, otaku, polite, terse
  - `STYLE_DESCRIPTIONS`辞書でプロンプト指示
- [x] 特殊な習慣（habits）の実装
  - `HabitType`列挙型: news_summarizer, emoji_heavy, tip_sharer, wip_poster, question_asker, self_deprecating, enthusiastic
  - `HABIT_DESCRIPTIONS`辞書でプロンプト指示
- [x] プロンプト生成時にstyle/habitsを反映
  - `ContentStrategy._get_style_instruction()`
  - `ContentStrategy._get_habit_instructions()`
- [x] 95人分のプロファイル更新スクリプト
  - `scripts/update_profiles.py`

### 興味・嗜好の詳細化（2025-12-26 完了）
- [x] interests構造の拡張（`src/domain/models.py` `Interests`クラス）
  - 既存: topics, keywords, code_languages
  - 追加: likes（カテゴリ別好み）、dislikes（カテゴリ別嫌い）、values（価値観）
  - 例: likes: {"manga": ["チェンソーマン"]}、dislikes: {"os": ["Windows"]}、values: ["収益化"]
- [x] プロンプト生成時に反映（`ContentStrategy._get_preferences_context()`）

### 関係性パラメータの拡張（2025-12-26 完了）
- [x] trust（信頼度）の実装
  - `Affinity.trust`、`get_trust()`、`update_trust()`
- [x] familiarity（親密度）の実装
  - `Affinity.familiarity`、`get_familiarity()`、`update_familiarity()`
  - 相互作用時に双方の親密度が上昇
- [x] mood（気分）の実装
  - `BotState.mood`（-1.0〜1.0）
  - 反応をもらうと気分が上昇
- [x] これらのパラメータに基づく相互作用の調整
  - `AffinitySettings` に familiarity/mood 変動値を追加
  - `AffinityService.update_on_interaction()` で親密度を更新
  - `InteractionService._update_mood_on_feedback()` で気分を更新

### 記者の追加（2025-12-26 完了）
- [x] reporter_general（一般時事記者）の追加
  - `bots/backend/reporter_general/profile.yaml`
  - はてブ総合、Yahoo!ニュースITをソースに
  - IT・創作関連のキーワードでフィルター
  - 政治・事件・炎上を除外

### reject時の反省機能（2025-12-26 完了）
- [x] rejectされた投稿の理由を次回生成に反映
  - `QueueRepository.get_recent_rejected()` で過去のrejectを取得
  - `BotService._load_rejected_posts()` で変換
  - `ContentStrategy._get_rejection_feedback()` でプロンプトに反映
  - 最新2件のNG例と理由をプロンプトに含める

### 活動ログシステム（2025-12-26 完了）
- [x] 日報形式のログ（作者確認用、LLM入力には使わない）
  - `src/domain/activity_log.py`: LogEntry, DailyLog, ActivityLogger
  - `src/infrastructure/storage/log_repo.py`: LogRepository（7日分保持）
- [x] 記録内容
  - 投稿生成（プロンプト要約、生成内容、連作情報）
  - レビュー結果（承認/却下、理由）
  - 投稿完了（event_id）
  - リプライ/リアクション送受信（パラメータ変化含む）
  - 連作開始/完了
- [x] 各サービスへの統合
  - BotService, InteractionService, tick.py

### 文章スタイルシステム（2025-12-26 完了）
- [x] WritingStyleモデルの実装（`src/domain/models.py`）
  - `typo_rate`: 誤字率（0.0〜0.1）
  - `LineBreakStyle`: 改行スタイル（none, minimal, sentence, paragraph）
  - `PunctuationStyle`: 句読点スタイル（full, comma_only, period_only, none）
  - `WritingQuirk`: 文章の癖（w_heavy, kusa, ellipsis_heavy, suffix_ne等12種）
- [x] TextProcessorクラス（`src/domain/text_processor.py`）
  - 誤字挿入（TYPO_MAP使用）
  - 改行スタイル適用
  - 句読点スタイル適用
  - 癖の適用（確率的処理）
- [x] プロンプト指示の統合
  - ContentStrategy._get_writing_style_instructions()
  - create_prompt, create_reply_prompt, create_mumble_promptに反映
- [x] コンテンツ生成後の加工
  - BotService.generate_post_content()にTextProcessor統合
  - InteractionService（リプライ生成）にTextProcessor統合
  - StalkerService（ぶつぶつ生成）にTextProcessor統合
- [x] 95人分のwriting_style設定
  - scripts/add_writing_style.py による一括追加
  - 性格・職業・文体に基づく自動設定

### 外部ユーザー反応システム（2025-12-26 完了）
- [x] スター機能（住人間）- 既存のリアクション機能として実装済み
- [x] ExternalReactionService（`src/application/external_reaction_service.py`）
  - タイムラインAPI / EXTERNAL_PUBKEYS環境変数から外部投稿を取得
  - 住人の興味・キーワードとマッチング
  - 社交性に基づくスター/リプライ確率判定
- [x] ReplyTarget.pubkeyフィールド追加（外部ユーザー対応）
- [x] postコマンドで外部pubkey対応
  - `external:xxx`形式のresident判定
  - pubkeyを直接使用した投稿
- [x] tickコマンドへの統合
  - `process_external_reactions()` を相互作用処理後に実行
  - 1人1投稿まで（控えめ設定）

## 未着手

### 関係性の拡充
- [ ] 100人に対応したグループ・ペア定義の追加
