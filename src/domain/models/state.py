"""
NPC状態・鍵関連のモデル
"""

import os

from pydantic import BaseModel, Field


class NpcKey(BaseModel):
    """NPCの鍵情報"""

    id: int = Field(gt=0, description="NPC ID")
    name: str = Field(min_length=1, description="NPC名")
    pubkey: str = Field(min_length=64, max_length=64, description="公開鍵")
    nsec: str = Field(pattern=r"^nsec1[a-z0-9]+$", description="秘密鍵")

    @classmethod
    def from_env(cls, npc_id: int) -> "NpcKey":
        """環境変数からNPCキーを読み込み"""
        npc_id_str = f"{npc_id:03d}"
        pubkey = os.getenv(f"NPC_{npc_id_str}_PUBKEY")
        nsec = os.getenv(f"NPC_{npc_id_str}_NSEC")

        if not pubkey or not nsec:
            raise ValueError(f"Keys not found for NPC {npc_id_str} in environment variables")

        return cls(
            id=npc_id,
            name=f"npc{npc_id_str}",
            pubkey=pubkey,
            nsec=nsec,
        )


class NpcState(BaseModel):
    """NPCの状態（実行時）"""

    id: int = Field(gt=0, description="NPC ID")
    last_post_time: int = Field(ge=0, description="最後の投稿時刻")
    next_post_time: int = Field(ge=0, description="次回投稿時刻")
    total_posts: int = Field(ge=0, description="累計投稿数")
    last_post_content: str | None = Field(default=None, description="最後の投稿内容")
    last_event_id: str | None = Field(default=None, description="最後の投稿のイベントID")
    post_history: list[str] = Field(default_factory=list, description="過去の投稿内容（最新20件）")
    discovered_topics: list[str] = Field(
        default_factory=list, description="新しく興味を持ったトピック"
    )
    # 気分（-1.0〜1.0、負がネガティブ、正がポジティブ）
    mood: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="現在の気分（-1.0〜1.0）",
    )
    # 追加の状態パラメータ（0.0〜1.0）
    energy: float = Field(default=0.5, ge=0.0, le=1.0, description="エネルギー")
    focus: float = Field(default=0.5, ge=0.0, le=1.0, description="集中度")
    motivation: float = Field(default=0.5, ge=0.0, le=1.0, description="モチベーション")
    fatigue: float = Field(default=0.0, ge=0.0, le=1.0, description="疲労度")
    excitement: float = Field(default=0.0, ge=0.0, le=1.0, description="興奮度")
    mental_health: float = Field(default=0.7, ge=0.0, le=1.0, description="メンタル")


class TickState(BaseModel):
    """tickコマンドのラウンドロビン状態"""

    next_index: int = Field(default=0, ge=0, description="次に処理するNPCのインデックス")
    last_run_at: str | None = Field(default=None, description="最後の実行時刻（ISO形式）")
    total_ticks: int = Field(default=0, ge=0, description="累計tick回数")
