"""
ストーカーサービス（外部アカウントウォッチ）
"""

import random
from typing import Any

from ..domain import BotProfile, BotState, ContentStrategy, PostType, QueueEntry, QueueStatus
from ..domain.models import BotKey
from ..domain.queue import MumbleAbout
from ..domain.relationships import Stalker
from ..infrastructure import LLMProvider, QueueRepository
from ..infrastructure.storage.relationship_repo import RelationshipRepository


class StalkerService:
    """ストーカー（外部アカウントウォッチャー）の処理"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        queue_repo: QueueRepository,
        relationship_repo: RelationshipRepository,
        content_strategy: ContentStrategy,
        bots: dict[int, tuple[BotKey, BotProfile, BotState]],
    ):
        self.llm_provider = llm_provider
        self.queue_repo = queue_repo
        self.relationship_repo = relationship_repo
        self.content_strategy = content_strategy
        self.bots = bots

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
            # ストーカー役のボットを取得
            bot_id = self._parse_bot_id(stalker.resident)
            if bot_id is None or bot_id not in self.bots:
                continue

            _, profile, _ = self.bots[bot_id]

            # 反応確率でスキップ
            if random.random() > stalker.behavior.reaction_probability:
                continue

            # 外部投稿を取得（TODO: MYPACE API経由で実装）
            external_post = self._fetch_external_post(stalker)
            if not external_post:
                continue

            # ぶつぶつ投稿を生成
            entry = await self._generate_mumble(
                bot_id, profile, stalker, external_post
            )
            if entry:
                self.queue_repo.add(entry)
                generated += 1
                print(f"      👁️ {profile.name} → {stalker.target.display_name}")

        return generated

    def _parse_bot_id(self, resident: str) -> int | None:
        """bot001 -> 1"""
        if resident.startswith("bot"):
            try:
                return int(resident[3:])
            except ValueError:
                return None
        return None

    def _fetch_external_post(self, stalker: Stalker) -> dict[str, Any] | None:
        """
        外部アカウントの投稿を取得

        TODO: MYPACE API経由で実装
        現在はモック実装
        """
        # モック: ターゲットの最新投稿を模擬
        if not stalker.target.pubkey:
            return None

        # 実装時はここでMYPACE APIを呼び出し
        # 今はNoneを返して処理をスキップ
        return None

    async def _generate_mumble(
        self,
        bot_id: int,
        profile: BotProfile,
        stalker: Stalker,
        external_post: dict[str, Any],
    ) -> QueueEntry | None:
        """ぶつぶつ投稿を生成"""
        if not self.llm_provider:
            return None

        # 反応タイプを選択
        reaction_type = self._select_reaction_type(stalker)

        # プロンプト生成
        prompt = self._create_mumble_prompt(
            profile, stalker, external_post, reaction_type
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # MumbleAboutを作成
        mumble_about = MumbleAbout(
            type="external",
            pubkey=stalker.target.pubkey,
            display_name=stalker.target.display_name,
            original_content=external_post.get("content", ""),
        )

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
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
        profile: BotProfile,
        stalker: Stalker,
        external_post: dict[str, Any],
        reaction_type: str,
    ) -> str:
        """ぶつぶつ用のプロンプトを生成"""
        target_name = stalker.target.display_name
        original_content = external_post.get("content", "")

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

        prompt = f"""あなたは{profile.name}です。{target_name}さんの投稿を見て、{instruction}投稿を書いてください。

【{target_name}さんの投稿】
{original_content}

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
