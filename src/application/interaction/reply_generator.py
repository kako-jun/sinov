"""
リプライ生成ロジック
"""

from ...domain import (
    ContentStrategy,
    ConversationContext,
    NpcProfile,
    PostType,
    QueueEntry,
    QueueStatus,
    ReplyTarget,
    TextProcessor,
)
from ...infrastructure import LLMProvider, ProfileRepository


class ReplyGenerator:
    """リプライ生成を担当"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        content_strategy: ContentStrategy,
        profile_repo: ProfileRepository | None = None,
    ):
        self.llm_provider = llm_provider
        self.content_strategy = content_strategy
        self.profile_repo = profile_repo

    async def generate_reply(
        self,
        npc_id: int,
        profile: NpcProfile,
        target_entry: QueueEntry,
        affinity: float,
        relationship_type: str = "知り合い",
    ) -> QueueEntry | None:
        """リプライを生成"""
        if not self.llm_provider:
            return None

        # リプライ先情報を作成
        reply_to = ReplyTarget(
            resident=f"npc{target_entry.npc_id:03d}",
            event_id=target_entry.event_id or "",
            content=target_entry.content,
        )

        # マージ済みプロンプトを取得
        merged_prompts = None
        if self.profile_repo:
            merged_prompts = self.profile_repo.get_merged_prompts(profile)

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=None,  # 新規リプライなのでコンテキストなし
            relationship_type=relationship_type,
            affinity=affinity,
            merged_prompts=merged_prompts,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        # 会話コンテキストを作成
        conversation = ConversationContext(
            thread_id=target_entry.event_id or target_entry.id,
            depth=1,
            history=[
                {
                    "author": target_entry.npc_name,
                    "content": target_entry.content,
                    "depth": 0,
                }
            ],
        )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    async def generate_chain_reply(
        self,
        npc_id: int,
        profile: NpcProfile,
        incoming_entry: QueueEntry,
        affinity: float,
        relationship_type: str = "知り合い",
    ) -> QueueEntry | None:
        """会話チェーンへの返信を生成"""
        if not self.llm_provider:
            return None

        # 会話コンテキストを更新
        existing_conv = incoming_entry.conversation
        new_depth = (existing_conv.depth + 1) if existing_conv else 1

        new_history = existing_conv.history.copy() if existing_conv else []
        new_history.append(
            {
                "author": incoming_entry.npc_name,
                "content": incoming_entry.content,
                "depth": existing_conv.depth if existing_conv else 0,
            }
        )

        conversation = ConversationContext(
            thread_id=existing_conv.thread_id if existing_conv else incoming_entry.id,
            depth=new_depth,
            history=new_history,
        )

        # リプライ先情報
        reply_to = ReplyTarget(
            resident=f"npc{incoming_entry.npc_id:03d}",
            event_id=incoming_entry.event_id or "",
            content=incoming_entry.content,
        )

        # マージ済みプロンプトを取得
        merged_prompts = None
        if self.profile_repo:
            merged_prompts = self.profile_repo.get_merged_prompts(profile)

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=conversation,
            relationship_type=relationship_type,
            affinity=affinity,
            merged_prompts=merged_prompts,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )
