"""
投稿コンテンツ生成戦略
"""

import random

from ..config import ContentSettings
from .memory import BotMemory
from .models import BotProfile, BotState, HabitType, Interests, Prompts, StyleType
from .queue import ConversationContext, ReplyTarget

# 連作を開始する確率
SERIES_START_PROBABILITY = 0.2

# 文体スタイルの説明
STYLE_DESCRIPTIONS: dict[StyleType, str] = {
    StyleType.NORMAL: "普通の口語体で書く",
    StyleType.OJISAN: "おじさん構文で書く（絵文字多用、「〜だネ❗」「頑張ってね😄👍」など）",
    StyleType.YOUNG: "若者言葉で書く（「まじで」「やばい」「ｗｗｗ」など）",
    StyleType.NICHAN: "2ch風に書く（「ｷﾀ━(ﾟ∀ﾟ)━!」「うp」「wktk」など）",
    StyleType.OTAKU: "オタク構文で書く（「尊い」「神」「推せる」など）",
    StyleType.POLITE: "丁寧語で書く（「〜ですね」「〜ました」など）",
    StyleType.TERSE: "短く簡潔に書く（1文で、余計な言葉を省く）",
}

# 習慣の説明
HABIT_DESCRIPTIONS: dict[HabitType, str] = {
    HabitType.NEWS_SUMMARIZER: "ニュースや情報を要約して共有する傾向",
    HabitType.EMOJI_HEAVY: "絵文字を多用する",
    HabitType.TIP_SHARER: "「〜すると便利」「〜がおすすめ」などのTipsを共有する",
    HabitType.WIP_POSTER: "制作過程や途中経過を共有する",
    HabitType.QUESTION_ASKER: "質問形式や「〜ってどうなんだろう」が多い",
    HabitType.SELF_DEPRECATING: "自虐的・謙遜した言い方をする",
    HabitType.ENTHUSIASTIC: "テンション高めで熱量のある書き方",
}


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
        event_topics: list[str] | None = None,
        merged_prompts: Prompts | None = None,
        rejected_posts: list[dict[str, str]] | None = None,
    ) -> str:
        """LLM用のプロンプトを生成"""
        # 連作中かどうかチェック
        if memory and memory.series.active:
            return self._create_series_prompt(profile, memory, merged_prompts)

        # トピック選択: 通常の興味 + 新しく発見したトピック + 短期記憶 + イベントトピック
        all_topics = profile.interests.topics + state.discovered_topics
        if memory:
            all_topics += memory.get_active_interests()
        if event_topics:
            all_topics += event_topics
        topic = random.choice(all_topics) if all_topics else "プログラミング"

        # 前回投稿との文脈継続（記憶から取得）
        context_continuation = ""
        recent_posts = memory.recent_posts if memory else state.post_history
        if recent_posts and random.random() < self.settings.context_continuation_probability:
            last_post = recent_posts[-1]
            context_continuation = (
                f'\n前回の投稿: "{last_post}"' "\n→ この流れを続けるか、関連した話題にする"
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

        # 文体スタイル
        style_instruction = self._get_style_instruction(profile.style)

        # 習慣の反映
        habit_instructions = self._get_habit_instructions(profile.habits)

        # プロンプト（positive/negative）
        prompt_instructions = self._get_prompt_instructions(merged_prompts)

        # 好み・嫌い・価値観
        preferences_context = self._get_preferences_context(profile.interests)
        preferences_section = ""
        if preferences_context:
            preferences_section = f"\n\n【この人の好み】\n{preferences_context}"

        # 過去のrejectからの反省
        rejection_feedback = self._get_rejection_feedback(rejected_posts)

        prompt = f"""以下の条件でSNS投稿を1つ書け:

テーマ: {topic}{context_continuation}{news_context}{memory_context}
文字数: 最大{profile.behavior.post_length_max}文字

【文体】
{style_instruction}{preferences_section}

【条件】
- 必ず日本語で書け（中国語は絶対に使うな）
- 1文か2文の文
{prompt_instructions}{habit_instructions}{history_constraint}{rejection_feedback}

投稿:"""

        return prompt

    def _get_style_instruction(self, style: StyleType) -> str:
        """文体スタイルの指示を取得"""
        return STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS[StyleType.NORMAL])

    def _get_habit_instructions(self, habits: list[HabitType]) -> str:
        """習慣の指示を取得"""
        if not habits:
            return ""

        lines = ["\n【この人の傾向】"]
        for habit in habits:
            desc = HABIT_DESCRIPTIONS.get(habit)
            if desc:
                lines.append(f"- {desc}")
        return "\n".join(lines) if len(lines) > 1 else ""

    def _get_prompt_instructions(self, prompts: Prompts | None) -> str:
        """positive/negativeプロンプトの指示を取得"""
        if not prompts:
            return ""

        lines = []
        if prompts.positive:
            for p in prompts.positive:
                lines.append(f"- {p}")
        if prompts.negative:
            lines.append("\n【禁止事項】")
            for n in prompts.negative:
                lines.append(f"- {n}")

        return "\n".join(lines) if lines else ""

    def _get_preferences_context(self, interests: Interests) -> str:
        """好み/嫌いのコンテキストを取得"""
        lines = []

        # 好きなもの
        if interests.likes:
            like_items = []
            for category, items in interests.likes.items():
                if items:
                    like_items.append(f"{category}: {', '.join(items[:3])}")
            if like_items:
                lines.append("好きなもの: " + "、".join(like_items[:3]))

        # 嫌いなもの
        if interests.dislikes:
            dislike_items = []
            for category, items in interests.dislikes.items():
                if items:
                    dislike_items.append(f"{category}: {', '.join(items[:2])}")
            if dislike_items:
                lines.append("避けるもの: " + "、".join(dislike_items[:2]))

        # 価値観
        if interests.values:
            lines.append("大事にしていること: " + "、".join(interests.values[:3]))

        return "\n".join(lines) if lines else ""

    def _get_rejection_feedback(self, rejected_posts: list[dict[str, str]] | None) -> str:
        """過去のrejectからのフィードバックを取得"""
        if not rejected_posts:
            return ""

        lines = ["\n\n【過去の失敗から学ぶ】"]
        for post in rejected_posts[:2]:  # 最新2件のみ
            content = post.get("content", "")[:30]
            reason = post.get("reason", "理由不明")
            lines.append(f"- NG例: 「{content}...」 → 理由: {reason}")

        lines.append("⚠️ 上記と同じ失敗を繰り返さないこと")
        return "\n".join(lines)

    def _create_series_prompt(
        self,
        profile: BotProfile,
        memory: BotMemory,
        merged_prompts: Prompts | None = None,
    ) -> str:
        """連作つぶやき用のプロンプトを生成"""
        series = memory.series
        idx = series.current_index + 1
        total = series.total_planned

        # これまでの投稿を文脈として渡す
        previous_posts = "\n".join(f"{i+1}投稿目: {p}" for i, p in enumerate(series.posts))

        # 文体スタイル
        style_instruction = self._get_style_instruction(profile.style)

        # プロンプト（positive/negative）
        prompt_instructions = self._get_prompt_instructions(merged_prompts)

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
{prompt_instructions}

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

    def create_reply_prompt(
        self,
        profile: BotProfile,
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
        style_instruction = self._get_style_instruction(profile.style)

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
- 必ず日本語で書く{closing_hint}{negative_instructions}

返信:"""

        return prompt

    def create_mumble_prompt(
        self,
        profile: BotProfile,
        target_name: str,
        target_content: str,
        merged_prompts: Prompts | None = None,
    ) -> str:
        """ぶつぶつ（引用なしの言及）用のプロンプトを生成"""
        # 文体スタイル
        style_instruction = self._get_style_instruction(profile.style)

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
- 必ず日本語で書く{negative_instructions}

独り言:"""

        return prompt
