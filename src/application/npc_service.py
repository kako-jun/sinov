"""
NPCサービス（アプリケーションユースケース）
"""

import difflib
import json
import random
from datetime import datetime
from pathlib import Path

from nostr_sdk import Keys

from ..config import Settings
from ..domain import (
    ActivityLogger,
    ContentStrategy,
    EventCalendar,
    NpcKey,
    NpcMemory,
    NpcProfile,
    NpcState,
    Scheduler,
    TextProcessor,
    format_npc_name,
)
from ..infrastructure import (
    LLMProvider,
    LogRepository,
    MemoryRepository,
    NostrPublisher,
    ProfileRepository,
    QueueRepository,
    StateRepository,
)


class NpcService:
    """NPC管理サービス"""

    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider | None,
        publisher: NostrPublisher,
        profile_repo: ProfileRepository,
        state_repo: StateRepository,
        memory_repo: MemoryRepository,
        queue_repo: QueueRepository | None = None,
        log_repo: LogRepository | None = None,
    ):
        self.settings = settings
        self.llm_provider = llm_provider
        self.publisher = publisher
        self.profile_repo = profile_repo
        self.state_repo = state_repo
        self.memory_repo = memory_repo
        self.queue_repo = queue_repo
        self.log_repo = log_repo
        self.content_strategy = ContentStrategy(settings.content)

        # NPCデータ
        self.npcs: dict[int, tuple[NpcKey, NpcProfile, NpcState]] = {}
        self.keys: dict[int, Keys] = {}

    async def load_bots(self) -> None:
        """NPCのデータを読み込み"""
        print("Loading bot profiles...")

        profiles = self.profile_repo.load_all()
        states = self.state_repo.load_all()

        for profile in profiles:
            npc_id = profile.id

            # 環境変数から鍵を読み込み
            try:
                npc_key = NpcKey.from_env(npc_id)
            except Exception as e:
                print(f"⚠️  Keys not found for {format_npc_name(npc_id)}: {e}, skipping...")
                continue

            # 状態読み込み（存在しない場合は初期化）
            state = states.get(npc_id) or self.state_repo.create_initial(npc_id)

            self.npcs[npc_id] = (npc_key, profile, state)

        print(f"✅ Loaded {len(self.npcs)} NPCs")

    async def initialize_keys(self) -> None:
        """Nostr署名鍵を初期化"""
        print("Initializing Nostr keys...")

        for npc_id, (key, _, _) in self.npcs.items():
            try:
                keys = Keys.parse(key.nsec)
                self.keys[npc_id] = keys
            except Exception as e:
                print(f"⚠️  Failed to parse key for bot {npc_id}: {e}")

        print(f"✅ Initialized {len(self.keys)} bot keys")

    async def generate_post_content(self, npc_id: int) -> str:
        """投稿内容を生成"""
        _, profile, state = self.npcs[npc_id]

        if not self.llm_provider:
            raise RuntimeError("LLM provider is not available")

        # 記憶を読み込み
        memory = self.memory_repo.load(npc_id)

        # 連作を開始するか判定（連作中でなければ）
        if not memory.series.active and self.content_strategy.should_start_series():
            theme, total = self.content_strategy.generate_series_theme(profile)
            memory.start_series(theme, total)
            print(f"      📝 連作開始: {theme} ({total}投稿)")
            # ログ記録
            if self.log_repo:
                self.log_repo.add_entry(npc_id, ActivityLogger.log_series_start(theme, total))

        # 共有ニュース読み込み
        shared_news = self._load_shared_news()

        # イベントトピック読み込み
        event_topics = self._load_event_topics()

        # 過去のrejectを取得（反省のため）
        rejected_posts = self._load_rejected_posts(npc_id)

        # 共通プロンプト + 個人プロンプトをマージ
        merged_prompts = self.profile_repo.get_merged_prompts(profile)

        # 最大リトライ回数
        for attempt in range(self.settings.content.llm_retry_count):
            # プロンプト生成（記憶を含む）
            prompt = self.content_strategy.create_prompt(
                profile,
                state,
                memory=memory,
                shared_news=shared_news,
                event_topics=event_topics,
                merged_prompts=merged_prompts,
                rejected_posts=rejected_posts,
            )

            # LLMで生成
            content = await self.llm_provider.generate(
                prompt, max_length=profile.behavior.post_length_max
            )

            # クリーンアップ（use_markdown/use_code_blocks設定を考慮）
            use_markdown = profile.behavior.use_markdown
            use_code_blocks = profile.behavior.use_code_blocks
            content = self.content_strategy.clean_content(content, use_markdown, use_code_blocks)

            # バリデーション（use_markdown/use_code_blocks設定を考慮）
            if not self.content_strategy.validate_content(content, use_markdown, use_code_blocks):
                print(
                    f"⚠️  Retry {attempt + 1}/{self.settings.content.llm_retry_count}: "
                    "Invalid content detected"
                )
                continue

            # 長さ調整
            content = self.content_strategy.adjust_length(
                content,
                profile.behavior.post_length_min,
                profile.behavior.post_length_max,
            )

            # 文章スタイル加工（誤字、改行、句読点、癖）
            if profile.writing_style:
                text_processor = TextProcessor(profile.writing_style)
                content = text_processor.process(content)

            # 類似投稿チェック（セルフチェック）
            recent_posts = memory.recent_posts if memory else state.post_history
            if self._is_too_similar(content, recent_posts):
                print(
                    f"⚠️  Retry {attempt + 1}/{self.settings.content.llm_retry_count}: "
                    "Too similar to recent posts"
                )
                continue

            # 記憶を更新
            self._update_memory_after_generate(npc_id, content, memory)

            # ログ記録（投稿生成）
            if self.log_repo:
                # フルプロンプトを記録（デバッグ用）
                prompt_summary = prompt
                series_info = None
                if memory.series.active:
                    idx = memory.series.current_index + 1
                    total = memory.series.total_planned
                    series_info = f"連作「{memory.series.theme}」{idx}/{total}"
                self.log_repo.add_entry(
                    npc_id,
                    ActivityLogger.log_post_generate(content, prompt_summary, series_info),
                )

            return content

        raise RuntimeError(
            f"Failed to generate valid content after "
            f"{self.settings.content.llm_retry_count} attempts"
        )

    def _update_memory_after_generate(self, npc_id: int, content: str, memory: NpcMemory) -> None:
        """投稿生成後に記憶を更新"""

        # 短期記憶を減衰
        memory.decay_short_term(decay_rate=0.1)

        # 新しい投稿を短期記憶に追加
        memory.add_short_term(content, source="post")

        # 最近の投稿に追加
        memory.add_recent_post(content)

        # 連作中なら進める
        if memory.series.active:
            theme = memory.series.theme  # 完了前に保存
            finished = memory.advance_series(content)
            if finished:
                print("      ✅ 連作完了")
                # 連作完了したら長期記憶に昇格（テーマをタグとして付与）
                memory.promote_to_long_term(
                    f"連作「{theme}」を完了",
                    importance=0.7,
                    tags=[theme] if theme else [],
                )
                # ログ記録
                if self.log_repo and theme:
                    self.log_repo.add_entry(npc_id, ActivityLogger.log_series_end(theme))

        # 記憶を保存
        self.memory_repo.save(memory)

    async def post(self, npc_id: int, content: str) -> None:
        """投稿を実行"""
        try:
            npc_key, profile, state = self.npcs[npc_id]
            keys = self.keys[npc_id]

            # 投稿実行
            event_id = await self.publisher.publish(keys, content, profile.name)

            # 状態を更新
            current_time = int(datetime.now().timestamp())
            state.last_post_time = current_time
            state.next_post_time = Scheduler.calculate_next_post_time(profile)
            state.total_posts += 1
            state.last_post_content = content
            state.last_event_id = event_id

            # 投稿履歴を更新
            state.post_history.append(content)
            if len(state.post_history) > self.settings.content.max_history_size:
                state.post_history = state.post_history[-self.settings.content.max_history_size :]

            # 成長要素
            self._evolve_interests(npc_id)

            next_datetime = datetime.fromtimestamp(state.next_post_time)
            print(
                f"📝 {profile.name} posted: {content[:50]}... "
                f"(next: {next_datetime.strftime('%H:%M:%S')})"
            )

            # ログ記録（投稿完了）
            if self.log_repo and event_id:
                self.log_repo.add_entry(
                    npc_id, ActivityLogger.log_post_published(content, event_id)
                )
        except Exception as e:
            _, profile, _ = self.npcs[npc_id]
            print(f"❌ Failed to post for {profile.name}: {e}")
            raise

    def _evolve_interests(self, npc_id: int) -> None:
        """NPCの興味を成長させる"""
        _, profile, state = self.npcs[npc_id]
        interval = self.settings.content.evolution_interval

        if state.total_posts % interval == 0 and state.total_posts > 0:
            # まだ興味を持っていないトピックを選択
            existing = set(profile.interests.topics + state.discovered_topics)
            new_topics = [t for t in self.settings.topic_pool if t not in existing]

            if new_topics:
                new_topic = random.choice(new_topics)
                state.discovered_topics.append(new_topic)
                print(f"🌱 {profile.name}が新しいトピックに興味: {new_topic}")

    def _load_shared_news(self) -> list[str]:
        """掲示板ニュースを読み込む"""
        bulletin_file = Path(self.settings.bulletin_dir) / "news.json"
        if not bulletin_file.exists():
            return []

        try:
            with open(bulletin_file) as f:
                data = json.load(f)
                items = data.get("items", [])
                news: list[str] = []
                now = datetime.now()
                for item in items:
                    # 期限切れチェック
                    expires_str = item.get("expires_at", "")
                    if expires_str:
                        try:
                            expires = datetime.fromisoformat(expires_str)
                            if now > expires:
                                continue
                        except ValueError:
                            pass

                    title = item.get("title", "")
                    summary = item.get("summary", "")
                    url = item.get("original_url", "")
                    if title:
                        news_text = title
                        if summary:
                            news_text += f": {summary}"
                        if url:
                            news_text += f" ({url})"
                        news.append(news_text)
                return news
        except Exception as e:
            print(f"⚠️  Failed to load bulletin news: {e}")
            return []

    def _load_event_topics(self) -> list[str]:
        """現在有効なイベントのトピックを読み込む"""
        events_file = Path(self.settings.bulletin_dir) / "events.json"
        if not events_file.exists():
            return []

        try:
            with open(events_file) as f:
                data = json.load(f)
                calendar = EventCalendar(events=[])
                for e in data.get("events", []):
                    from ..domain.events import SeasonalEvent

                    event = SeasonalEvent(**e)
                    calendar.events.append(event)
                return calendar.get_event_topics()
        except Exception as e:
            print(f"⚠️  Failed to load events: {e}")
            return []

    def _is_too_similar(
        self, content: str, recent_posts: list[str], threshold: float = 0.6
    ) -> bool:
        """
        生成したコンテンツが最近の投稿と類似しすぎていないかチェック

        Args:
            content: 新しく生成したコンテンツ
            recent_posts: 最近の投稿リスト
            threshold: 類似度の閾値（0.0-1.0、デフォルト0.6）

        Returns:
            類似しすぎている場合はTrue
        """
        for old_post in recent_posts[-5:]:
            ratio = difflib.SequenceMatcher(None, content, old_post).ratio()
            if ratio > threshold:
                return True
        return False

    def _load_rejected_posts(self, npc_id: int) -> list[dict[str, str]]:
        """過去にrejectされた投稿を読み込む（反省のため）"""
        if not self.queue_repo:
            return []

        try:
            entries = self.queue_repo.get_recent_rejected(npc_id, limit=3)
            return [{"content": e.content, "reason": e.review_note or "理由不明"} for e in entries]
        except Exception as e:
            print(f"⚠️  Failed to load rejected posts: {e}")
            return []

    async def review_content(self, content: str) -> tuple[bool, str | None]:
        """
        投稿内容をレビュー（NGルールに違反していないかチェック）

        Returns:
            (is_approved, reason): 承認されたかどうかと理由
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider is not available")

        review_prompt = f"""この投稿にNGワードがあるか？

