"""
ボットサービス（アプリケーションユースケース）
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path

from nostr_sdk import Keys

from ..config import Settings
from ..domain import BotKey, BotProfile, BotState, ContentStrategy, Scheduler
from ..infrastructure import (
    LLMProvider,
    NostrPublisher,
    ProfileRepository,
    StateRepository,
)


class BotService:
    """ボット管理サービス"""

    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider | None,
        publisher: NostrPublisher,
        profile_repo: ProfileRepository,
        state_repo: StateRepository,
    ):
        self.settings = settings
        self.llm_provider = llm_provider
        self.publisher = publisher
        self.profile_repo = profile_repo
        self.state_repo = state_repo
        self.content_strategy = ContentStrategy(settings.content)

        # ボットデータ
        self.bots: dict[int, tuple[BotKey, BotProfile, BotState]] = {}
        self.keys: dict[int, Keys] = {}

    async def load_bots(self) -> None:
        """ボットのデータを読み込み"""
        print("Loading bot profiles...")

        profiles = self.profile_repo.load_all()
        states = self.state_repo.load_all()

        for profile in profiles:
            bot_id = profile.id

            # 環境変数から鍵を読み込み
            try:
                bot_key = BotKey.from_env(bot_id)
            except Exception as e:
                print(f"⚠️  Keys not found for bot{bot_id:03d}: {e}, skipping...")
                continue

            # 状態読み込み（存在しない場合は初期化）
            state = states.get(bot_id) or self.state_repo.create_initial(bot_id)

            self.bots[bot_id] = (bot_key, profile, state)

        print(f"✅ Loaded {len(self.bots)} bots")

    async def initialize_keys(self) -> None:
        """Nostr署名鍵を初期化"""
        print("Initializing Nostr keys...")

        for bot_id, (key, _, _) in self.bots.items():
            try:
                keys = Keys.parse(key.nsec)
                self.keys[bot_id] = keys
            except Exception as e:
                print(f"⚠️  Failed to parse key for bot {bot_id}: {e}")

        print(f"✅ Initialized {len(self.keys)} bot keys")

    async def generate_post_content(self, bot_id: int) -> str:
        """投稿内容を生成"""
        _, profile, state = self.bots[bot_id]

        if not self.llm_provider:
            raise RuntimeError("LLM provider is not available")

        # 共有ニュース読み込み
        shared_news = self._load_shared_news()

        # 最大リトライ回数
        for attempt in range(self.settings.content.llm_retry_count):
            # プロンプト生成
            prompt = self.content_strategy.create_prompt(profile, state, shared_news)

            # LLMで生成
            content = await self.llm_provider.generate(
                prompt, max_length=profile.behavior.post_length_max
            )

            # クリーンアップ
            content = self.content_strategy.clean_content(content)

            # バリデーション
            if not self.content_strategy.validate_content(content):
                print(
                    f"⚠️  Retry {attempt + 1}/{self.settings.content.llm_retry_count}: "
                    "Markdown symbols detected"
                )
                continue

            # 長さ調整
            content = self.content_strategy.adjust_length(
                content,
                profile.behavior.post_length_min,
                profile.behavior.post_length_max,
            )

            return content

        raise RuntimeError(
            f"Failed to generate valid content after "
            f"{self.settings.content.llm_retry_count} attempts"
        )

    async def post(self, bot_id: int, content: str) -> None:
        """投稿を実行"""
        try:
            bot_key, profile, state = self.bots[bot_id]
            keys = self.keys[bot_id]

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
            self._evolve_interests(bot_id)

            next_datetime = datetime.fromtimestamp(state.next_post_time)
            print(
                f"📝 {profile.name} posted: {content[:50]}... "
                f"(next: {next_datetime.strftime('%H:%M:%S')})"
            )
        except Exception as e:
            _, profile, _ = self.bots[bot_id]
            print(f"❌ Failed to post for {profile.name}: {e}")
            raise

    def _evolve_interests(self, bot_id: int) -> None:
        """ボットの興味を成長させる"""
        _, profile, state = self.bots[bot_id]
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
        """共有ニュースを読み込む"""
        news_file = Path(self.settings.shared_news_file)
        if not news_file.exists():
            return []

        try:
            with open(news_file) as f:
                data = json.load(f)
                news: list[str] = data.get("news", [])
                return news
        except Exception as e:
            print(f"⚠️  Failed to load shared news: {e}")
            return []

    def _save_states(self) -> None:
        """全ボットの状態を保存"""
        states = {bot_id: state for bot_id, (_, _, state) in self.bots.items()}
        self.state_repo.save_all(states)

    async def run_once(self) -> None:
        """全ボットをチェックして投稿が必要なら投稿"""
        for bot_id, (_, profile, state) in self.bots.items():
            if Scheduler.should_post_now(profile, state):
                try:
                    content = await self.generate_post_content(bot_id)
                    await self.post(bot_id, content)
                except Exception as e:
                    print(f"❌ Error posting for {profile.name}: {e}")

        # 状態を保存
        self._save_states()

    async def run_forever(self) -> None:
        """定期的に投稿をチェックして実行（メインループ）"""
        print(f"\n🤖 Starting bot service (checking every {self.settings.check_interval}s)...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                await self.run_once()
                await asyncio.sleep(self.settings.check_interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            self._save_states()
