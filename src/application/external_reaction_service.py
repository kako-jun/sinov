"""
外部ユーザー反応サービス

100人以外のNostrユーザーの投稿に対して、
内容が興味深い場合はスター/リプライ/リポストを行う。
"""

import os
import random
from typing import Any

import httpx

from ..domain import (
    ActivityLogger,
    ContentStrategy,
    NpcProfile,
    NpcState,
    PostType,
    QueueEntry,
    QueueStatus,
    TextProcessor,
)
from ..domain.models import NpcKey
from ..domain.queue import ReplyTarget
from ..infrastructure import LLMProvider, LogRepository, QueueRepository


class ExternalReactionService:
    """外部ユーザーへの反応サービス"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        queue_repo: QueueRepository,
        content_strategy: ContentStrategy,
        bots: dict[int, tuple[NpcKey, NpcProfile, NpcState]],
        log_repo: LogRepository | None = None,
    ):
        self.llm_provider = llm_provider
        self.queue_repo = queue_repo
        self.content_strategy = content_strategy
        self.bots = bots
        self.log_repo = log_repo
        self.api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")
        # 反応済みイベントIDのキャッシュ（重複防止）
        self._reacted_events: set[str] = set()

    async def process_external_reactions(
        self,
        target_bot_ids: list[int] | None = None,
        max_posts_per_bot: int = 3,
    ) -> int:
        """
        外部投稿への反応処理

        Args:
            target_bot_ids: 処理対象のNPC ID（Noneなら全員）
            max_posts_per_bot: 1NPCあたりの最大反応数

        Returns:
            生成したエントリー数
        """
        # 既に反応済みのイベントIDを読み込み（重複防止）
        self._load_reacted_events()

        # タイムラインから外部投稿を取得
        external_posts = await self._fetch_timeline_posts(limit=50)
        if not external_posts:
            print("  📭 外部投稿なし")
            return 0

        # 住人のpubkey一覧（除外用）
        resident_pubkeys = {
            key.pubkey for _, (key, _, _) in self.bots.items()
        }

        # 外部投稿のみにフィルタ
        external_posts = [
            p for p in external_posts
            if p.get("pubkey") not in resident_pubkeys
        ]

        if not external_posts:
            print("  📭 外部投稿なし（フィルタ後）")
            return 0

        print(f"  📬 外部投稿: {len(external_posts)}件")

        total_entries = 0
        bot_ids = target_bot_ids or list(self.bots.keys())

        for bot_id in bot_ids:
            if bot_id not in self.bots:
                continue

            _, profile, state = self.bots[bot_id]

            # このNPCの反応数
            reactions_added = 0

            for post in external_posts:
                if reactions_added >= max_posts_per_bot:
                    break

                event_id = post.get("id", post.get("event_id", ""))

                # 重複チェック（このNPCが既にこの投稿に反応済み）
                reaction_key = f"{bot_id}:{event_id}"
                if reaction_key in self._reacted_events:
                    continue

                # 興味マッチング
                if not self._matches_interests(post, profile):
                    continue

                # 反応するか判定
                reaction_type = self._decide_reaction(profile, post)
                if not reaction_type:
                    continue

                # エントリー生成
                entry = await self._generate_entry(
                    bot_id, profile, post, reaction_type
                )
                if entry:
                    self.queue_repo.add(entry)
                    self._reacted_events.add(reaction_key)
                    reactions_added += 1
                    total_entries += 1

                    # ログ記録
                    if self.log_repo:
                        target_info = f"external:{post.get('pubkey', '')[:8]}"
                        self.log_repo.add_entry(
                            bot_id,
                            ActivityLogger.log_external_reaction(
                                reaction_type=reaction_type,
                                target=target_info,
                                content=post.get("content", "")[:50],
                            ),
                        )

                    print(f"    {profile.name} → {reaction_type} to external post")

        return total_entries

    def _load_reacted_events(self) -> None:
        """既に反応済みのイベントIDを読み込み"""
        # キューから外部向けの投稿済み/承認済みエントリーを取得
        for status in [QueueStatus.POSTED, QueueStatus.APPROVED, QueueStatus.PENDING]:
            entries = self.queue_repo.get_all(status)
            for entry in entries:
                if entry.reply_to and entry.reply_to.resident.startswith("external:"):
                    reaction_key = f"{entry.bot_id}:{entry.reply_to.event_id}"
                    self._reacted_events.add(reaction_key)

    async def _fetch_timeline_posts(self, limit: int = 50) -> list[dict[str, Any]]:
        """タイムラインから投稿を取得"""
        # 公開タイムラインを取得（API依存）
        url = f"{self.api_endpoint}/api/timeline"

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(url, params={"limit": limit})

                if response.status_code != 200:
                    # タイムラインAPIがない場合はフォールバック
                    return await self._fetch_from_known_users(limit)

                data = response.json()
                events: list[dict[str, Any]] = data.get("events", [])
                return events

        except Exception as e:
            print(f"  ⚠️ タイムライン取得エラー: {e}")
            return await self._fetch_from_known_users(limit)

    async def _fetch_from_known_users(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        既知のユーザーから投稿を取得（フォールバック）
        環境変数 EXTERNAL_PUBKEYS から取得
        """
        pubkeys_str = os.getenv("EXTERNAL_PUBKEYS", "")
        if not pubkeys_str:
            return []

        pubkeys = [p.strip() for p in pubkeys_str.split(",") if p.strip()]
        all_posts: list[dict[str, Any]] = []

        for pubkey in pubkeys[:10]:  # 最大10人
            posts = await self._fetch_user_posts(pubkey)
            all_posts.extend(posts)

        # シャッフルして返す
        random.shuffle(all_posts)
        return all_posts[:limit]

    async def _fetch_user_posts(self, pubkey: str) -> list[dict[str, Any]]:
        """特定ユーザーの投稿を取得"""
        url = f"{self.api_endpoint}/api/user/{pubkey}/events"

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(url, params={"limit": 5})

                if response.status_code != 200:
                    return []

                data = response.json()
                events: list[dict[str, Any]] = data.get("events", [])

                # pubkeyを追加
                for event in events:
                    event["pubkey"] = pubkey

                return events

        except Exception:
            return []

    def _matches_interests(self, post: dict[str, Any], profile: NpcProfile) -> bool:
        """投稿が住人の興味に合うか判定"""
        content = post.get("content", "").lower()
        if not content:
            return False

        # キーワードマッチング
        keywords = [k.lower() for k in profile.interests.keywords]
        topics = [t.lower() for t in profile.interests.topics]

        # いずれかのキーワード/トピックを含むか
        for keyword in keywords + topics:
            if keyword in content:
                return True

        # likesの内容もチェック
        for category, items in profile.interests.likes.items():
            for item in items:
                if item.lower() in content:
                    return True

        return False

    def _decide_reaction(
        self,
        profile: NpcProfile,
        post: dict[str, Any],
    ) -> str | None:
        """反応タイプを決定"""
        # 社交性に基づく確率
        sociability = 0.5
        if profile.traits_detail:
            sociability = profile.traits_detail.sociability

        # 基本確率（低め: 外部なので控えめ）
        base_prob = 0.1 * (0.5 + sociability)

        # スター確率
        if random.random() < base_prob * 2:
            return "star"

        # リプライ確率（さらに低い）
        if random.random() < base_prob * 0.5:
            return "reply"

        return None

    async def _generate_entry(
        self,
        bot_id: int,
        profile: NpcProfile,
        post: dict[str, Any],
        reaction_type: str,
    ) -> QueueEntry | None:
        """エントリーを生成"""
        event_id = post.get("id", post.get("event_id", ""))
        pubkey = post.get("pubkey", "")
        content = post.get("content", "")

        if not event_id or not pubkey:
            return None

        # スターの場合
        if reaction_type == "star":
            return self._generate_star_entry(bot_id, profile, event_id, pubkey)

        # リプライの場合
        if reaction_type == "reply":
            return await self._generate_reply_entry(
                bot_id, profile, event_id, pubkey, content
            )

        return None

    def _generate_star_entry(
        self,
        bot_id: int,
        profile: NpcProfile,
        event_id: str,
        pubkey: str,
    ) -> QueueEntry:
        """スターエントリーを生成"""
        reply_to = ReplyTarget(
            resident=f"external:{pubkey[:8]}",
            event_id=event_id,
            content="",
            pubkey=pubkey,  # 外部ユーザーのpubkey
        )

        # 絵文字を選択
        emojis = ["👍", "❤️", "+", "⭐", "🙌"]
        emoji = random.choice(emojis)

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
            content=emoji,
            status=QueueStatus.PENDING,
            post_type=PostType.REACTION,
            reply_to=reply_to,
        )

    async def _generate_reply_entry(
        self,
        bot_id: int,
        profile: NpcProfile,
        event_id: str,
        pubkey: str,
        target_content: str,
    ) -> QueueEntry | None:
        """リプライエントリーを生成"""
        if not self.llm_provider:
            return None

        # プロンプト生成
        prompt = f"""あなたは{profile.name}です。
外部ユーザーの投稿に対して、短いリプライを書いてください。

【相手の投稿】
{target_content[:200]}

【ルール】
- 短めに（20〜60文字程度）
- フレンドリーだが馴れ馴れしすぎない
- 必ず日本語で書く

返信:"""

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        reply_to = ReplyTarget(
            resident=f"external:{pubkey[:8]}",
            event_id=event_id,
            content=target_content[:100],
            pubkey=pubkey,
        )

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
        )
