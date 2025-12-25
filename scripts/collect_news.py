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


def fetch_rss(url: str) -> list[dict]:
    """RSSフィードを取得（実際のRSS取得はfeedparserが必要）"""
    # 注意: 本番環境ではfeedparserを使用
    # pip install feedparser
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
            })
        return items
    except ImportError:
        # feedparserがない場合はサンプルデータを返す
        return get_sample_news()


def get_sample_news() -> list[dict]:
    """サンプルニュースデータ（開発・テスト用）"""
    return [
        {"title": "新しいWebフレームワークがリリース", "summary": "開発者向けの新しいツールが登場", "link": ""},
        {"title": "AIアシスタントの最新動向", "summary": "機械学習を活用した新サービス", "link": ""},
        {"title": "オープンソースプロジェクトが注目を集める", "summary": "コミュニティ主導の開発が活発に", "link": ""},
        {"title": "クラウドサービスの新機能発表", "summary": "開発者向けの機能が充実", "link": ""},
        {"title": "プログラミング言語の最新アップデート", "summary": "パフォーマンス改善と新機能追加", "link": ""},
    ]


def collect_news_for_reporter(reporter_id: str, config: ReporterConfig) -> list[NewsItem]:
    """記者ごとにニュースを収集"""
    all_items = []

    for source in config.sources:
        print(f"  Fetching from {source['name']}...")
        raw_items = fetch_rss(source["url"])

        for item in raw_items:
            title = item.get("title", "")
            summary = item.get("summary", "")

            # フィルタリング
            if not config.should_include(title + " " + summary):
                continue

            news_item = NewsItem(
                id=f"news_{uuid.uuid4().hex[:8]}",
                title=title,
                summary=summary[:100] if summary else None,
                category=config.specialty.lower().replace("・", "_"),
                source=reporter_id,
                original_url=item.get("link"),
                posted_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=2),
            )
            all_items.append(news_item)

    return all_items


def main():
    """メイン処理"""
    print("📰 Collecting news from all reporters...")

    bulletin_repo = BulletinRepository(Path("bots/data/bulletin_board"))

    # 期限切れニュースを削除
    removed = bulletin_repo.cleanup_expired()
    if removed > 0:
        print(f"  Removed {removed} expired news items")

    total_added = 0

    for reporter_id, config in REPORTERS.items():
        print(f"\n📝 {reporter_id} ({config.specialty}):")

        news_items = collect_news_for_reporter(reporter_id, config)

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
