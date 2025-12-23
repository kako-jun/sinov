"""
ボットの型定義
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BotKey(BaseModel):
    """ボットの鍵情報"""
    id: int = Field(gt=0, description="ボットID")
    name: str = Field(min_length=1, description="ボット名")
    pubkey: str = Field(min_length=64, max_length=64, description="公開鍵")
    nsec: str = Field(pattern=r"^nsec1[a-z0-9]+$", description="秘密鍵")
    
    @classmethod
    def from_env(cls, bot_id: int) -> "BotKey":
        """環境変数からボットキーを読み込み"""
        import os
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
    code_languages: Optional[list[str]] = Field(default=None, description="好きなプログラミング言語")


class Behavior(BaseModel):
    """行動パターン"""
    post_frequency: int = Field(gt=0, le=100, description="1日あたりの投稿回数")
    post_frequency_variance: float = Field(ge=0.0, le=1.0, description="投稿頻度のばらつき")
    active_hours: list[int] = Field(min_length=1, description="活動時間帯")
    post_length_min: int = Field(gt=0, description="投稿の最小文字数")
    post_length_max: int = Field(gt=0, description="投稿の最大文字数")
    use_markdown: bool = Field(default=True, description="Markdownを使うか")
    use_code_blocks: bool = Field(default=False, description="コードブロックを使うか")
    
    @field_validator('active_hours')
    @classmethod
    def validate_active_hours(cls, v: list[int]) -> list[int]:
        """活動時間帯が0-23の範囲内かチェック"""
        if not all(0 <= hour <= 23 for hour in v):
            raise ValueError("active_hours must be between 0 and 23")
        return v
    
    @field_validator('post_length_max')
    @classmethod
    def validate_length_max(cls, v: int, info) -> int:
        """最大文字数が最小文字数より大きいかチェック"""
        if 'post_length_min' in info.data and v <= info.data['post_length_min']:
            raise ValueError("post_length_max must be greater than post_length_min")
        return v


class Social(BaseModel):
    """社交性"""
    friend_bot_ids: list[int] = Field(default_factory=list, description="仲の良いボットのID")
    reply_probability: float = Field(ge=0.0, le=1.0, description="返信する確率")
    repost_probability: float = Field(ge=0.0, le=1.0, description="リポストする確率")
    like_probability: float = Field(ge=0.0, le=1.0, description="いいねする確率")


class Background(BaseModel):
    """経歴・背景"""
    occupation: Optional[str] = Field(default=None, description="職業")
    experience: Optional[str] = Field(default=None, description="経験・スキル")
    hobbies: Optional[list[str]] = Field(default=None, description="趣味")
    favorite_quotes: Optional[list[str]] = Field(default=None, description="好きな言葉")


class BotProfile(BaseModel):
    """ボットプロフィール（YAML形式の履歴書）"""
    id: int = Field(gt=0, description="ボットID")
    name: str = Field(min_length=1, description="ボット名")
    personality: Personality
    interests: Interests
    behavior: Behavior
    social: Social
    background: Background


class BotState(BaseModel):
    """ボットの状態（実行時）"""
    id: int = Field(gt=0, description="ボットID")
    last_post_time: int = Field(ge=0, description="最後の投稿時刻")
    next_post_time: int = Field(ge=0, description="次回投稿時刻")
    total_posts: int = Field(ge=0, description="累計投稿数")
    last_post_content: Optional[str] = Field(default=None, description="最後の投稿内容")
