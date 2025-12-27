"""
ストーカーサービス（外部アカウントウォッチ）
"""

import os
import random
from typing import Any

import httpx

from ..domain import (
    ContentStrategy,
    MumbleAbout,
    NpcKey,
    NpcProfile,
    NpcState,
    PostType,
    QueueEntry,
    QueueStatus,
    Stalker,
    TextProcessor,
    extract_npc_id,
)
from ..infrastructure import LLMProvider, QueueRepository, RelationshipRepository


class StalkerService:
    """ストーカー（外部アカウントウォッチャー）の処理"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        queue_repo: QueueRepository,
        relationship_repo: RelationshipRepository,
        content_strategy: ContentStrategy,
        npcs: dict[int, tuple[NpcKey, NpcProfile, NpcState]],
    ):
        self.llm_provider = llm_provider
        self.queue_repo = queue_repo
        self.relationship_repo = relationship_repo
        self.content_strategy = content_strategy
        self.npcs = npcs

        # ストーカー定義を読み込み
        self.stalkers = relationship_repo.load_stalkers()

    async def process_stalkers(self) -> int:
        """
        全ストーカーの処理を実行

        Returns:
            生成されたぶつぶつ投稿数
        """
        if not self.llm_provider:
            return 0

        if not self.stalkers:
            return 0

        generated = 0

        for stalker in self.stalkers:
            # ストーカー役のNPCを取得
            npc_id = extract_npc_id(stalker.resident)
            if npc_id is None or npc_id not in self.npcs:
                continue

            _, profile, _ = self.npcs[npc_id]

            # 反応確率でスキップ
            if random.random() > stalker.behavior.reaction_probability:
                continue

            # ターゲットの最近の投稿を取得
            external_posts = await self._fetch_external_posts(stalker)
            if not external_posts:
                continue

            # ぶつぶつ投稿を生成
            entry = await self._generate_mumble(npc_id, profile, stalker, external_posts)
            if entry:
                self.queue_repo.add(entry)
                generated += 1
                print(f"      👁️ {profile.name} → {stalker.target.display_name}")

        return generated

    async def _fetch_external_posts(self, stalker: Stalker, limit: int = 5) -> list[dict[str, Any]]:
        """
        ターゲットアカウントの最近の投稿を取得（MYPACE API経由）
        """
        if not stalker.target.pubkey:
            return []

        api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")
        url = f"{api_endpoint}/api/user/{stalker.target.pubkey}/events"

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(url, params={"limit": limit})

                if response.status_code != 200:
                    print(f"  ⚠️ API応答: {response.status_code}")
                    return []

                data = response.json()
                events = data.get("events", [])

                if not events:
                    return []

                # 最近の投稿をリストで返す
                return [
                    {
                        "event_id": e.get("id", ""),
                        "content": e.get("content", ""),
                        "created_at": e.get("created_at", 0),
                    }
                    for e in events
                ]

        except Exception as e:
            print(f"  ⚠️ 投稿取得エラー: {e}")
            return []

    async def _generate_mumble(
        self,
        npc_id: int,
        profile: NpcProfile,
        stalker: Stalker,
        external_posts: list[dict[str, Any]],
    ) -> QueueEntry | None:
        """ぶつぶつ投稿を生成"""
        if not self.llm_provider or not external_posts:
            return None

        # 反応タイプを選択
        reaction_type = self._select_reaction_type(stalker)

        # プロンプト生成（最新の投稿をメインに、他は文脈として使用）
        prompt = self._create_mumble_prompt(profile, stalker, external_posts, reaction_type)

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        # MumbleAboutを作成（最新の投稿を参照）
        latest_post = external_posts[0]
        mumble_about = MumbleAbout(
            type="external",
            pubkey=stalker.target.pubkey,
            display_name=stalker.target.display_name,
            original_content=latest_post.get("content", ""),
        )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.MUMBLE,
            mumble_about=mumble_about,
        )

    def _select_reaction_type(self, stalker: Stalker) -> str:
        """反応タイプを確率で選択"""
        reactions = stalker.behavior.reactions
        if not reactions:
            return "mumble"

        # 確率に基づいて選択
        rand = random.random()
        cumulative = 0.0
        for reaction in reactions:
            cumulative += reaction.probability
            if rand < cumulative:
                return reaction.type

        return reactions[-1].type if reactions else "mumble"

    def _create_mumble_prompt(
        self,
        profile: NpcProfile,
        stalker: Stalker,
        external_posts: list[dict[str, Any]],
        reaction_type: str,
    ) -> str:
        """ぶつぶつ用のプロンプトを生成"""
        target_name = stalker.target.display_name

        # 最新の投稿（メインで反応する対象）
        latest_content = external_posts[0].get("content", "") if external_posts else ""

        # 過去の投稿を文脈として含める
        recent_context = ""
        if len(external_posts) > 1:
            past_posts = [p.get("content", "")[:80] for p in external_posts[1:4]]
            if past_posts:
                recent_context = "\n\n【最近の投稿傾向】\n" + "\n".join(
                    f"- {p}..." for p in past_posts
                )

        # 反応タイプに応じた指示
        type_instructions = {
            "mumble": "独り言のようにぶつぶつ言及する",
            "comment": "感想を述べる",
            "support": "応援する気持ちを表す",
        }
        instruction = type_instructions.get(reaction_type, "言及する")

        # 例文を取得
        examples = []
        for reaction in stalker.behavior.reactions:
            if reaction.type == reaction_type:
                examples = reaction.examples
                break

        examples_text = ""
        if examples:
            examples_text = "\n例:\n" + "\n".join(f"- {e}" for e in examples[:3])

        # 制約
        constraints = stalker.constraints or []
        constraints_text = ""
        if constraints:
            constraints_text = "\n制約:\n" + "\n".join(f"- {c}" for c in constraints)

        prompt = f"""あなたは{profile.name}です。
{target_name}さんの投稿を見て、{instruction}投稿を書いてください。

【{target_name}さんの最新投稿】
{latest_content}
{recent_context}

【あなたの性格】
{profile.personality.type}
{examples_text}
{constraints_text}

条件:
- 直接リプライではなく、独り言として投稿
- {target_name}さんに話しかけない
- 最大{profile.behavior.post_length_max}文字
- 日本語で書く

投稿:"""

        return prompt
