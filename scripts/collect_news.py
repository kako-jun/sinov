#!/usr/bin/env python
"""
ニュース収集スクリプト
定期的に実行してbots/data/bulletin_board/news.jsonに最新ニュースを保存
"""

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.news import NewsItem, ReporterConfig
from src.infrastructure.external import RSSClient, XTrendScraper
from src.infrastructure.storage.bulletin_repo import BulletinRepository

# 記者設定
REPORTERS = {
    "reporter_tech": ReporterConfig(
        id="reporter_tech",
        specialty="IT・テクノロジー",
        sources=[
            {
                "name": "はてなブックマーク（テクノロジー）",
                "url": "https://b.hatena.ne.jp/hotentry/it.rss",
            },
        ],
        include_keywords=[
            "アプリ",
            "ツール",
            "サービス",
            "開発",
            "プログラミング",
            "AI",
            "機械学習",
            "オープンソース",
            "リリース",
        ],
        exclude_keywords=["政治", "選挙", "逮捕", "事件", "訴訟", "炎上"],
        anonymize=True,
    ),
    "reporter_game": ReporterConfig(
        id="reporter_game",
        specialty="ゲーム",
        sources=[
            {
                "name": "はてなブックマーク（ゲーム）",
                "url": "https://b.hatena.ne.jp/hotentry/game.rss",
            },
        ],
        include_keywords=[
            "ゲーム",
            "インディー",
            "Steam",
            "Nintendo",
            "PlayStation",
            "リリース",
            "アップデート",
        ],
        exclude_keywords=["炎上", "訴訟", "スキャンダル"],
        anonymize=True,
    ),
    "reporter_creative": ReporterConfig(
        id="reporter_creative",
        specialty="創作・アート",
        sources=[
            {
                "name": "はてなブックマーク（エンタメ）",
                "url": "https://b.hatena.ne.jp/hotentry/entertainment.rss",
            },
        ],
        include_keywords=[
            "イラスト",
            "絵",
            "漫画",
            "アニメ",
            "デザイン",
            "音楽",
            "DTM",
            "作曲",
            "小説",
            "創作",
        ],
        exclude_keywords=["炎上", "批判", "訴訟", "スキャンダル", "政治", "事件"],
        anonymize=True,
    ),
    "reporter_general": ReporterConfig(
        id="reporter_general",
        specialty="一般時事（IT・創作系）",
        sources=[
            {
                "name": "はてなブックマーク（総合）",
                "url": "https://b.hatena.ne.jp/hotentry/all.rss",
            },
        ],
        include_keywords=[
            "テクノロジー",
            "アプリ",
            "サービス",
            "創作",
            "ツール",
            "開発",
        ],
        exclude_keywords=[
            "政治",
            "選挙",
            "宗教",
            "事件",
            "逮捕",
            "炎上",
            "訴訟",
            "戦争",
        ],
        anonymize=True,
    ),
}


def collect_news_for_reporter(
    reporter_id: str, config: ReporterConfig, rss_client: RSSClient
) -> list[NewsItem]:
    """記者ごとにニュースを収集"""
    all_items = []

    for source in config.sources:
        print(f"  Fetching from {source['name']}...")
        rss_items = rss_client.fetch(source["url"], limit=10)

        for item in rss_items:
            title = item.title
            summary = item.summary

            # フィルタリング
            if not config.should_include(title + " " + summary):
                continue

            news_item = NewsItem(
                id=f"news_{uuid.uuid4().hex[:8]}",
                title=title,
                summary=summary[:100] if summary else None,
                category=config.specialty.lower().replace("・", "_"),
                source=reporter_id,
                original_url=item.link or None,
                posted_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=2),
            )
            all_items.append(news_item)

    return all_items


def collect_trends(scraper: XTrendScraper) -> list[NewsItem]:
    """Xトレンドを収集"""
    all_items = []

    print("  Fetching X trends...")
    trends = scraper.fetch_trends(limit=10)

    for trend in trends:
        news_item = NewsItem(
            id=f"trend_{uuid.uuid4().hex[:8]}",
            title=trend.name,
            summary=f"Xでトレンド入り（{trend.category or '話題'}）",
            category="trend",
            source="reporter_trend",
            original_url=None,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=12),  # トレンドは短命
        )
        all_items.append(news_item)

    return all_items


def main():
    """メイン処理"""
    print("📰 Collecting news from all reporters...")

    bulletin_repo = BulletinRepository(Path("bots/data/bulletin_board"))
    rss_client = RSSClient()
    x_scraper = XTrendScraper()

    # 期限切れニュースを削除
    removed = bulletin_repo.cleanup_expired()
    if removed > 0:
        print(f"  Removed {removed} expired news items")

    total_added = 0

    # RSS記者からニュースを収集
    for reporter_id, config in REPORTERS.items():
        print(f"\n📝 {reporter_id} ({config.specialty}):")

        news_items = collect_news_for_reporter(reporter_id, config, rss_client)

        for item in news_items[:5]:  # 各記者最大5件
            bulletin_repo.add_news_item(item)
            print(f"    + {item.title[:50]}...")
            total_added += 1

    # Xトレンドを収集
    print("\n📝 reporter_trend (Xトレンド):")
    trend_items = collect_trends(x_scraper)

    for item in trend_items[:5]:  # 最大5件
        bulletin_repo.add_news_item(item)
        print(f"    + {item.title[:50]}...")
        total_added += 1

    print(f"\n✅ Added {total_added} news items")

    # 最新ニュースを表示
    recent = bulletin_repo.get_recent_news(5)
    print(f"\n📋 Recent news ({len(recent)} items):")
    for item in recent:
        print(f"  - [{item.category}] {item.title[:40]}...")


if __name__ == "__main__":
    main()
