"""
好感度サービス（好感度の更新・減衰処理）
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ..config import AffinitySettings
from ..domain import (
    NpcKey,
    NpcProfile,
    NpcState,
    PostType,
    QueueStatus,
    RelationshipData,
    format_npc_name,
)

if TYPE_CHECKING:
    NpcDataDict = dict[int, tuple[NpcKey, NpcProfile, NpcState]]
from ..infrastructure import QueueRepository, RelationshipRepository


class AffinityService:
    """好感度の更新・減衰を処理するサービス"""

    def __init__(
        self,
        relationship_repo: RelationshipRepository,
        queue_repo: QueueRepository,
        relationship_data: RelationshipData,
        affinity_settings: AffinitySettings | None = None,
    ):
        self.relationship_repo = relationship_repo
        self.queue_repo = queue_repo
        self.relationship_data = relationship_data
        self.affinity_settings = affinity_settings or AffinitySettings()

    def update_on_interaction(
        self,
        from_npc_id: int,
        to_npc_id: int,
        interaction_type: str,
    ) -> None:
        """
        相互作用発生時に好感度と親密度を更新

        Args:
            from_npc_id: 反応した側のNPC ID
            to_npc_id: 元投稿者のNPC ID（好感度が上がる側）
            interaction_type: "reply" or "reaction"
        """
        to_npc_name = format_npc_name(to_npc_id)
        from_npc_name = format_npc_name(from_npc_id)

        affinity = self.relationship_repo.load_affinity(to_npc_name)

        # 好感度を更新
        if interaction_type == "reply":
            affinity_delta = self.affinity_settings.delta_reply
            familiarity_delta = self.affinity_settings.familiarity_reply
        elif interaction_type == "reaction":
            affinity_delta = self.affinity_settings.delta_reaction
            familiarity_delta = self.affinity_settings.familiarity_reaction
        else:
            return

        old_affinity = affinity.get_affinity(from_npc_name)
        new_affinity = affinity.update_affinity(from_npc_name, affinity_delta)

        # 親密度を更新（双方向）
        old_familiarity = affinity.get_familiarity(from_npc_name)
        new_familiarity = affinity.update_familiarity(from_npc_name, familiarity_delta)

        # 最後の相互作用日時を記録
        affinity.record_interaction(from_npc_name, datetime.now().isoformat())

        # 保存
        self.relationship_repo.save_affinity(affinity)

        # 反応した側も親密度を更新
        from_affinity = self.relationship_repo.load_affinity(from_npc_name)
        from_affinity.update_familiarity(to_npc_name, familiarity_delta)
        from_affinity.record_interaction(to_npc_name, datetime.now().isoformat())
        self.relationship_repo.save_affinity(from_affinity)

        # ログ出力
        if new_affinity != old_affinity:
            print(
                f"         📈 {to_npc_name}の{from_npc_name}への好感度: "
                f"{old_affinity:.2f} → {new_affinity:.2f}"
            )
        if new_familiarity != old_familiarity:
            print(
                f"         🤝 {to_npc_name}と{from_npc_name}の親密度: "
                f"{old_familiarity:.2f} → {new_familiarity:.2f}"
            )

    def process_decay(self, target_npc_ids: list[int], npcs: NpcDataDict) -> int:
        """
        好感度の減衰処理を実行（疎遠期間による減衰）

        1週間以上相互作用がない関係について好感度を減衰させる。

        Args:
            target_npc_ids: 処理対象の住人ID一覧
            npcs: NPCデータ辞書

        Returns:
            減衰が発生した関係の数
        """
        decayed_count = 0
        now = datetime.now()
        one_week_ago = now - timedelta(weeks=1)

        for npc_id in target_npc_ids:
            if npc_id not in npcs:
                continue

            npc_name = format_npc_name(npc_id)
            affinity = self.relationship_repo.load_affinity(npc_name)
            updated = False

            # 関係のある住人を取得
            related_members = self.relationship_data.get_related_members(npc_name)

            for target_name in related_members:
                # 最後の相互作用日時を確認
                last_interaction = affinity.get_last_interaction(target_name)

                if last_interaction:
                    try:
                        last_dt = datetime.fromisoformat(last_interaction)
                        if last_dt < one_week_ago:
                            # 1週間以上相互作用がない → 減衰
                            old_value = affinity.get_affinity(target_name)
                            new_value = affinity.update_affinity(
                                target_name, self.affinity_settings.decay_weekly
                            )
                            if new_value != old_value:
                                decayed_count += 1
                                updated = True
                    except ValueError:
                        pass

            if updated:
                self.relationship_repo.save_affinity(affinity)

        return decayed_count

    def process_ignored_posts(self, target_npc_ids: list[int]) -> int:
        """
        無視された投稿による好感度減衰を処理

        関係者がいるのに誰からも反応がなかった投稿について、
        投稿者の関係者への好感度を微減させる。

        Args:
            target_npc_ids: 処理対象の住人ID一覧

        Returns:
            減衰が発生した数
        """
        decayed_count = 0

        # 投稿済みエントリーを取得（通常投稿のみ）
        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)
        normal_posts = [
            e
            for e in posted_entries
            if e.post_type == PostType.NORMAL and e.npc_id in target_npc_ids
        ]

        for entry in normal_posts:
            if not entry.event_id:
                continue

            npc_name = format_npc_name(entry.npc_id)

            # この投稿へのリプライ/リアクションがあるかチェック
            has_reaction = self._has_any_reaction(entry.event_id)

            if has_reaction:
                continue

            # 反応がない場合、関係者への好感度を微減
            related_members = self.relationship_data.get_related_members(npc_name)

            if not related_members:
                continue

            affinity = self.relationship_repo.load_affinity(npc_name)
            updated = False

            for target_name in related_members:
                old_value = affinity.get_affinity(target_name)
                new_value = affinity.update_affinity(
                    target_name, self.affinity_settings.delta_ignored
                )
                if new_value != old_value:
                    decayed_count += 1
                    updated = True

            if updated:
                self.relationship_repo.save_affinity(affinity)

        return decayed_count

    def _has_any_reaction(self, event_id: str) -> bool:
        """指定イベントへの反応（リプライ/リアクション）があるかチェック"""
        for status in [QueueStatus.PENDING, QueueStatus.APPROVED, QueueStatus.POSTED]:
            entries = self.queue_repo.get_all(status)
            for entry in entries:
                if entry.reply_to and entry.reply_to.event_id == event_id:
                    return True
        return False
