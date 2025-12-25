"""
投稿コンテンツ生成戦略
"""

import random

from ..config import ContentSettings
from .memory import BotMemory
from .models import BotProfile, BotState

# 連作を開始する確率
SERIES_START_PROBABILITY = 0.2


class ContentStrategy:
    """投稿コンテンツの生成戦略"""

    def __init__(self, settings: ContentSettings):
        self.settings = settings

    def create_prompt(
        self,
        profile: BotProfile,
        state: BotState,
        memory: BotMemory | None = None,
        shared_news: list[str] | None = None,
    ) -> str:
        """LLM用のプロンプトを生成"""
        # 連作中かどうかチェック
        if memory and memory.series.active:
            return self._create_series_prompt(profile, memory)

        # トピック選択: 通常の興味 + 新しく発見したトピック + 短期記憶
        all_topics = profile.interests.topics + state.discovered_topics
        if memory:
            all_topics += memory.get_active_interests()
        topic = random.choice(all_topics) if all_topics else "プログラミング"

        # 前回投稿との文脈継続（記憶から取得）
        context_continuation = ""
        recent_posts = memory.recent_posts if memory else state.post_history
        if recent_posts and random.random() < self.settings.context_continuation_probability:
            last_post = recent_posts[-1]
            context_continuation = (
                f'\n前回の投稿: "{last_post}"'
                "\n→ この流れを続けるか、関連した話題にする"
            )

        # 共有ニュースの参照
        news_context = ""
        if random.random() < self.settings.news_reference_probability and shared_news:
            news_item = random.choice(shared_news)
            news_context = f"\n最近のニュース: {news_item}\n→ これに関連した話題もOK"

        # 短期記憶から興味を取得
        memory_context = ""
        if memory and memory.short_term:
            active_interests = memory.get_active_interests()[:3]
            if active_interests:
                memory_context = "\n最近興味があること: " + "、".join(active_interests)

        # 過去投稿の制約（重複防止）
        history_constraint = ""
        check_posts = recent_posts[-self.settings.history_check_count :] if recent_posts else []
        if check_posts:
            history_constraint = "\n\n過去の投稿:\n" + "\n".join(f"- {p}" for p in check_posts)
            history_constraint += "\n\n⚠️ これらとまったく同じ内容・表現は使うな"

        prompt = f"""以下の条件でSNS投稿を1つ書け:

テーマ: {topic}{context_continuation}{news_context}{memory_context}
文字数: 最大{profile.behavior.post_length_max}文字
条件:
- 必ず日本語で書け（中国語は絶対に使うな）
- 1文か2文のカジュアルな文
- 記号・マークダウン禁止{history_constraint}

投稿:"""

        return prompt

    def _create_series_prompt(self, profile: BotProfile, memory: BotMemory) -> str:
        """連作つぶやき用のプロンプトを生成"""
        series = memory.series
        idx = series.current_index + 1
        total = series.total_planned

        # これまでの投稿を文脈として渡す
        previous_posts = "\n".join(f"{i+1}投稿目: {p}" for i, p in enumerate(series.posts))

        prompt = f"""連作つぶやきの続きを書け:

テーマ: {series.theme}
現在: {idx}/{total}投稿目

これまでの投稿:
{previous_posts if previous_posts else "(まだなし - 1投稿目)"}

文字数: 最大{profile.behavior.post_length_max}文字
条件:
- 必ず日本語で書け
- 前の投稿と関連した続きを書く
- {idx}投稿目らしい展開にする
- 記号・マークダウン禁止

{idx}投稿目:"""

        return prompt

    def should_start_series(self) -> bool:
        """連作を開始すべきか判定"""
        return random.random() < SERIES_START_PROBABILITY

    def generate_series_theme(self, profile: BotProfile) -> tuple[str, int]:
        """連作のテーマと投稿数を生成"""
        topics = profile.interests.topics
        theme = random.choice(topics) if topics else "日常"
        total = random.randint(2, 5)
        return theme, total

    def clean_content(self, content: str) -> str:
        """生成されたコンテンツをクリーンアップ"""
        import re

        # 余計な記号を削除
        content = content.replace("###", "").replace("```", "").strip()

        # 改行を整理（2つ以上の連続改行は1つに）
        content = re.sub(r"\n{2,}", "\n", content)

        # 連続空白を1つに
        content = re.sub(r"\s+", " ", content).strip()

        return content

    def validate_content(self, content: str) -> bool:
        """コンテンツが有効かチェック"""
        # 禁止文字チェック（マークダウン記号）
        if "```" in content or "###" in content or "**" in content:
            return False
        return True

    def adjust_length(
        self,
        content: str,
        min_length: int,
        max_length: int,
    ) -> str:
        """コンテンツの長さを調整"""
        if len(content) < min_length:
            # 最小長に満たない場合は補完
            content = content + " " * (min_length - len(content))
        elif len(content) > max_length:
            # 最大長を超える場合はトリミング
            content = content[:max_length].rsplit(" ", 1)[0] + "..."

        return content
