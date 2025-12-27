"""
外部サービスクライアント
"""

from .article_fetcher import ArticleFetcher, ArticleSummarizer
from .rss_client import RSSClient, RSSItem
from .trend_scraper import TrendItem, TrendScraper

# 後方互換性のためXTrendScraperもエクスポート
XTrendScraper = TrendScraper

__all__ = [
    "ArticleFetcher",
    "ArticleSummarizer",
    "RSSClient",
    "RSSItem",
    "TrendItem",
    "TrendScraper",
    "XTrendScraper",
]
