"""
ニュースシステム

記者が収集したニュースを管理する。
"""

from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """ニュースアイテム"""

    id: str = Field(description="ニュースID")
    title: str = Field(description="タイトル")
    summary: str | None = Field(default=None, description="要約")
    category: str = Field(description="カテゴリ（tech, game, creative, general）")
    source: str = Field(description="記者ID（reporter_tech等）")
    original_url: str | None = Field(default=None, description="元記事URL")
    posted_at: datetime = Field(default_factory=datetime.now, description="投稿日時")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(days=2),
        description="有効期限",
    )

    def is_expired(self) -> bool:
        """期限切れかどうか"""
        return datetime.now() > self.expires_at


class BulletinBoard(BaseModel):
    """掲示板（ニュース一覧）"""

    updated_at: datetime = Field(default_factory=datetime.now, description="最終更新日時")
    items: list[NewsItem] = Field(default_factory=list, description="ニュース一覧")

    def add_item(self, item: NewsItem) -> None:
        """ニュースを追加"""
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_expired(self) -> int:
        """期限切れのニュースを削除"""
        before = len(self.items)
        self.items = [item for item in self.items if not item.is_expired()]
        return before - len(self.items)

    def get_by_category(self, category: str) -> list[NewsItem]:
        """カテゴリでフィルタ"""
        return [item for item in self.items if item.category == category]

    def get_recent(self, limit: int = 10) -> list[NewsItem]:
        """最新のニュースを取得"""
        sorted_items = sorted(self.items, key=lambda x: x.posted_at, reverse=True)
        return sorted_items[:limit]


class ReporterConfig(BaseModel):
    """記者の設定"""

    id: str = Field(description="記者ID（reporter_tech等）")
    specialty: str = Field(description="専門分野")
    sources: list[dict[str, str]] = Field(default_factory=list, description="ソース一覧")
    include_keywords: list[str] = Field(default_factory=list, description="含めるキーワード")
    exclude_keywords: list[str] = Field(default_factory=list, description="除外キーワード")
    anonymize: bool = Field(default=True, description="個人名を除去するか")

    def should_include(self, text: str) -> bool:
        """テキストを含めるべきか判定"""
        text_lower = text.lower()

        # 除外キーワードチェック
        for keyword in self.exclude_keywords:
            if keyword.lower() in text_lower:
                return False

        # 含めるキーワードが設定されている場合、マッチ必須
        if self.include_keywords:
            return any(kw.lower() in text_lower for kw in self.include_keywords)

        return True
