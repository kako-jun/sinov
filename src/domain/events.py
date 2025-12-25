"""
季節イベントシステム
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SeasonalEvent(BaseModel):
    """季節イベント"""

    id: str = Field(description="イベントID")
    name: str = Field(description="イベント名")
    start_month: int = Field(ge=1, le=12, description="開始月")
    start_day: int = Field(ge=1, le=31, description="開始日")
    end_month: int = Field(ge=1, le=12, description="終了月")
    end_day: int = Field(ge=1, le=31, description="終了日")
    topics: list[str] = Field(default_factory=list, description="関連トピック")
    keywords: list[str] = Field(default_factory=list, description="使いやすいキーワード")
    greetings: list[str] = Field(default_factory=list, description="挨拶例")
    probability: float = Field(default=0.3, ge=0.0, le=1.0, description="話題に出す確率")

    def is_active(self, date: datetime | None = None) -> bool:
        """イベントが現在有効かどうか"""
        if date is None:
            date = datetime.now()

        current_month = date.month
        current_day = date.day

        # 年をまたぐイベント（例: 12/25〜1/3）
        if self.start_month > self.end_month:
            if current_month >= self.start_month:
                return current_day >= self.start_day or current_month > self.start_month
            elif current_month <= self.end_month:
                return current_day <= self.end_day or current_month < self.end_month
            return False

        # 同じ年内のイベント
        if current_month < self.start_month or current_month > self.end_month:
            return False

        if current_month == self.start_month and current_day < self.start_day:
            return False

        if current_month == self.end_month and current_day > self.end_day:
            return False

        return True


class EventCalendar(BaseModel):
    """イベントカレンダー"""

    events: list[SeasonalEvent] = Field(default_factory=list, description="イベント一覧")

    def get_active_events(self, date: datetime | None = None) -> list[SeasonalEvent]:
        """現在有効なイベントを取得"""
        return [e for e in self.events if e.is_active(date)]

    def get_event_topics(self, date: datetime | None = None) -> list[str]:
        """現在有効なイベントのトピックを取得"""
        topics = []
        for event in self.get_active_events(date):
            topics.extend(event.topics)
        return topics

    def get_event_keywords(self, date: datetime | None = None) -> list[str]:
        """現在有効なイベントのキーワードを取得"""
        keywords = []
        for event in self.get_active_events(date):
            keywords.extend(event.keywords)
        return keywords
