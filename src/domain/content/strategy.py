"""
投稿コンテンツ生成戦略

ファサードとして各コンポーネントを組み合わせる
"""

import random

from ...config import ContentSettings
from ..memory import NpcMemory
from ..models import NpcProfile, NpcState, Prompts
from ..queue import ConversationContext, ReplyTarget
from .content_processor import ContentProcessor
from .prompt_builder import PromptBuilder

# 連作を開始する確率
SERIES_START_PROBABILITY = 0.2


class ContentStrategy:
    """投稿コンテンツの生成戦略（ファサード）"""

    def __init__(self, settings: ContentSettings):
        self.settings = settings
        self.prompt_builder = PromptBuilder()
        self.processor = ContentProcessor()

    def create_prompt(
        self,
        profile: NpcProfile,
        state: NpcState,
        memory: NpcMemory | None = None,
        shared_news: list[str] | None = None,
        event_topics: list[str] | None = None,
        merged_prompts: Prompts | None = None,
        rejected_posts: list[dict[str, str]] | None = None,
    ) -> str:
        """LLM用のプロンプトを生成"""
        if memory and memory.series.active:
            return self._create_series_prompt(profile, memory, merged_prompts)

        topic = self._select_topic(profile, state, memory, event_topics)
        recent_posts = memory.recent_posts if memory else state.post_history

        # コンテキスト情報を収集
        context = self._build_topic_context(memory, recent_posts, shared_news, topic)
        history_constraint = self._build_history_constraint(recent_posts)

        # スタイル指示を収集
        style = self.prompt_builder.get_style_instruction(profile.style)
        prefs = self.prompt_builder.get_preferences_context(profile.interests)
        prefs_section = f"\n\n【この人の好み】\n{prefs}" if prefs else ""

        # 追加指示を収集
        instructions = (
            self.prompt_builder.get_prompt_instructions(merged_prompts)
            + self.prompt_builder.get_habit_instructions(profile.habits)
            + self.prompt_builder.get_writing_style_instructions(profile.writing_style)
            + history_constraint
            + self.prompt_builder.get_rejection_feedback(rejected_posts)
        )

        # Markdown対応の場合は長めの文章もOK
        if profile.behavior.use_markdown or profile.behavior.use_code_blocks:
            length_hint = "- 複数の文や段落で書いてもよい"
        else:
            length_hint = "- 1文か2文の短い文"

        return f"""以下の条件でSNS投稿を1つ書け:

テーマ: {topic}{context}
文字数: 最大{profile.behavior.post_length_max}文字

【文体】
{style}{prefs_section}

【条件】
- 必ず日本語で書け（中国語は絶対に使うな）
{length_hint}
{instructions}

投稿:"""

    def _select_topic(
        self,
        profile: NpcProfile,
        state: NpcState,
        memory: NpcMemory | None,
        event_topics: list[str] | None,
    ) -> str:
        """トピックを選択"""
        all_topics = profile.interests.topics + state.discovered_topics
        if memory:
            all_topics += memory.get_active_interests()
        if event_topics:
            all_topics += event_topics
        return random.choice(all_topics) if all_topics else "プログラミング"

    def _build_topic_context(
        self,
        memory: NpcMemory | None,
        recent_posts: list[str],
        shared_news: list[str] | None,
        topic: str,
    ) -> str:
        """トピック関連のコンテキストを構築"""
        parts: list[str] = []

        # 前回投稿との文脈継続
        if recent_posts and random.random() < self.settings.context_continuation_probability:
            last = recent_posts[-1]
            parts.append(f'\n前回の投稿: "{last}"\n→ この流れを続けるか、関連した話題にする')

        # 共有ニュースの参照
        if random.random() < self.settings.news_reference_probability and shared_news:
            news = random.choice(shared_news)
            parts.append(
                f"\n最近のニュース: {news}\n"
                "→ このニュースに関連した感想や話題を書いてもよい\n"
                "→ ニュースを参考にした場合は、記事のURL（https://...）を投稿に含めること"
            )

        # 短期記憶から興味を取得
        if memory and memory.short_term:
            active = memory.get_active_interests()[:3]
            if active:
                parts.append("\n最近興味があること: " + "、".join(active))

        # 長期記憶から関連する経験
        if memory and memory.long_term_acquired:
            relevant = memory.get_relevant_long_term(topic, limit=2)
            if relevant:
                parts.append("\n過去の経験: " + "、".join(relevant))

        return "".join(parts)

    def _build_history_constraint(self, recent_posts: list[str]) -> str:
        """過去投稿の制約を構築"""
        check_posts = recent_posts[-self.settings.history_check_count :] if recent_posts else []
        if not check_posts:
            return ""
        constraint = "\n\n過去の投稿:\n" + "\n".join(f"- {p}" for p in check_posts)
        return (
            constraint + "\n\n⚠️ 上記と同じ内容・似た内容・同じ表現は絶対に使うな。"
            "新しい切り口や別のトピックで書け"
        )

    def _create_series_prompt(
        self,
        profile: NpcProfile,
        memory: NpcMemory,
        merged_prompts: Prompts | None = None,
    ) -> str:
        """連作つぶやき用のプロンプトを生成"""
        series = memory.series
        idx = series.current_index + 1
        total = series.total_planned

        # これまでの投稿を文脈として渡す
        previous_posts = "\n".join(f"{i+1}投稿目: {p}" for i, p in enumerate(series.posts))

        # 文体スタイル
        style_instruction = self.prompt_builder.get_style_instruction(profile.style)

        # プロンプト（positive/negative）
        prompt_instructions = self.prompt_builder.get_prompt_instructions(merged_prompts)

        prompt = f"""連作つぶやきの続きを書け:

テーマ: {series.theme}
現在: {idx}/{total}投稿目

これまでの投稿:
{previous_posts if previous_posts else "(まだなし - 1投稿目)"}

文字数: 最大{profile.behavior.post_length_max}文字

【文体】
{style_instruction}

条件:
- 必ず日本語で書け
- 前の投稿と関連した続きを書く
- {idx}投稿目らしい展開にする
- 「N/N投稿目」「N投稿目」などの番号を本文に書くな
{prompt_instructions}

{idx}投稿目:"""

        return prompt

    def should_start_series(self) -> bool:
        """連作を開始すべきか判定"""
        return random.random() < SERIES_START_PROBABILITY

    def generate_series_theme(self, profile: NpcProfile) -> tuple[str, int]:
        """連作のテーマと投稿数を生成"""
        topics = profile.interests.topics
        theme = random.choice(topics) if topics else "日常"
        total = random.randint(2, 5)
        return theme, total

    def clean_content(
        self, content: str, use_markdown: bool = False, use_code_blocks: bool = False
    ) -> str:
        """生成されたコンテンツをクリーンアップ"""
        return self.processor.clean(content, use_markdown, use_code_blocks)

    def validate_content(
        self, content: str, use_markdown: bool = False, use_code_blocks: bool = False
    ) -> bool:
        """コンテンツが有効かチェック"""
        return self.processor.validate(content, use_markdown, use_code_blocks)

    def adjust_length(
        self,
        content: str,
        min_length: int,
        max_length: int,
    ) -> str:
        """コンテンツの長さを調整"""
        return self.processor.adjust_length(content, min_length, max_length)

    def create_reply_prompt(
        self,
        profile: NpcProfile,
        reply_to: ReplyTarget,
        conversation: ConversationContext | None = None,
        relationship_type: str = "知り合い",
        affinity: float = 0.0,
        merged_prompts: Prompts | None = None,
    ) -> str:
        """リプライ用のプロンプトを生成"""
        depth = conversation.depth if conversation else 1

        # 会話履歴を構築
        history_text = ""
        if conversation and conversation.history:
            history_lines = []
            for h in conversation.history[-5:]:  # 最新5件
                history_lines.append(f"  {h['author']}: {h['content']}")
            history_text = "\n".join(history_lines)

        # 締めを促すかどうか
        closing_hint = ""
        if depth >= 3:
            closing_hint = "\n- そろそろ会話を締めてもよい（短い返事で）"
        elif depth >= 2:
            closing_hint = "\n- 長くなりすぎないように"

        # 文体スタイル
        style_instruction = self.prompt_builder.get_style_instruction(profile.style)

        # 文章スタイルの癖
        writing_style_instructions = self.prompt_builder.get_writing_style_instructions(
            profile.writing_style
        )

        # 禁止事項（negativeプロンプトのみ使用）
        negative_instructions = ""
        if merged_prompts and merged_prompts.negative:
            negative_instructions = "\n- " + "\n- ".join(merged_prompts.negative[:5])

        prompt = f"""あなたは{profile.name}です。リプライを書いてください。

【相手の投稿】
{reply_to.content}

【会話の流れ】
{history_text if history_text else "  (最初のリプライ)"}

【相手との関係】
関係: {relationship_type}

【文体】
{style_instruction}

【返信のルール】
- 短めに（20〜80文字程度）
- 会話の文脈に沿った返信をする
- 必ず日本語で書く{closing_hint}{negative_instructions}{writing_style_instructions}

返信:"""

        return prompt

    def create_mumble_prompt(
        self,
        profile: NpcProfile,
        target_name: str,
        target_content: str,
        merged_prompts: Prompts | None = None,
    ) -> str:
        """ぶつぶつ（引用なしの言及）用のプロンプトを生成"""
        # 文体スタイル
        style_instruction = self.prompt_builder.get_style_instruction(profile.style)

        # 文章スタイルの癖
        writing_style_instructions = self.prompt_builder.get_writing_style_instructions(
            profile.writing_style
        )

        # 禁止事項（negativeプロンプトのみ使用）
        negative_instructions = ""
        if merged_prompts and merged_prompts.negative:
            negative_instructions = "\n- " + "\n- ".join(merged_prompts.negative[:5])

        prompt = f"""あなたは{profile.name}です。
誰かの投稿を見て、独り言をつぶやいてください。
直接返信はせず、ぶつぶつと言及するだけです。

【見た投稿】
{target_name}さん: {target_content}

【文体】
{style_instruction}

【ルール】
- 直接話しかけない（「〜さん、」で始めない）
- 「〜してるな」「〜だなあ」のような独り言
- 20〜60文字程度
- 必ず日本語で書く{negative_instructions}{writing_style_instructions}

独り言:"""

        return prompt
