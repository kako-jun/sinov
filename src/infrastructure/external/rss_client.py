"""
RSSフィード取得クライアント
"""

from dataclasses import dataclass


@dataclass
class RSSItem:
    """RSSフィードアイテム"""

    title: str
    summary: str
    link: str


class RSSClient:
    """RSSフィードを取得するクライアント"""

    def __init__(self, use_sample: bool = False):
        """
        Args:
            use_sample: Trueの場合、実際のRSS取得の代わりにサンプルデータを返す
        """
        self.use_sample = use_sample
        self._feedparser_available = self._check_feedparser()

    def _check_feedparser(self) -> bool:
        """feedparserが利用可能かチェック"""
        try:
            import feedparser  # noqa: F401
            return True
        except ImportError:
            return False

    def fetch(self, url: str, limit: int = 10) -> list[RSSItem]:
        """
        RSSフィードを取得

        Args:
            url: RSSフィードのURL
            limit: 取得する最大件数

        Returns:
            RSSItemのリスト
        """
        if self.use_sample or not self._feedparser_available:
            return self._get_sample_items()

        return self._fetch_real(url, limit)

    def _fetch_real(self, url: str, limit: int) -> list[RSSItem]:
        """実際のRSSフィードを取得"""
        import feedparser

        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries[:limit]:
            items.append(
                RSSItem(
                    title=entry.get("title", ""),
                    summary=entry.get("summary", ""),
                    link=entry.get("link", ""),
                )
            )

        return items

    def _get_sample_items(self) -> list[RSSItem]:
        """サンプルデータ（開発・テスト用）"""
        return [
            RSSItem(
                title="新しいWebフレームワークがリリース",
                summary="開発者向けの新しいツールが登場",
                link="",
            ),
            RSSItem(
                title="AIアシスタントの最新動向",
                summary="機械学習を活用した新サービス",
                link="",
            ),
            RSSItem(
                title="オープンソースプロジェクトが注目を集める",
                summary="コミュニティ主導の開発が活発に",
                link="",
            ),
            RSSItem(
                title="クラウドサービスの新機能発表",
                summary="開発者向けの機能が充実",
                link="",
            ),
            RSSItem(
                title="プログラミング言語の最新アップデート",
                summary="パフォーマンス改善と新機能追加",
                link="",
            ),
        ]
