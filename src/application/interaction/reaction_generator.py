"""
リアクション生成ロジック
"""

from ...domain import (
    InteractionManager,
    NpcProfile,
    PostType,
    QueueEntry,
    QueueStatus,
    ReplyTarget,
)


class ReactionGenerator:
    """リアクション（絵文字）生成を担当"""

    def __init__(self, interaction_manager: InteractionManager):
        self.interaction_manager = interaction_manager

    def generate_reaction(
        self,
        npc_id: int,
        profile: NpcProfile,
        target_entry: QueueEntry,
        personality_type: str = "normal",
    ) -> QueueEntry | None:
        """リアクションを生成"""
        # 性格に応じた絵文字を選択
        emoji = self.interaction_manager.select_reaction_emoji(
            target_entry.content, personality_type
        )

        reply_to = ReplyTarget(
            resident=f"npc{target_entry.npc_id:03d}",
            event_id=target_entry.event_id or "",
            content="",  # リアクションでは内容不要
        )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=emoji,
            status=QueueStatus.PENDING,
            post_type=PostType.REACTION,
            reply_to=reply_to,
        )
