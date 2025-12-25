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
from src.infrastructure.external import RSSClient
from src.infrastructure.storage.bulletin_repo import BulletinRepository

# 記者設定
REPORTERS = {
    "reporter_tech": ReporterConfig(
        id="reporter_tech",
        specialty="IT・テクノロジー",
        sources=[
            {"name": "はてなブックマーク（テクノロジー）", "url": "https://b.hatena.ne.jp/hotentry/it.rss"},
        ],
        include_keywords=["アプリ", "ツール", "サービス", "開発", "プログラミング", "AI", "機械学習", "オープンソース", "リリース"],
        exclude_keywords=["政治", "選挙", "逮捕", "事件", "訴訟", "炎上"],
        anonymize=True,
    ),
    "reporter_game": ReporterConfig(
        id="reporter_game",
        specialty="ゲーム",
        sources=[
            {"name": "はてなブックマーク（ゲーム）", "url": "https://b.hatena.ne.jp/hotentry/game.rss"},
        ],
        include_keywords=["ゲーム", "インディー", "Steam", "Nintendo", "PlayStation", "リリース", "アップデート"],
        exclude_keywords=["炎上", "訴訟", "スキャンダル"],
        anonymize=True,
    ),
    "reporter_creative": ReporterConfig(
        id="reporter_creative",
        specialty="創作・アート",
        sources=[
            {"name": "はてなブックマーク（エンタメ）", "url": "https://b.hatena.ne.jp/hotentry/entertainment.rss"},
        ],
        include_keywords=["イラスト", "絵", "漫画", "アニメ", "デザイン", "音楽", "DTM", "作曲", "小説", "創作"],
        exclude_keywords=["炎上", "批判", "訴訟", "スキャンダル", "政治", "事件"],
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


def main():
    """メイン処理"""
    print("📰 Collecting news from all reporters...")

    bulletin_repo = BulletinRepository(Path("bots/data/bulletin_board"))
    rss_client = RSSClient()

    # 期限切れニュースを削除
    removed = bulletin_repo.cleanup_expired()
    if removed > 0:
        print(f"  Removed {removed} expired news items")

    total_added = 0

    for reporter_id, config in REPORTERS.items():
        print(f"\n📝 {reporter_id} ({config.specialty}):")

        news_items = collect_news_for_reporter(reporter_id, config, rss_client)

        for item in news_items[:5]:  # 各記者最大5件
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
