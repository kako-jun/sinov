"""
関係性システム

グループ、個人間の関係、ストーカー、好感度を管理する。
"""

from enum import Enum

from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    """関係の種類"""

    CLOSE_FRIENDS = "close_friends"  # 親しい友人
    COUPLE = "couple"  # 夫婦・カップル
    SIBLINGS = "siblings"  # 兄弟姉妹
    RIVALS = "rivals"  # ライバル
    AWKWARD = "awkward"  # 気まずい関係（絡まない）
    MENTOR = "mentor"  # 師弟関係


class GroupInteraction(BaseModel):
    """グループ内の相互作用設定"""

    reply_probability: float = Field(default=0.15, ge=0.0, le=1.0, description="リプライ確率")
    reaction_probability: float = Field(default=0.3, ge=0.0, le=1.0, description="リアクション確率")
    topics: list[str] = Field(default_factory=list, description="共通の話題")


class Group(BaseModel):
    """仲良しグループ"""

    id: str = Field(description="グループID")
    name: str = Field(description="グループ名")
    members: list[str] = Field(description="メンバーのNPC ID（npc001形式）")
    description: str | None = Field(default=None, description="グループの説明")
    interaction: GroupInteraction = Field(
        default_factory=GroupInteraction, description="相互作用設定"
    )


class PairInteraction(BaseModel):
    """個人間の相互作用設定"""

    reply_probability: float = Field(default=0.2, ge=0.0, le=1.0, description="リプライ確率")
    tone: str = Field(default="friendly", description="会話のトーン")
    topics: list[str] = Field(default_factory=list, description="共通の話題")
    avoid: bool = Field(default=False, description="避けるかどうか（awkward関係）")


class Pair(BaseModel):
    """個人間の関係"""

    id: str = Field(description="関係ID")
    type: RelationshipType = Field(description="関係の種類")
    members: list[str] = Field(min_length=2, max_length=2, description="2人のNPC ID")
    description: str | None = Field(default=None, description="関係の説明")
    interaction: PairInteraction = Field(
        default_factory=PairInteraction, description="相互作用設定"
    )


class StalkerReaction(BaseModel):
    """ストーカーの反応パターン"""

    type: str = Field(description="反応タイプ（mumble, comment, support）")
    probability: float = Field(ge=0.0, le=1.0, description="発生確率")
    description: str | None = Field(default=None, description="反応の説明")
    examples: list[str] = Field(default_factory=list, description="反応例")


class StalkerTarget(BaseModel):
    """ストーカーのターゲット"""

    type: str = Field(default="external_nostr", description="ターゲットの種類")
    pubkey: str | None = Field(default=None, description="NostrのPubkey")
    display_name: str = Field(description="表示名")


class StalkerBehavior(BaseModel):
    """ストーカーの行動設定"""

    check_interval_minutes: int = Field(default=60, description="チェック間隔（分）")
    reaction_probability: float = Field(default=0.3, ge=0.0, le=1.0, description="反応確率")
    reactions: list[StalkerReaction] = Field(default_factory=list, description="反応パターン")


class Stalker(BaseModel):
    """ストーカー定義"""

    id: str = Field(description="ストーカーID")
    resident: str = Field(description="ストーカー役のNPC ID")
    display_name: str = Field(description="表示名")
    target: StalkerTarget = Field(description="ターゲット")
    behavior: StalkerBehavior = Field(default_factory=StalkerBehavior, description="行動設定")
    quirks: list[str] = Field(default_factory=list, description="ストーカーらしい癖")
    constraints: list[str] = Field(default_factory=list, description="NGルール")


