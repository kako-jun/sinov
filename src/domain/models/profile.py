"""
NPCプロフィール関連のモデル
"""

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from .creative_work import CreativeWorks
from .enums import DialectType, HabitType, StyleType
from .writing import PersonalityTraits, Prompts, WritingStyle


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
        description="好きなもの（カテゴリ→リスト）",
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
    # 活動時間の詳細設定
    chronotype: str = Field(
        default="intermediate",
        description="朝型/夜型 (lark/owl/intermediate)",
    )
    hourly_weight: dict[int, float] = Field(
        default_factory=dict,
        description="時間帯別活動確率 (0-23の時間→確率)",
    )
    rhythm_stability: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="生活リズム安定度",
    )
    daily_schedule: dict[int, dict[str, float]] = Field(
        default_factory=dict,
        description="時間帯別活動 (時間→{活動名: 確率})",
    )

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

    @field_validator("chronotype")
    @classmethod
    def validate_chronotype(cls, v: str) -> str:
        """chronotypeが有効な値かチェック"""
        valid = ["lark", "owl", "intermediate"]
        if v not in valid:
            raise ValueError(f"chronotype must be one of {valid}")
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


class WindowColor(BaseModel):
    """ウィンドウカラー（MYPACE独自機能）

    4つの角の色を指定。Noneの場合はテーマデフォルト。
    """

    top_left: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    top_right: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    bottom_left: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    bottom_right: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")

    def to_aurora_tag(self) -> list[str] | None:
        """auroraタグ形式に変換（全て指定されている場合のみ）"""
        if all([self.top_left, self.top_right, self.bottom_left, self.bottom_right]):
            return ["aurora", self.top_left, self.top_right, self.bottom_left, self.bottom_right]
        return None


class NpcProfile(BaseModel):
    """NPCプロフィール（YAML形式の履歴書）"""

    id: int = Field(gt=0, description="NPC ID")
    name: str = Field(min_length=1, description="NPC名")
    personality: Personality
    interests: Interests
    behavior: Behavior
    social: Social
    background: Background

    # バックエンドNPC用フィールド
    is_backend: bool = Field(default=False, description="裏方NPCかどうか")
    posts: bool = Field(default=True, description="投稿するかどうか")

    # 拡張フィールド（オプション、後方互換性のためデフォルト値あり）
    traits_detail: PersonalityTraits | None = Field(
        default=None, description="詳細な性格パラメータ（0.0〜1.0）"
    )
    style: StyleType = Field(default=StyleType.NORMAL, description="文体スタイル")
    dialect: DialectType = Field(
        default=DialectType.NONE, description="方言（さりげなく語尾に出る程度）"
    )
    habits: list[HabitType] = Field(default_factory=list, description="特殊な習慣")
    writing_style: WritingStyle | None = Field(
        default=None, description="文章スタイル設定（誤字率、改行、句読点など）"
    )
    prompts: Prompts | None = Field(default=None, description="個人プロンプト設定")
    creative_works: CreativeWorks | None = Field(
        default=None, description="制作物（進行中・完成・予定）"
    )
    window_color: WindowColor | None = Field(
        default=None, description="ウィンドウカラー（MYPACE独自機能）"
    )
