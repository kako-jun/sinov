"""
関係性リポジトリ

グループ、ペア、ストーカー、好感度の永続化を担当。
"""

import json
from pathlib import Path

import yaml

from ...domain import (
    Affinity,
    Group,
    GroupInteraction,
    Pair,
    PairInteraction,
    RelationshipData,
    Stalker,
    StalkerBehavior,
    StalkerReaction,
    StalkerTarget,
)

# 関係タイプから好感度への変換マップ
PAIR_TYPE_AFFINITY: dict[str, float] = {
    "close_friends": 0.5,
    "couple": 0.8,
    "siblings": 0.6,
    "rivals": 0.2,
    "awkward": -0.3,
}


class RelationshipRepository:
    """関係性データの永続化"""

    def __init__(self, relationships_dir: Path):
        self.relationships_dir = relationships_dir
        self.groups_file = relationships_dir / "groups.yaml"
        self.pairs_file = relationships_dir / "pairs.yaml"
        self.stalkers_file = relationships_dir / "stalkers.yaml"
        self.affinity_dir = relationships_dir / "affinity"

        # ディレクトリ作成
        self.relationships_dir.mkdir(parents=True, exist_ok=True)
        self.affinity_dir.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> RelationshipData:
        """全関係性データを読み込み"""
        groups = self._load_groups()
        pairs = self._load_pairs()
        stalkers = self._load_stalkers()

        return RelationshipData(groups=groups, pairs=pairs, stalkers=stalkers)

    def _load_groups(self) -> list[Group]:
        """グループを読み込み"""
        if not self.groups_file.exists():
            return []

        with open(self.groups_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        groups_data = data.get("groups", [])
        groups = []

        for g in groups_data:
            interaction_data = g.get("interaction", {})
            interaction = GroupInteraction(
                reply_probability=interaction_data.get("reply_probability", 0.15),
                reaction_probability=interaction_data.get("reaction_probability", 0.3),
                topics=interaction_data.get("topics", []),
            )
            groups.append(
                Group(
                    id=g["id"],
                    name=g["name"],
                    members=g.get("members", []),
                    description=g.get("description"),
                    interaction=interaction,
                )
            )

        return groups

    def _load_pairs(self) -> list[Pair]:
        """個人間関係を読み込み"""
        if not self.pairs_file.exists():
            return []

        with open(self.pairs_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        pairs_data = data.get("pairs", [])
        pairs = []

        for p in pairs_data:
            interaction_data = p.get("interaction", {})
            interaction = PairInteraction(
                reply_probability=interaction_data.get("reply_probability", 0.2),
                tone=interaction_data.get("tone", "friendly"),
                topics=interaction_data.get("topics", []),
                avoid=interaction_data.get("avoid", False),
            )
            pairs.append(
                Pair(
                    id=p["id"],
                    type=p["type"],
                    members=p["members"],
                    description=p.get("description"),
                    interaction=interaction,
                )
            )

        return pairs

    def _load_stalkers(self) -> list[Stalker]:
        """ストーカーを読み込み"""
        if not self.stalkers_file.exists():
            return []

        with open(self.stalkers_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        stalkers_data = data.get("stalkers") or []
        stalkers = []

        for s in stalkers_data:
            target_data = s.get("target", {})
            target = StalkerTarget(
                type=target_data.get("type", "external_nostr"),
                pubkey=target_data.get("pubkey"),
                display_name=target_data.get("display_name", "Unknown"),
            )

            behavior_data = s.get("behavior", {})
            reactions = [
                StalkerReaction(
                    type=r["type"],
                    probability=r.get("probability", 0.3),
                    description=r.get("description"),
                    examples=r.get("examples", []),
                )
                for r in behavior_data.get("reactions", [])
            ]
            behavior = StalkerBehavior(
                check_interval_minutes=behavior_data.get("check_interval_minutes", 60),
                reaction_probability=behavior_data.get("reaction_probability", 0.3),
                reactions=reactions,
            )

            stalkers.append(
                Stalker(
                    id=s["id"],
                    resident=s["resident"],
                    display_name=s.get("display_name", ""),
                    target=target,
                    behavior=behavior,
                    quirks=s.get("quirks", []),
                    constraints=s.get("constraints", []),
                )
            )

        return stalkers

    def load_stalkers(self) -> list[Stalker]:
        """ストーカー定義を読み込み（公開メソッド）"""
        return self._load_stalkers()

    def load_affinity(self, npc_id: str) -> Affinity:
        """指定NPCの好感度を読み込み"""
        affinity_file = self.affinity_dir / f"{npc_id}.json"

        if not affinity_file.exists():
            return Affinity(npc_id=npc_id)

        with open(affinity_file, encoding="utf-8") as f:
            data = json.load(f)

        return Affinity(
            npc_id=data.get("npc_id", npc_id),
            targets=data.get("targets", {}),
            last_interactions=data.get("last_interactions", {}),
        )

    def save_affinity(self, affinity: Affinity) -> None:
        """好感度を保存"""
        affinity_file = self.affinity_dir / f"{affinity.npc_id}.json"

        with open(affinity_file, "w", encoding="utf-8") as f:
            json.dump(affinity.model_dump(), f, ensure_ascii=False, indent=2)

    def load_all_affinities(self) -> dict[str, Affinity]:
        """全NPCの好感度を読み込み"""
        affinities: dict[str, Affinity] = {}

        if not self.affinity_dir.exists():
            return affinities

        for affinity_file in self.affinity_dir.glob("*.json"):
            npc_id = affinity_file.stem
            affinities[npc_id] = self.load_affinity(npc_id)

        return affinities

    def initialize_affinities_from_relationships(self, relationship_data: RelationshipData) -> None:
        """関係性データから好感度の初期値を設定"""
        all_bots = self._collect_all_bots(relationship_data)

        for npc_id in all_bots:
            affinity = self.load_affinity(npc_id)
            self._init_group_affinities(affinity, npc_id, relationship_data.groups)
            self._init_pair_affinities(affinity, npc_id, relationship_data.pairs)
            self.save_affinity(affinity)

    def _collect_all_bots(self, relationship_data: RelationshipData) -> set[str]:
        """全NPC IDを収集"""
        all_bots: set[str] = set()
        for group in relationship_data.groups:
            all_bots.update(group.members)
        for pair in relationship_data.pairs:
            all_bots.update(pair.members)
        return all_bots

    def _init_group_affinities(self, affinity: Affinity, npc_id: str, groups: list[Group]) -> None:
        """グループメンバーとの好感度を初期化"""
        for group in groups:
            if npc_id in group.members:
                for member in group.members:
                    if member != npc_id and member not in affinity.targets:
                        affinity.set_affinity(member, 0.3)

    def _init_pair_affinities(self, affinity: Affinity, npc_id: str, pairs: list[Pair]) -> None:
        """ペアとの好感度を初期化"""
        for pair in pairs:
            if npc_id not in pair.members:
                continue
            other = next(m for m in pair.members if m != npc_id)
            if other in affinity.targets:
                continue
            base_affinity = PAIR_TYPE_AFFINITY.get(pair.type.value)
            if base_affinity is not None:
                affinity.set_affinity(other, base_affinity)
