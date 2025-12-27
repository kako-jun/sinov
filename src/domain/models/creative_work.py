"""
制作物関連のモデル
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreativeWork(BaseModel):
    """制作物（進行中のプロジェクト）"""

    id: str = Field(description="制作物ID")
    name: str = Field(description="作品名 例: 「星降る夜に」")
    type: str = Field(description="作品タイプ 例: illustration_series, indie_game, single, novel")
    status: str = Field(
        default="in_progress",
        description="ステータス (in_progress/completed/planned)",
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="進捗 (0.0-1.0)",
    )
    current_task: str | None = Field(
        default=None,
        description="現在のタスク 例: 第3話の背景",
    )
    started_at: datetime | None = Field(default=None, description="開始日時")
    completed_at: datetime | None = Field(default=None, description="完成日時")


class CreativeWorks(BaseModel):
    """制作物一覧"""

    current: list[CreativeWork] = Field(
        default_factory=list,
        description="進行中の作品",
    )
    completed: list[CreativeWork] = Field(
        default_factory=list,
        description="完成した作品",
    )
    planned: list[CreativeWork] = Field(
        default_factory=list,
        description="予定している作品",
    )


# 作品タイプの定義（職業別）
WORK_TYPES = {
    "イラストレーター": ["illustration", "illustration_series", "fan_art"],
    "ゲーム開発者": ["indie_game", "game_jam", "prototype"],
    "作曲家": ["single", "album", "bgm"],
    "小説家": ["novel", "short_story", "web_serial"],
    "漫画家": ["manga", "manga_series", "doujin"],
    "デザイナー": ["design", "branding", "ui_design"],
}

# 進捗に応じた発言テンプレート
PROGRESS_MESSAGES = {
    (0.0, 0.2): ["{name}、始めた", "{name}の構想中"],
    (0.2, 0.5): ["{name}、やっと{progress_pct}%", "{name}、進めてる"],
    (0.5, 0.8): ["{name}、あと少し", "{name}、終わりが見えてきた"],
    (0.8, 1.0): ["{name}、ほぼ完成", "{name}、仕上げ中"],
}
