"""
Xトレンドスクレイピングクライアント
"""

from dataclasses import dataclass


@dataclass
class TrendItem:
    """Xトレンドアイテム"""

    name: str  # トレンドワード
    category: str | None = None  # カテゴリ（判別できれば）
    tweet_volume: int | None = None  # ツイート数（取得できれば）


# 許可するトピック（ホワイトリスト）
WHITELIST_KEYWORDS = [
    # 季節イベント
    "クリスマス",
    "正月",
    "バレンタイン",
    "ハロウィン",
    "夏休み",
    "ゴールデンウィーク",
    "お盆",
    "花見",
    "紅葉",
    # ゲーム関連
    "ゲーム",
    "Steam",
    "Nintendo",
    "PlayStation",
    "Xbox",
    "インディー",
    "新作",
    "アップデート",
    "配信",
    # 創作関連
    "イラスト",
    "絵描き",
    "漫画",
    "同人",
    "コミケ",
    "デザイン",
    "音楽",
    "DTM",
    "作曲",
    # IT関連
    "プログラミング",
    "開発",
    "エンジニア",
    "AI",
    "アプリ",
    "サービス",
]

# 禁止するトピック（ブラックリスト）
BLACKLIST_KEYWORDS = [
    # 政治
    "政治",
    "選挙",
    "政党",
    "議員",
    "首相",
    "大統領",
    "国会",
    "政府",
    # 事件・事故
    "事件",
    "事故",
    "逮捕",
    "死亡",
    "殺人",
    "容疑",
    "犯罪",
    "裁判",
    "訴訟",
    # 炎上・ネガティブ
    "炎上",
    "批判",
    "謝罪",
    "不祥事",
    "スキャンダル",
    "問題",
    # 宗教・戦争
    "宗教",
    "戦争",
    "軍事",
    "紛争",
    # 個人名（ジャンル）
    "俳優",
    "女優",
    "アイドル",
    "芸人",
]


class XTrendScraper:
    """Xトレンドをスクレイピングで取得"""

    def __init__(self, use_sample: bool = False):
        """
        Args:
            use_sample: Trueの場合、実際のスクレイピングの代わりにサンプルデータを返す
        """
        self.use_sample = use_sample

    def fetch_trends(self, limit: int = 20) -> list[TrendItem]:
        """
        日本のトレンドを取得

        Args:
            limit: 取得する最大件数

        Returns:
            TrendItemのリスト（フィルタリング済み）
        """
        if self.use_sample:
            raw_trends = self._get_sample_trends()
        else:
            raw_trends = self._scrape_trends(limit * 2)

        # フィルタリング
        filtered = self._filter_trends(raw_trends)
        return filtered[:limit]

    def _scrape_trends(self, limit: int) -> list[TrendItem]:
        """実際のスクレイピング（未実装）

        Note:
            Xのトレンドページをスクレイピングするには、
            Seleniumなどのブラウザ自動化ツールが必要。
            現時点ではサンプルデータを返す。
        """
        # TODO: 実際のスクレイピング実装
        # Xのトレンドページは動的にロードされるため、
        # requests + BeautifulSoupでは取得困難。
        # Selenium または Playwright が必要。
        return self._get_sample_trends()

    def _filter_trends(self, trends: list[TrendItem]) -> list[TrendItem]:
        """トレンドをフィルタリング"""
        filtered = []

        for trend in trends:
            name_lower = trend.name.lower()

            # ブラックリストチェック
            if any(kw in name_lower for kw in BLACKLIST_KEYWORDS):
                continue

            # ホワイトリストチェック（どれかにマッチする必要がある）
            if any(kw in name_lower for kw in WHITELIST_KEYWORDS):
                filtered.append(trend)

        return filtered

    def is_safe_topic(self, topic: str) -> bool:
        """トピックが安全か（LLMチェック前の事前判定）"""
        topic_lower = topic.lower()

        # ブラックリストに該当したらNG
        if any(kw in topic_lower for kw in BLACKLIST_KEYWORDS):
            return False

        # ホワイトリストに該当したらOK
        if any(kw in topic_lower for kw in WHITELIST_KEYWORDS):
            return True

        # どちらにも該当しない場合は不明（LLMチェックが必要）
        return False

    def _get_sample_trends(self) -> list[TrendItem]:
        """サンプルデータ（開発・テスト用）"""
        return [
            TrendItem(name="Steamセール", category="ゲーム"),
            TrendItem(name="インディーゲーム", category="ゲーム"),
            TrendItem(name="イラストAC", category="創作"),
            TrendItem(name="クリスマスイラスト", category="季節"),
            TrendItem(name="新作アプリ", category="IT"),
            TrendItem(name="Python新バージョン", category="IT"),
            TrendItem(name="コミケ準備", category="創作"),
            TrendItem(name="ゲーム配信", category="ゲーム"),
            TrendItem(name="DTM機材", category="音楽"),
            TrendItem(name="正月休み", category="季節"),
        ]
