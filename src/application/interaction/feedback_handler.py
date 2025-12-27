"""
フィードバック処理（記憶・気分・状態パラメータ・ログ更新）
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

# 状態パラメータの変動量
STATE_CHANGES: dict[str, dict[str, float]] = {
    "reply": {
        "motivation": 0.1,
        "excitement": 0.15,
        "mental_health": 0.05,
    },
    "reaction": {
        "motivation": 0.05,
        "excitement": 0.08,
        "mental_health": 0.02,
    },
    "post": {
        "energy": -0.05,
        "fatigue": 0.03,
    },
    "ignored": {
        "motivation": -0.05,
        "mental_health": -0.02,
    },
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

    def update_state_on_feedback(
        self,
        npc_id: int,
        interaction_type: str,
    ) -> list[ParameterChange]:
        """
        リプライ/リアクションをもらった時に状態パラメータを更新

        Args:
            npc_id: 元投稿者のNPC ID
            interaction_type: "reply" or "reaction"

        Returns:
            変更されたパラメータのリスト
        """
        if npc_id not in self.npcs:
            return []

        changes = STATE_CHANGES.get(interaction_type, {})
        if not changes:
            return []

        _, profile, state = self.npcs[npc_id]
        sensitivity = self._get_feedback_sensitivity(npc_id)
        result = []

        for param, delta in changes.items():
            old_value = getattr(state, param, None)
            if old_value is None:
                continue

            # feedback_sensitivityで変動量を調整
            adjusted_delta = delta * (0.5 + sensitivity)
            new_value = max(0.0, min(1.0, old_value + adjusted_delta))

            if new_value != old_value:
                setattr(state, param, new_value)
                result.append(
                    ParameterChange(
                        name=param,
                        old_value=old_value,
                        new_value=new_value,
                        reason=f"{interaction_type}を受けた",
                    )
                )

        return result

    def update_state_on_post(self, npc_id: int, hour: int) -> list[ParameterChange]:
        """
        投稿時に状態パラメータを更新

        Args:
            npc_id: 投稿したNPC ID
            hour: 現在の時刻（0-23）

        Returns:
            変更されたパラメータのリスト
        """
        if npc_id not in self.npcs:
            return []

        _, profile, state = self.npcs[npc_id]
        result = []
        changes = STATE_CHANGES.get("post", {})

        for param, delta in changes.items():
            old_value = getattr(state, param, None)
            if old_value is None:
                continue

            # 深夜（0-5時）は疲労が増えやすい
            if param == "fatigue" and (hour < 5 or hour >= 23):
                delta *= 1.5

            new_value = max(0.0, min(1.0, old_value + delta))
            if new_value != old_value:
                setattr(state, param, new_value)
                result.append(
                    ParameterChange(
                        name=param,
                        old_value=old_value,
                        new_value=new_value,
                        reason="投稿した",
                    )
                )

        return result

    def update_state_on_time(self, npc_id: int, hour: int) -> list[ParameterChange]:
        """
        時間経過による状態パラメータの更新

        Args:
            npc_id: NPC ID
            hour: 現在の時刻（0-23）

        Returns:
            変更されたパラメータのリスト
        """
        if npc_id not in self.npcs:
            return []

        _, profile, state = self.npcs[npc_id]
        result = []

        # エネルギー: 昼間（6-18時）は回復、深夜は低下
        old_energy = state.energy
        if 6 <= hour < 18:
            state.energy = min(1.0, state.energy + 0.02)
        elif hour < 5 or hour >= 23:
            state.energy = max(0.0, state.energy - 0.02)

        if state.energy != old_energy:
            result.append(
                ParameterChange(
                    name="energy",
                    old_value=old_energy,
                    new_value=state.energy,
                    reason="時間経過",
                )
            )

        # 疲労: 時間経過で回復（休息）
        old_fatigue = state.fatigue
        state.fatigue = max(0.0, state.fatigue - 0.01)
        if state.fatigue != old_fatigue:
            result.append(
                ParameterChange(
                    name="fatigue",
                    old_value=old_fatigue,
                    new_value=state.fatigue,
                    reason="時間経過",
                )
            )

        # 興奮度: 時間経過で減衰
        old_excitement = state.excitement
        state.excitement = max(0.0, state.excitement - 0.02)
        if state.excitement != old_excitement:
            result.append(
                ParameterChange(
                    name="excitement",
                    old_value=old_excitement,
                    new_value=state.excitement,
                    reason="時間経過",
                )
            )

        return result

    def update_state_on_ignored(self, npc_id: int) -> list[ParameterChange]:
        """
        投稿が無視された時に状態パラメータを更新

        Args:
            npc_id: 無視されたNPC ID

        Returns:
            変更されたパラメータのリスト
        """
        if npc_id not in self.npcs:
            return []

        _, profile, state = self.npcs[npc_id]
        sensitivity = self._get_feedback_sensitivity(npc_id)
        result = []
        changes = STATE_CHANGES.get("ignored", {})

        for param, delta in changes.items():
            old_value = getattr(state, param, None)
            if old_value is None:
                continue

            # 反応への感度が高いほど影響が大きい
            adjusted_delta = delta * (0.5 + sensitivity)
            new_value = max(0.0, min(1.0, old_value + adjusted_delta))

            if new_value != old_value:
                setattr(state, param, new_value)
                result.append(
                    ParameterChange(
                        name=param,
                        old_value=old_value,
                        new_value=new_value,
                        reason="投稿が無視された",
                    )
                )

        return result

    def update_focus_on_series(self, npc_id: int, in_series: bool) -> list[ParameterChange]:
        """
        連作状態に応じて集中度を更新

        Args:
            npc_id: NPC ID
            in_series: 連作中かどうか

        Returns:
            変更されたパラメータのリスト
        """
        if npc_id not in self.npcs:
            return []

        _, _, state = self.npcs[npc_id]
        result = []
        old_focus = state.focus

        if in_series:
            # 連作中は集中度が上がる
            state.focus = min(1.0, state.focus + 0.1)
        else:
            # 連作終了で集中度が下がる
            state.focus = max(0.0, state.focus - 0.15)

        if state.focus != old_focus:
            result.append(
                ParameterChange(
                    name="focus",
                    old_value=old_focus,
                    new_value=state.focus,
                    reason="連作中" if in_series else "連作終了",
                )
            )

        return result

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
