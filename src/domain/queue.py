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
