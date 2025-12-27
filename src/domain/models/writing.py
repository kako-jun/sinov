"""
文章スタイル関連のモデル
"""

from pydantic import BaseModel, Field

from .enums import LineBreakStyle, PunctuationStyle, WritingQuirk


class WritingStyle(BaseModel):
    """文章スタイル設定"""

    typo_rate: float = Field(default=0.0, ge=0.0, le=0.1, description="誤字率（0.0〜0.1）")
    line_break: LineBreakStyle = Field(default=LineBreakStyle.MINIMAL, description="改行スタイル")
    punctuation: PunctuationStyle = Field(
        default=PunctuationStyle.FULL, description="句読点スタイル"
    )
    quirks: list[WritingQuirk] = Field(default_factory=list, description="文章の癖リスト")


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
    feedback_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0, description="反応への感度")


class Prompts(BaseModel):
    """個人プロンプト設定"""

    positive: list[str] = Field(default_factory=list, description="こう書いてほしい指示")
    negative: list[str] = Field(default_factory=list, description="これは避けてほしい指示")
