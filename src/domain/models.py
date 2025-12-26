"""
NPCの型定義（ドメインモデル）
"""

import os
from enum import Enum

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class StyleType(str, Enum):
    """文体スタイル"""

    NORMAL = "normal"  # 「新しい絵描いてる」
    OJISAN = "ojisan"  # 「今日も頑張ってるネ❗😄👍✨」
    YOUNG = "young"  # 「まじでやばいｗｗｗ」
    NICHAN = "2ch"  # 「うpしますた。ｷﾀ━(ﾟ∀ﾟ)━!」
    OTAKU = "otaku"  # 「尊い…この構図は神」
    POLITE = "polite"  # 「〜ですね」丁寧語
    TERSE = "terse"  # 短く簡潔


class HabitType(str, Enum):
    """特殊な習慣"""

    NEWS_SUMMARIZER = "news_summarizer"  # ニュースを要約して投稿
    EMOJI_HEAVY = "emoji_heavy"  # 絵文字を多用
    TIP_SHARER = "tip_sharer"  # 「〜すると便利」系
    WIP_POSTER = "wip_poster"  # 制作過程を共有
    QUESTION_ASKER = "question_asker"  # 質問形式が多い
    SELF_DEPRECATING = "self_deprecating"  # 自虐的
    ENTHUSIASTIC = "enthusiastic"  # テンション高め


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


class WritingStyle(BaseModel):
    """文章スタイル設定"""

    typo_rate: float = Field(
        default=0.0, ge=0.0, le=0.1, description="誤字率（0.0〜0.1）"
    )
    line_break: LineBreakStyle = Field(
        default=LineBreakStyle.MINIMAL, description="改行スタイル"
    )
    punctuation: PunctuationStyle = Field(
        default=PunctuationStyle.FULL, description="句読点スタイル"
    )
    quirks: list[WritingQuirk] = Field(
        default_factory=list, description="文章の癖リスト"
    )


class PersonalityTraits(BaseModel):
    """詳細な性格パラメータ（0.0〜1.0）"""

    activeness: float = Field(default=0.5, ge=0.0, le=1.0, description="積極性")
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0, description="好奇心")
    sociability: float = Field(default=0.5, ge=0.0, le=1.0, description="社交性")
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0, description="感受性")
    optimism: float = Field(default=0.5, ge=0.0, le=1.0, description="楽観性")
    creativity: float = Field(default=0.5, ge=0.0, le=1.0, description="創造性")
    persistence: float = Field(default=0.5, ge=0.0, le=1.0, description="粘り強さ")
    expressiveness: float = Field(default=0.5, ge=0.0, le=1.0, description="表現力")
    expertise: float = Field(default=0.5, ge=0.0, le=1.0, description="習熟度")
    intelligence: float = Field(default=0.5, ge=0.0, le=1.0, description="知性")
    feedback_sensitivity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="反応への感度"
    )


class Prompts(BaseModel):
    """個人プロンプト設定"""

    positive: list[str] = Field(default_factory=list, description="こう書いてほしい指示")
    negative: list[str] = Field(default_factory=list, description="これは避けてほしい指示")


class BotKey(BaseModel):
    """NPCの鍵情報"""

    id: int = Field(gt=0, description="NPC ID")
    name: str = Field(min_length=1, description="NPC名")
    pubkey: str = Field(min_length=64, max_length=64, description="公開鍵")
    nsec: str = Field(pattern=r"^nsec1[a-z0-9]+$", description="秘密鍵")

    @classmethod
    def from_env(cls, bot_id: int) -> "BotKey":
        """環境変数からNPCキーを読み込み"""
        bot_id_str = f"{bot_id:03d}"
        pubkey = os.getenv(f"BOT_{bot_id_str}_PUBKEY")
        nsec = os.getenv(f"BOT_{bot_id_str}_NSEC")

        if not pubkey or not nsec:
            raise ValueError(f"Keys not found for bot {bot_id_str} in environment variables")

        return cls(
            id=bot_id,
            name=f"bot{bot_id_str}",
            pubkey=pubkey,
            nsec=nsec,
        )


class Personality(BaseModel):
    """性格・特性"""

    type: str = Field(min_length=1, description="性格タイプ")
    traits: list[str] = Field(min_length=1, description="特徴リスト")
    emotional_range: int = Field(ge=0, le=10, description="感情表現の幅")


