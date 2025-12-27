"""
掲示板リポジトリ

ニュースの永続化を担当。
"""

import json
from datetime import datetime
from pathlib import Path

from ...domain import BulletinBoard, NewsItem


class BulletinRepository:
    """掲示板データの永続化"""

    def __init__(self, bulletin_dir: Path):
        self.bulletin_dir = bulletin_dir
        self.news_file = bulletin_dir / "news.json"
        self.events_file = bulletin_dir / "events.json"

        # ディレクトリ作成
        self.bulletin_dir.mkdir(parents=True, exist_ok=True)

    def load_news(self) -> BulletinBoard:
        """ニュースを読み込み"""
        if not self.news_file.exists():
            return BulletinBoard()

        with open(self.news_file, encoding="utf-8") as f:
            data = json.load(f)

        items = []
        for item_data in data.get("items", []):
            items.append(
                NewsItem(
                    id=item_data["id"],
                    title=item_data["title"],
                    summary=item_data.get("summary"),
                    category=item_data["category"],
                    source=item_data["source"],
                    original_url=item_data.get("original_url"),
                    posted_at=datetime.fromisoformat(item_data["posted_at"]),
                    expires_at=datetime.fromisoformat(item_data["expires_at"]),
                )
            )

        return BulletinBoard(
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            items=items,
        )

    def save_news(self, bulletin: BulletinBoard) -> None:
        """ニュースを保存"""
        data = {
            "updated_at": bulletin.updated_at.isoformat(),
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "summary": item.summary,
                    "category": item.category,
                    "source": item.source,
                    "original_url": item.original_url,
                    "posted_at": item.posted_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                }
                for item in bulletin.items
            ],
        }

        with open(self.news_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_news_item(self, item: NewsItem) -> None:
        """ニュースを追加"""
        bulletin = self.load_news()
        bulletin.add_item(item)
        self.save_news(bulletin)

    def cleanup_expired(self) -> int:
        """期限切れのニュースを削除"""
        bulletin = self.load_news()
        removed = bulletin.remove_expired()
        if removed > 0:
            self.save_news(bulletin)
        return removed

    def get_recent_news(self, limit: int = 10) -> list[NewsItem]:
        """最新のニュースを取得"""
        bulletin = self.load_news()
        return bulletin.get_recent(limit)

    def get_news_by_category(self, category: str) -> list[NewsItem]:
        """カテゴリ別のニュースを取得"""
        bulletin = self.load_news()
        return bulletin.get_by_category(category)
