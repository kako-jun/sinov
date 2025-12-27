"""
フィードバック処理（記憶・気分・ログ更新）
"""

from datetime import datetime
from typing import TYPE_CHECKING

from ...config import AffinitySettings
from ...domain import (
    ActivityLogger,
    NpcKey,
    NpcProfile,
    NpcState,
    ParameterChange,
)
from ...infrastructure import LogRepository, MemoryRepository

if TYPE_CHECKING:
    from ...domain import NpcMemory

# インタラクションタイプごとの記憶強化量
INTERACTION_BOOST: dict[str, float] = {
    "reply": 0.3,  # リプライは強い反応
    "reaction": 0.15,  # リアクションは軽い反応
}


class FeedbackHandler:
    """リプライ/リアクションのフィードバック処理を担当"""

    def __init__(
        self,
        memory_repo: MemoryRepository | None,
        log_repo: LogRepository | None,
        affinity_settings: AffinitySettings,
        npcs: dict[int, tuple[NpcKey, NpcProfile, NpcState]],
    ):
        self.memory_repo = memory_repo
        self.log_repo = log_repo
        self.affinity_settings = affinity_settings
        self.npcs = npcs

    def update_memory_on_feedback(
        self,
        npc_id: int,
        original_content: str,
        interaction_type: str,
    ) -> None:
        """
        リプライ/リアクションをもらった時に記憶を強化

        Args:
            npc_id: 元投稿者のNPC ID（記憶が強化される側）
            original_content: 元投稿の内容
            interaction_type: "reply" or "reaction"
        """
        if not self.memory_repo:
            return

        boost = INTERACTION_BOOST.get(interaction_type)
        if boost is None:
            return

        memory = self.memory_repo.load(npc_id)
        sensitivity = self._get_feedback_sensitivity(npc_id)
        reinforced = self._reinforce_memory(memory, original_content, boost, sensitivity)
        promoted = memory.check_and_promote(threshold=0.95)

        if reinforced or promoted:
            memory.last_updated = datetime.now().isoformat()
            self.memory_repo.save(memory)

        for content in promoted:
            print(f"         🧠 長期記憶に昇格: {content[:30]}...")

    def _get_feedback_sensitivity(self, npc_id: int) -> float:
        """feedback_sensitivityを取得"""
        if npc_id not in self.npcs:
            return 0.5
        _, profile, _ = self.npcs[npc_id]
        if profile.traits_detail:
            return profile.traits_detail.feedback_sensitivity
        return 0.5

    def _reinforce_memory(
        self, memory: "NpcMemory", content: str, boost: float, sensitivity: float
    ) -> bool:
        """関連する短期記憶を強化"""
        keywords = content.split()[:5]
        reinforced = False

        for keyword in keywords:
            if len(keyword) >= 2:
                if memory.reinforce_short_term(keyword, boost, sensitivity):
                    reinforced = True

        if memory.reinforce_short_term(content[:20], boost, sensitivity):
            reinforced = True

        return reinforced

    def update_mood_on_feedback(
        self,
        npc_id: int,
        interaction_type: str,
    ) -> None:
        """
        リプライ/リアクションをもらった時に気分を更新

        Args:
            npc_id: 元投稿者のNPC ID（気分が上がる側）
            interaction_type: "reply" or "reaction"
        """
        if npc_id not in self.npcs:
            return

        key, profile, state = self.npcs[npc_id]

        # 気分の変動量
        if interaction_type == "reply":
            delta = self.affinity_settings.mood_reply
        elif interaction_type == "reaction":
            delta = self.affinity_settings.mood_reaction
        else:
            return

        old_mood = state.mood
        new_mood = max(-1.0, min(1.0, state.mood + delta))
        state.mood = new_mood

        # NPCデータを更新（stateは参照なので自動的に反映）
        if new_mood != old_mood:
            print(f"         😊 bot{npc_id:03d}の気分: {old_mood:.2f} → {new_mood:.2f}")

    def get_mood(self, npc_id: int) -> float:
        """NPCの現在の気分を取得"""
        if npc_id not in self.npcs:
            return 0.0
        _, _, state = self.npcs[npc_id]
        return state.mood

    def log_reply_interaction(
        self,
        sender_npc_id: int,
        receiver_npc_id: int,
        sender_name: str,
        receiver_name: str,
        content: str,
        relationship_type: str,
        old_affinity: float,
        new_affinity: float,
        old_mood: float,
        new_mood: float,
    ) -> None:
        """リプライ相互作用のログを記録"""
        if not self.log_repo:
            return

        # 送信側のログ（リプライ送信）
        self.log_repo.add_entry(
            sender_npc_id,
            ActivityLogger.log_reply_sent(
                receiver_name,
                content,
                relationship_type,
            ),
        )

        # 受信側のログ（リプライ受信 + パラメータ変化）
        changes = []
        if old_affinity != new_affinity:
            changes.append(
                ParameterChange(
                    name="好感度",
                    old_value=old_affinity,
                    new_value=new_affinity,
                    reason="リプライを受けた",
                    target=sender_name,
                )
            )
        if old_mood != new_mood:
            changes.append(
                ParameterChange(
                    name="気分",
                    old_value=old_mood,
                    new_value=new_mood,
                    reason="リプライを受けた",
                )
            )
        self.log_repo.add_entry(
            receiver_npc_id,
            ActivityLogger.log_reply_received(
                sender_name,
                content,
                relationship_type,
                changes,
            ),
        )

    def log_reaction_interaction(
        self,
        sender_npc_id: int,
        receiver_npc_id: int,
        sender_name: str,
        original_content: str,
        emoji: str,
        old_affinity: float,
        new_affinity: float,
        old_mood: float,
        new_mood: float,
    ) -> None:
        """リアクション相互作用のログを記録"""
        if not self.log_repo:
            return

        # 送信側のログ
        self.log_repo.add_entry(
            sender_npc_id,
            ActivityLogger.log_reaction_sent(f"npc{receiver_npc_id:03d}", emoji, original_content),
        )

        # 受信側のログ
        changes = []
        if old_affinity != new_affinity:
            changes.append(
                ParameterChange(
                    name="好感度",
                    old_value=old_affinity,
                    new_value=new_affinity,
                    reason="リアクションを受けた",
                    target=sender_name,
                )
            )
        if old_mood != new_mood:
            changes.append(
                ParameterChange(
                    name="気分",
                    old_value=old_mood,
                    new_value=new_mood,
                    reason="リアクションを受けた",
                )
            )
        self.log_repo.add_entry(
            receiver_npc_id,
            ActivityLogger.log_reaction_received(sender_name, emoji, original_content, changes),
        )