class Interests(BaseModel):
    """興味・関心"""

    topics: list[str] = Field(min_length=1, description="興味のあるトピック")
    keywords: list[str] = Field(min_length=1, description="よく使うキーワード")
    code_languages: list[str] | None = Field(default=None, description="好きなプログラミング言語")

    # 詳細な好み（カテゴリ別）
    likes: dict[str, list[str]] = Field(
        default_factory=dict,
        description="好きなもの（カテゴリ→リスト）例: {'manga': ['チェンソーマン'], 'languages': ['Rust']}",
    )
    dislikes: dict[str, list[str]] = Field(
        default_factory=dict,
        description="嫌いなもの（カテゴリ→リスト）例: {'os': ['Windows']}",
    )
    values: list[str] = Field(
        default_factory=list,
        description="価値観・重視すること 例: ['収益化', 'オープンソース']",
    )


class Behavior(BaseModel):
    """行動パターン"""

    post_frequency: int = Field(gt=0, le=100, description="1日あたりの投稿回数")
    post_frequency_variance: float = Field(ge=0.0, le=1.0, description="投稿頻度のばらつき")
    active_hours: list[int] = Field(min_length=1, description="活動時間帯")
    post_length_min: int = Field(gt=0, description="投稿の最小文字数")
    post_length_max: int = Field(gt=0, description="投稿の最大文字数")
    use_markdown: bool = Field(default=True, description="Markdownを使うか")
    use_code_blocks: bool = Field(default=False, description="コードブロックを使うか")

    @field_validator("active_hours")
    @classmethod
    def validate_active_hours(cls, v: list[int]) -> list[int]:
        """活動時間帯が0-23の範囲内かチェック"""
        if not all(0 <= hour <= 23 for hour in v):
            raise ValueError("active_hours must be between 0 and 23")
        return v

    @field_validator("post_length_max")
    @classmethod
    def validate_length_max(cls, v: int, info: "ValidationInfo") -> int:
        """最大文字数が最小文字数より大きいかチェック"""
        if "post_length_min" in info.data and v <= info.data["post_length_min"]:
            raise ValueError("post_length_max must be greater than post_length_min")
        return v


class Social(BaseModel):
    """社交性"""

    friend_bot_ids: list[int] = Field(default_factory=list, description="仲の良いNPCのID")
    reply_probability: float = Field(ge=0.0, le=1.0, description="返信する確率")
    repost_probability: float = Field(ge=0.0, le=1.0, description="リポストする確率")
    like_probability: float = Field(ge=0.0, le=1.0, description="いいねする確率")


class Background(BaseModel):
    """経歴・背景"""

    occupation: str | None = Field(default=None, description="職業")
    experience: str | None = Field(default=None, description="経験・スキル")
    hobbies: list[str] | None = Field(default=None, description="趣味")
    favorite_quotes: list[str] | None = Field(default=None, description="好きな言葉")


class BotProfile(BaseModel):
    """NPCプロフィール（YAML形式の履歴書）"""

    id: int = Field(gt=0, description="NPC ID")
    name: str = Field(min_length=1, description="NPC名")
    personality: Personality
    interests: Interests
    behavior: Behavior
    social: Social
    background: Background

    # 拡張フィールド（オプション、後方互換性のためデフォルト値あり）
    traits_detail: PersonalityTraits | None = Field(
        default=None, description="詳細な性格パラメータ（0.0〜1.0）"
    )
    style: StyleType = Field(default=StyleType.NORMAL, description="文体スタイル")
    habits: list[HabitType] = Field(default_factory=list, description="特殊な習慣")
    writing_style: WritingStyle | None = Field(
        default=None, description="文章スタイル設定（誤字率、改行、句読点など）"
    )
    prompts: Prompts | None = Field(default=None, description="個人プロンプト設定")


class BotState(BaseModel):
    """NPCの状態（実行時）"""

    id: int = Field(gt=0, description="NPC ID")
    last_post_time: int = Field(ge=0, description="最後の投稿時刻")
    next_post_time: int = Field(ge=0, description="次回投稿時刻")
    total_posts: int = Field(ge=0, description="累計投稿数")
    last_post_content: str | None = Field(default=None, description="最後の投稿内容")
    last_event_id: str | None = Field(default=None, description="最後の投稿のイベントID")
    post_history: list[str] = Field(default_factory=list, description="過去の投稿内容（最新20件）")
    discovered_topics: list[str] = Field(
        default_factory=list, description="新しく興味を持ったトピック"
    )
    # 気分（-1.0〜1.0、負がネガティブ、正がポジティブ）
    mood: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="現在の気分（-1.0〜1.0）",
    )


class TickState(BaseModel):
    """tickコマンドのラウンドロビン状態"""

    next_index: int = Field(default=0, ge=0, description="次に処理するNPCのインデックス")
    last_run_at: str | None = Field(default=None, description="最後の実行時刻（ISO形式）")
    total_ticks: int = Field(default=0, ge=0, description="累計tick回数")
