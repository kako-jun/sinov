"""
投稿キューのモデル
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class QueueStatus(str, Enum):
    """キューのステータス"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTED = "posted"
    DRY_RUN = "dry_run"


class PostType(str, Enum):
    """投稿の種類"""

    NORMAL = "normal"  # 通常のつぶやき
    REPLY = "reply"  # リプライ
    REACTION = "reaction"  # リアクション（絵文字）
    MUMBLE = "mumble"  # ぶつぶつ（引用なしで言及）
    QUOTE = "quote"  # 引用


class ReplyTarget(BaseModel):
    """リプライ先の情報"""

    resident: str = Field(description="リプライ先のボットID（bot001形式）またはexternal:xxx")
    event_id: str = Field(description="リプライ先のNostrイベントID")
    content: str = Field(description="リプライ先の投稿内容")
    pubkey: str | None = Field(default=None, description="外部ユーザーの場合のpubkey")


class ConversationContext(BaseModel):
    """会話スレッドのコンテキスト"""

    thread_id: str = Field(description="スレッドID")
    depth: int = Field(default=0, ge=0, description="会話の深さ（0=元投稿）")
    history: list[dict[str, str | int]] = Field(
        default_factory=list, description="会話履歴（author, content, depth）"
    )


class MumbleAbout(BaseModel):
    """ぶつぶつの対象"""

    type: str = Field(default="internal", description="対象の種類（internal/external）")
    resident: str | None = Field(default=None, description="内部住人のボットID")
    pubkey: str | None = Field(default=None, description="外部NostrアカウントのPubkey")
    display_name: str = Field(description="表示名")
    original_content: str = Field(description="元の投稿内容")


class QueueEntry(BaseModel):
    """キューエントリー（投稿候補）"""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    bot_id: int = Field(gt=0, description="ボットID")
    bot_name: str = Field(min_length=1, description="ボット名")
    content: str = Field(min_length=1, description="投稿内容")
    created_at: datetime = Field(default_factory=datetime.now)
    status: QueueStatus = Field(default=QueueStatus.PENDING)
    reviewed_at: datetime | None = Field(default=None)
    review_note: str | None = Field(default=None, description="レビューコメント")
    posted_at: datetime | None = Field(default=None)
    event_id: str | None = Field(default=None, description="NostrイベントID")

    # 投稿タイプ関連（拡張）
    post_type: PostType = Field(default=PostType.NORMAL, description="投稿の種類")
    reply_to: ReplyTarget | None = Field(default=None, description="リプライ先")
    conversation: ConversationContext | None = Field(default=None, description="会話コンテキスト")
    mumble_about: MumbleAbout | None = Field(default=None, description="ぶつぶつの対象")