class Affinity(BaseModel):
    """好感度・信頼度・親密度（住人間の関係値）"""

    npc_id: str = Field(description="この住人のNPC ID")
    targets: dict[str, float] = Field(
        default_factory=dict,
        description="対象NPC IDと好感度のマップ（-1.0〜1.0）",
    )
    last_interactions: dict[str, str] = Field(
        default_factory=dict,
        description="対象NPC IDと最後の相互作用日時のマップ（ISO形式）",
    )
    # 信頼度（約束を守る、頼りになる等）
    trust: dict[str, float] = Field(
        default_factory=dict,
        description="対象NPC IDと信頼度のマップ（0.0〜1.0）",
    )
    # 親密度（どれだけ知り合いか）
    familiarity: dict[str, float] = Field(
        default_factory=dict,
        description="対象NPC IDと親密度のマップ（0.0〜1.0）",
    )

    def get_affinity(self, target_id: str) -> float:
        """対象への好感度を取得（デフォルト0.0）"""
        return self.targets.get(target_id, 0.0)

    def update_affinity(self, target_id: str, delta: float) -> float:
        """好感度を更新（範囲制限あり）"""
        current = self.targets.get(target_id, 0.0)
        new_value = max(-1.0, min(1.0, current + delta))
        self.targets[target_id] = new_value
        return new_value

    def set_affinity(self, target_id: str, value: float) -> None:
        """好感度を設定"""
        self.targets[target_id] = max(-1.0, min(1.0, value))

    def record_interaction(self, target_id: str, timestamp: str) -> None:
        """最後の相互作用日時を記録"""
        self.last_interactions[target_id] = timestamp

    def get_last_interaction(self, target_id: str) -> str | None:
        """最後の相互作用日時を取得"""
        return self.last_interactions.get(target_id)

    def get_trust(self, target_id: str) -> float:
        """対象への信頼度を取得（デフォルト0.5）"""
        return self.trust.get(target_id, 0.5)

    def update_trust(self, target_id: str, delta: float) -> float:
        """信頼度を更新（範囲制限あり）"""
        current = self.trust.get(target_id, 0.5)
        new_value = max(0.0, min(1.0, current + delta))
        self.trust[target_id] = new_value
        return new_value

    def get_familiarity(self, target_id: str) -> float:
        """対象との親密度を取得（デフォルト0.0）"""
        return self.familiarity.get(target_id, 0.0)

    def update_familiarity(self, target_id: str, delta: float) -> float:
        """親密度を更新（範囲制限あり）"""
        current = self.familiarity.get(target_id, 0.0)
        new_value = max(0.0, min(1.0, current + delta))
        self.familiarity[target_id] = new_value
        return new_value


class RelationshipData(BaseModel):
    """関係性データ全体"""

    groups: list[Group] = Field(default_factory=list, description="グループ一覧")
    pairs: list[Pair] = Field(default_factory=list, description="個人間関係一覧")
    stalkers: list[Stalker] = Field(default_factory=list, description="ストーカー一覧")

    def get_related_members(self, npc_id: str) -> list[str]:
        """指定NPCと関係のある全メンバーを取得"""
        related = set()

        # グループメンバー
        for group in self.groups:
            if npc_id in group.members:
                for member in group.members:
                    if member != npc_id:
                        related.add(member)

        # ペア
        for pair in self.pairs:
            if npc_id in pair.members:
                for member in pair.members:
                    if member != npc_id:
                        related.add(member)

        return list(related)

    def get_groups_for_bot(self, npc_id: str) -> list[Group]:
        """指定NPCが所属するグループを取得"""
        return [g for g in self.groups if npc_id in g.members]

    def get_pairs_for_bot(self, npc_id: str) -> list[Pair]:
        """指定NPCが関係する個人間関係を取得"""
        return [p for p in self.pairs if npc_id in p.members]

    def get_reply_probability(self, from_bot: str, to_bot: str) -> float:
        """2人のNPC間のリプライ確率を取得"""
        max_prob = 0.0

        # グループ確率
        for group in self.groups:
            if from_bot in group.members and to_bot in group.members:
                max_prob = max(max_prob, group.interaction.reply_probability)

        # ペア確率（より優先）
        for pair in self.pairs:
            if from_bot in pair.members and to_bot in pair.members:
                if pair.interaction.avoid:
                    return 0.0  # 避ける関係
                max_prob = max(max_prob, pair.interaction.reply_probability)

        return max_prob

    def should_avoid(self, from_bot: str, to_bot: str) -> bool:
        """2人が避ける関係かどうか"""
        for pair in self.pairs:
            if from_bot in pair.members and to_bot in pair.members:
                if pair.type == RelationshipType.AWKWARD or pair.interaction.avoid:
                    return True
        return False
