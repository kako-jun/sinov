"""
相互作用システム

住人同士のリプライ、リアクション、ぶつぶつを管理する。
"""

import random
import uuid

from .queue import ConversationContext, MumbleAbout, PostType, QueueEntry, ReplyTarget
from .relationships import RelationshipData

# 会話の深さに応じた無視確率
IGNORE_RATES = {
    1: 0.10,  # depth 1: 10% 無視
    2: 0.30,  # depth 2: 30% 無視
    3: 0.60,  # depth 3: 60% 無視
    4: 0.85,  # depth 4: 85% 無視
}
DEFAULT_IGNORE_RATE = 0.95  # depth 5+


# 会話を締める表現
CLOSING_PATTERNS = [
    "ありがとう",
    "サンキュー",
    "thx",
    "了解",
    "おk",
    "がんばって",
    "がんばる",
    "またね",
    "じゃあね",
    "うん！",
    "そうだね",
    "なるほど",
]


def calculate_ignore_probability(depth: int) -> float:
    """会話の深さに応じた無視確率を計算"""
    if depth == 0:
        return 0.0
    return IGNORE_RATES.get(depth, DEFAULT_IGNORE_RATE)


def is_closing_message(content: str) -> bool:
    """会話を締める内容か判定"""
    return any(p in content for p in CLOSING_PATTERNS)


class InteractionManager:
    """相互作用マネージャー"""

    def __init__(self, relationship_data: RelationshipData):
        self.relationship_data = relationship_data

    def should_react_to_post(
        self,
        from_bot: str,
        to_bot: str,
        post_content: str,
        affinity: float = 0.0,
        sociability: float = 0.5,
    ) -> tuple[bool, str | None]:
        """
        投稿に反応すべきか判定

        Args:
            from_bot: 反応する住人
            to_bot: 投稿した住人
            post_content: 投稿内容
            affinity: 好感度
            sociability: 社交性パラメータ（0.0〜1.0）

        Returns:
            (should_react, reaction_type): 反応するかどうかと反応タイプ
        """
        # 自分自身には反応しない
        if from_bot == to_bot:
            return False, None

        # 避ける関係なら反応しない
        if self.relationship_data.should_avoid(from_bot, to_bot):
            return False, None

        # リプライ確率を取得
        reply_prob = self.relationship_data.get_reply_probability(from_bot, to_bot)

        # 好感度による調整
        if affinity > 0.7:
            reply_prob *= 1.3
        elif affinity < 0.3:
            reply_prob *= 0.7

        # 社交性による調整（0.0→×0.5、0.5→×1.0、1.0→×1.5）
        sociability_factor = 0.5 + sociability
        reply_prob *= sociability_factor

        # 判定
        if random.random() < reply_prob:
            return True, "reply"

        # リアクション確率（リプライ確率の1.5倍程度）
        reaction_prob = reply_prob * 1.5
        if random.random() < reaction_prob:
            return True, "reaction"

        return False, None

    def should_continue_conversation(
        self,
        from_bot: str,
        to_bot: str,
        incoming_content: str,
        depth: int,
        affinity: float = 0.0,
    ) -> bool:
        """リプライに返信すべきか判定"""
        # 締めの表現なら終了
        if is_closing_message(incoming_content):
            return False

        # 深さによる無視確率
        ignore_prob = calculate_ignore_probability(depth)

        # 好感度による調整
        if affinity > 0.7:
            ignore_prob *= 0.7
        elif affinity < 0.3:
            ignore_prob *= 1.3

        # 最大でも95%
        ignore_prob = min(0.95, ignore_prob)

        return random.random() > ignore_prob

    def create_reply_entry(
        self,
        npc_id: int,
        npc_name: str,
        content: str,
        reply_to: ReplyTarget,
        conversation: ConversationContext | None = None,
    ) -> QueueEntry:
        """リプライ用のQueueEntryを作成"""
        # 会話コンテキストを更新
        if conversation is None:
            conversation = ConversationContext(
                thread_id=uuid.uuid4().hex[:8],
                depth=1,
                history=[
                    {
                        "author": reply_to.resident,
                        "content": reply_to.content,
                        "depth": 0,
                    }
                ],
            )
        else:
            # 履歴に追加
            new_history = conversation.history.copy()
            new_history.append(
                {
                    "author": reply_to.resident,
                    "content": reply_to.content,
                    "depth": conversation.depth,
                }
            )
            conversation = ConversationContext(
                thread_id=conversation.thread_id,
                depth=conversation.depth + 1,
                history=new_history,
            )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=npc_name,
            content=content,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    def create_reaction_entry(
        self,
        npc_id: int,
        npc_name: str,
        emoji: str,
        target_resident: str,
        target_event_id: str,
    ) -> QueueEntry:
        """リアクション用のQueueEntryを作成"""
        return QueueEntry(
            npc_id=npc_id,
            npc_name=npc_name,
            content=emoji,
            post_type=PostType.REACTION,
            reply_to=ReplyTarget(
                resident=target_resident,
                event_id=target_event_id,
                content="",  # リアクションでは元内容は不要
            ),
        )

    def create_mumble_entry(
        self,
        npc_id: int,
        npc_name: str,
        content: str,
        about: MumbleAbout,
    ) -> QueueEntry:
        """ぶつぶつ用のQueueEntryを作成"""
        return QueueEntry(
            npc_id=npc_id,
            npc_name=npc_name,
            content=content,
            post_type=PostType.MUMBLE,
            mumble_about=about,
        )

    def select_reaction_emoji(self, content: str, personality_type: str) -> str:
        """投稿内容と性格に応じたリアクション絵文字を選択"""
        # 内容に応じた絵文字
        if any(w in content for w in ["完成", "できた", "リリース", "公開"]):
            return random.choice(["🎉", "👏", "🙌", "✨"])
        if any(w in content for w in ["難しい", "困った", "つらい", "大変"]):
            return random.choice(["💪", "🤔", "😢", "頑張れ"])
        if any(w in content for w in ["新しい", "始めた", "挑戦"]):
            return random.choice(["👀", "✨", "🔥", "💪"])

        # 性格に応じたデフォルト絵文字
        personality_emojis = {
            "陽気": ["❤️", "✨", "🎉", "👍"],
            "真面目": ["👍", "✅", "📝"],
            "クール": ["👍", "👀"],
            "熱血": ["🔥", "💪", "👊"],
            "のんびり": ["☺️", "🌸", "✨"],
            "内気": ["👍", "✨"],
        }

        emojis = personality_emojis.get(personality_type, ["👍", "❤️", "✨"])
        return random.choice(emojis)