投稿: {content[:200]}

NGワード:
- 実在の有名人の名前（田中太郎、山田花子など）
- 政党名、宗教団体名
- 「死ね」「殺す」などの暴力的な言葉

OKなもの:
- 技術用語（Python, React, AIなど）
- ゲーム名、アニメ名
- 普通の日常会話

回答は「OK」か「NG」の一言だけ。
"""

        response = await self.llm_provider.generate(review_prompt, max_length=100)
        response = response.strip().upper()

        # 明確にNGと判定された場合のみNG（具体的な理由がある場合）
        # 「NG」だけでなく、NGワードに関する具体的な言及があればNG
        ng_keywords = ["実在", "有名人", "政治", "宗教", "暴力", "死ね", "殺"]
        has_ng_reason = any(kw in response for kw in ng_keywords)

        if "NG" in response and has_ng_reason:
            return False, response[:100]

        # それ以外はすべてOK（デフォルトOK）
        return True, None

    def log_review(self, npc_id: int, content: str, approved: bool, reason: str | None) -> None:
        """レビュー結果をログに記録"""
        if self.log_repo:
            self.log_repo.add_entry(npc_id, ActivityLogger.log_review(content, approved, reason))

    def _save_states(self) -> None:
        """全NPCの状態を保存"""
        states = {npc_id: state for npc_id, (_, _, state) in self.npcs.items()}
        self.state_repo.save_all(states)
