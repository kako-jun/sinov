"""
トレンド取得クライアント（Google Trends RSS使用）
"""

from dataclasses import dataclass

import feedparser


@dataclass
class TrendItem:
    """トレンドアイテム"""

    name: str  # トレンドワード
    category: str | None = None  # カテゴリ（判別できれば）
    traffic: str | None = None  # トラフィック量


# 許可するトピック（ホワイトリスト）
WHITELIST_KEYWORDS = [
    # 季節イベント
    "クリスマス",
    "正月",
    "年末",
    "年始",
    "大晦日",
    "バレンタイン",
    "ハロウィン",
    "夏休み",
    "ゴールデンウィーク",
    "お盆",
    "花見",
    "紅葉",
    # ゲーム関連
    "ゲーム",
    "steam",
    "nintendo",
    "switch",
    "playstation",
    "ps5",
    "xbox",
    "インディー",
    "新作",
    "アップデート",
    "配信",
    "rpg",
    "アクション",
    "シミュレーション",
    # 創作関連
    "イラスト",
    "絵描き",
    "漫画",
    "同人",
    "コミケ",
    "デザイン",
    "音楽",
    "dtm",
    "作曲",
    "アニメ",
    "映画",
    "小説",
    "ラノベ",
    "vtuber",
    "ホロライブ",
    "にじさんじ",
    # IT関連
    "プログラミング",
    "開発",
    "エンジニア",
    "ai",
    "chatgpt",
    "claude",
    "gemini",
    "アプリ",
    "サービス",
    "python",
    "javascript",
    "typescript",
    "react",
    "github",
    "リリース",
    "アップデート",
    "障害",
    "復旧",
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
    "与党",
    "野党",
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
    "被害",
    # 炎上・ネガティブ
    "炎上",
    "批判",
    "謝罪",
    "不祥事",
    "スキャンダル",
    # 宗教・戦争
    "宗教",
    "戦争",
    "軍事",
    "紛争",
    # 芸能人関連
    "結婚",
    "離婚",
    "熱愛",
    "不倫",
    "アナウンサー",
    # TV局（芸能ニュースの発信元）
    "tbs",
    "ntv",
    "フジテレビ",
    "テレ朝",
    "テレビ東京",
    # ギャンブル
    "競馬",
    "競輪",
    "競艇",
    "パチンコ",
    "有馬記念",
    "グランプリ",
    # スポーツ（創作と無関係）
    "野球",
    "サッカー",
    "バスケ",
    "バレー",
    "相撲",
    "ボクシング",
]


class TrendScraper:
    """Google Trendsからトレンドを取得"""

    GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=JP"

    def __init__(self):
        pass

    def fetch_trends(self, limit: int = 20) -> list[TrendItem]:
        """
        日本のトレンドを取得

        Args:
            limit: 取得する最大件数

        Returns:
            TrendItemのリスト（フィルタリング済み）
        """
        raw_trends = self._fetch_from_google_trends()

        # フィルタリング
        filtered = self._filter_trends(raw_trends)
        return filtered[:limit]

    def _fetch_from_google_trends(self) -> list[TrendItem]:
        """Google Trends RSSからトレンドを取得"""
        try:
            feed = feedparser.parse(self.GOOGLE_TRENDS_RSS)

            trends = []
            for entry in feed.entries:
                title = entry.get("title", "")
                if not title:
                    continue

                # トラフィック量を取得
                traffic = None
                if hasattr(entry, "ht_approx_traffic"):
                    traffic = entry.ht_approx_traffic

                trends.append(
                    TrendItem(
                        name=title,
                        category=self._guess_category(title),
                        traffic=traffic,
                    )
                )

            return trends
        except Exception as e:
            print(f"⚠️  Failed to fetch Google Trends: {e}")
            return []

    def _guess_category(self, title: str) -> str | None:
        """タイトルからカテゴリを推測"""
        title_lower = title.lower()

        # ゲーム関連
        game_keywords = ["ゲーム", "steam", "nintendo", "playstation", "xbox"]
        if any(kw in title_lower for kw in game_keywords):
            return "ゲーム"

        # IT関連
        it_keywords = ["ai", "プログラミング", "開発", "アプリ", "python", "javascript"]
        if any(kw in title_lower for kw in it_keywords):
            return "IT"

        # 創作関連
        creative_keywords = ["イラスト", "漫画", "アニメ", "音楽", "映画"]
        if any(kw in title_lower for kw in creative_keywords):
            return "創作"

        # 季節イベント
        season_keywords = ["クリスマス", "正月", "バレンタイン", "ハロウィン"]
        if any(kw in title_lower for kw in season_keywords):
            return "季節"

        return None

    def _filter_trends(self, trends: list[TrendItem]) -> list[TrendItem]:
        """トレンドをフィルタリング（ホワイトリスト一致のみ採用）"""
        filtered = []

        for trend in trends:
            name_lower = trend.name.lower()

            # ブラックリストチェック（該当したら除外）
            if any(kw in name_lower for kw in BLACKLIST_KEYWORDS):
                continue

            # ホワイトリストに該当するものだけ採用
            if any(kw in name_lower for kw in WHITELIST_KEYWORDS):
                trend.category = trend.category or "話題"
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

        # どちらにも該当しない場合は不明
        return False
