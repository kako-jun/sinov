"""
記憶システム

短期記憶: 今興味を持っているもの。時間とともに減衰。
長期記憶: 基本的に消えない。履歴書（core）と獲得した記憶（acquired）。
連作状態: シリーズ投稿の管理。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ShortTermMemory(BaseModel):
    """短期記憶の1エントリ"""

    content: str = Field(description="記憶の内容")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="記憶の強さ（減衰する）")
    created_at: str = Field(description="作成日時（ISO形式）")
    source: str = Field(default="post", description="記憶のソース（post, reaction, news等）")


class AcquiredMemory(BaseModel):
    """獲得した長期記憶の1エントリ"""

    content: str = Field(description="記憶の内容")
    acquired_at: str = Field(description="獲得日時（ISO形式）")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要度")


class SeriesState(BaseModel):
    """連作つぶやきの状態"""

    active: bool = Field(default=False, description="連作中かどうか")
    theme: str | None = Field(default=None, description="連作のテーマ")
    current_index: int = Field(default=0, description="現在の投稿番号（0-indexed）")
    total_planned: int = Field(default=0, description="予定投稿数（2-5）")
    posts: list[str] = Field(default_factory=list, description="これまでの投稿内容")


class BotMemory(BaseModel):
    """ボットの記憶全体"""

    bot_id: int = Field(description="ボットID")

    # 長期記憶
    long_term_core: dict[str, str] = Field(
        default_factory=dict,
        description="コア長期記憶（履歴書から。occupation, experience等）",
    )
    long_term_acquired: list[AcquiredMemory] = Field(
        default_factory=list,
        description="獲得した長期記憶",
    )

    # 短期記憶
    short_term: list[ShortTermMemory] = Field(
        default_factory=list,
        description="短期記憶リスト",
    )

    # 連作状態
    series: SeriesState = Field(
        default_factory=SeriesState,
        description="連作つぶやきの状態",
    )

    # 最近の投稿履歴（プロンプト用）
    recent_posts: list[str] = Field(
        default_factory=list,
        description="最近の投稿内容（最新10件）",
    )

    # メタデータ
    last_updated: str | None = Field(default=None, description="最終更新日時")

    def decay_short_term(self, decay_rate: float = 0.1) -> None:
        """短期記憶を減衰させる"""
        surviving = []
        for memory in self.short_term:
            memory.strength -= decay_rate
            if memory.strength > 0.0:
                surviving.append(memory)
        self.short_term = surviving

    def add_short_term(self, content: str, source: str = "post") -> None:
        """短期記憶を追加"""
        self.short_term.append(
            ShortTermMemory(
                content=content,
                strength=1.0,
                created_at=datetime.now().isoformat(),
                source=source,
            )
        )
        # 最大20件に制限
        if len(self.short_term) > 20:
            # strength が低いものから削除
            self.short_term.sort(key=lambda m: m.strength, reverse=True)
            self.short_term = self.short_term[:20]

    def reinforce_short_term(self, keyword: str, boost: float = 0.3) -> bool:
        """
        キーワードに関連する短期記憶を強化（リアクションをもらった時など）

        Returns:
            強化された記憶があればTrue
        """
        reinforced = False
        for memory in self.short_term:
            if keyword.lower() in memory.content.lower():
                old_strength = memory.strength
                memory.strength = min(1.0, memory.strength + boost)
                if memory.strength > old_strength:
                    reinforced = True
        return reinforced

    def check_and_promote(self, threshold: float = 0.95) -> list[str]:
        """
        strength閾値を超えた短期記憶を長期記憶に昇格

        Returns:
            昇格した記憶のリスト
        """
        promoted = []
        remaining = []

        for memory in self.short_term:
            if memory.strength >= threshold:
                # 長期記憶に昇格
                self.promote_to_long_term(
                    content=memory.content,
                    importance=0.6,  # リアクションで強化されたので重要度高め
                )
                promoted.append(memory.content)
            else:
                remaining.append(memory)

        self.short_term = remaining
        return promoted

    def promote_to_long_term(self, content: str, importance: float = 0.5) -> None:
        """短期記憶を長期記憶に昇格"""
        self.long_term_acquired.append(
            AcquiredMemory(
                content=content,
                acquired_at=datetime.now().isoformat(),
                importance=importance,
            )
        )
        # 最大50件に制限
        if len(self.long_term_acquired) > 50:
            self.long_term_acquired.sort(key=lambda m: m.importance, reverse=True)
            self.long_term_acquired = self.long_term_acquired[:50]

    def add_recent_post(self, content: str) -> None:
        """最近の投稿を追加"""
        self.recent_posts.append(content)
        if len(self.recent_posts) > 10:
            self.recent_posts = self.recent_posts[-10:]

    def get_active_interests(self) -> list[str]:
        """現在興味を持っているトピック（strength が高い短期記憶）"""
        strong_memories = [m for m in self.short_term if m.strength >= 0.5]
        return [m.content for m in strong_memories[:5]]

    def start_series(self, theme: str, total: int) -> None:
        """連作を開始"""
        self.series = SeriesState(
            active=True,
            theme=theme,
            current_index=0,
            total_planned=total,
            posts=[],
        )

    def advance_series(self, post_content: str) -> bool:
        """連作を進める。完了したらTrueを返す"""
        if not self.series.active:
            return False

        self.series.posts.append(post_content)
        self.series.current_index += 1

        if self.series.current_index >= self.series.total_planned:
            # 連作完了
            self.series = SeriesState()
            return True

        return False
