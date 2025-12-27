"""
Enum定義（文体・習慣・文章スタイル）
"""

from enum import Enum


class StyleType(str, Enum):
    """文体スタイル"""

    NORMAL = "normal"  # 「新しい絵描いてる」
    OJISAN = "ojisan"  # 「今日も頑張ってるネ❗😄👍✨」
    YOUNG = "young"  # 「まじでやばいｗｗｗ」
    NICHAN = "2ch"  # 「うpしますた。ｷﾀ━(ﾟ∀ﾟ)━!」
    OTAKU = "otaku"  # 「尊い…この構図は神」
    POLITE = "polite"  # 「〜ですね」丁寧語
    TERSE = "terse"  # 短く簡潔


class DialectType(str, Enum):
    """方言（さりげなく語尾に出る程度）"""

    NONE = "none"  # 標準語
    KANSAI = "kansai"  # 関西弁: 〜やん、〜やで、〜やねん
    HAKATA = "hakata"  # 博多弁: 〜ばい、〜たい、〜っちゃ
    NAGOYA = "nagoya"  # 名古屋弁: 〜だがや、〜だがね
    TOHOKU = "tohoku"  # 東北弁: 〜だべ、〜っぺ
    HIROSHIMA = "hiroshima"  # 広島弁: 〜じゃけん、〜じゃ
    KYOTO = "kyoto"  # 京都弁: 〜どす、〜はる、〜やし


class HabitType(str, Enum):
    """特殊な習慣"""

    NEWS_SUMMARIZER = "news_summarizer"  # ニュースを要約して投稿
    EMOJI_HEAVY = "emoji_heavy"  # 絵文字を多用
    TIP_SHARER = "tip_sharer"  # 「〜すると便利」系
    WIP_POSTER = "wip_poster"  # 制作過程を共有
    QUESTION_ASKER = "question_asker"  # 質問形式が多い
    SELF_DEPRECATING = "self_deprecating"  # 自虐的
    ENTHUSIASTIC = "enthusiastic"  # テンション高め
    HASHTAG_USER = "hashtag_user"  # 時々ハッシュタグを付ける


class LineBreakStyle(str, Enum):
    """改行スタイル"""

    NONE = "none"  # 改行なし（陰キャ、長文一気書き）
    MINIMAL = "minimal"  # 最小限（必要な時だけ）
    SENTENCE = "sentence"  # 一文ごとに改行
    PARAGRAPH = "paragraph"  # 段落形式（複数改行で区切る）


class PunctuationStyle(str, Enum):
    """句読点スタイル"""

    FULL = "full"  # 「、」「。」両方使う
    COMMA_ONLY = "comma_only"  # 「、」だけ使う
    PERIOD_ONLY = "period_only"  # 「。」だけ使う
    NONE = "none"  # 使わない


class WritingQuirk(str, Enum):
    """文章の癖"""

    W_HEAVY = "w_heavy"  # 「w」を多用
    KUSA = "kusa"  # 「草」を使う
    ELLIPSIS_HEAVY = "ellipsis_heavy"  # 「…」を多用
    SUFFIX_NE = "suffix_ne"  # 語尾に「ね」
    SUFFIX_NA = "suffix_na"  # 語尾に「な」
    EXCLAMATION_HEAVY = "exclamation_heavy"  # 「！」を多用
    QUESTION_HEAVY = "question_heavy"  # 「？」を多用
    TILDE_HEAVY = "tilde_heavy"  # 「〜」を多用
    PARENTHESES = "parentheses"  # （）で補足を入れる
    ARROW = "arrow"  # 「→」を使う
    KATAKANA_ENGLISH = "katakana_english"  # カタカナ英語を使う
    ABBREVIATION = "abbreviation"  # 略語を使う（それな、わかる、など）
