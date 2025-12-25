"""
投稿コンテンツ生成戦略
"""

import random

from ..config import ContentSettings
from .models import BotProfile, BotState


class ContentStrategy:
    """投稿コンテンツの生成戦略"""

    def __init__(self, settings: ContentSettings):
        self.settings = settings

    def create_prompt(
        self,
        profile: BotProfile,
        state: BotState,
        shared_news: list[str] | None = None,
    ) -> str:
        """LLM用のプロンプトを生成"""
        # トピック選択: 通常の興味 + 新しく発見したトピック
        all_topics = profile.interests.topics + state.discovered_topics
        topic = random.choice(all_topics) if all_topics else "プログラミング"

        # 前回投稿との文脈継続
        context_continuation = ""
        if (
            state.last_post_content
            and random.random() < self.settings.context_continuation_probability
        ):
            context_continuation = (
                f'\n前回の投稿: "{state.last_post_content}"'
                "\n→ この流れを続けるか、関連した話題にする"
            )

        # 共有ニュースの参照
        news_context = ""
        if random.random() < self.settings.news_reference_probability and shared_news:
            news_item = random.choice(shared_news)
            news_context = f"\n最近のニュース: {news_item}\n→ これに関連した話題もOK"

        # 過去投稿の制約（重複防止）
        recent_posts = state.post_history[-self.settings.history_check_count :]
        history_constraint = ""
        if recent_posts:
            history_constraint = "\n\n過去の投稿:\n" + "\n".join(f"- {p}" for p in recent_posts)
            history_constraint += "\n\n⚠️ これらとまったく同じ内容・表現は使うな"

        prompt = f"""以下の条件でSNS投稿を1つ書け:

テーマ: {topic}{context_continuation}{news_context}
文字数: 最大{profile.behavior.post_length_max}文字
条件:
- 必ず日本語で書け（中国語は絶対に使うな）
- 1文か2文のカジュアルな文
- 記号・マークダウン禁止{history_constraint}

投稿:"""

        return prompt

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
