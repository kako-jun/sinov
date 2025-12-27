"""
プロンプト構築ロジック
"""

from ..models import HabitType, Interests, Prompts, StyleType, WritingStyle
from ..text_processor import get_writing_style_prompt_instructions

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
    HabitType.HASHTAG_USER: "時々ハッシュタグを付ける（#Python #開発 など）",
}


class PromptBuilder:
    """プロンプト構築を担当"""

    @staticmethod
    def get_style_instruction(style: StyleType) -> str:
        """文体スタイルの指示を取得"""
        return STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS[StyleType.NORMAL])

    @staticmethod
    def get_habit_instructions(habits: list[HabitType]) -> str:
        """習慣の指示を取得"""
        if not habits:
            return ""

        lines = ["\n【この人の傾向】"]
        for habit in habits:
            desc = HABIT_DESCRIPTIONS.get(habit)
            if desc:
                lines.append(f"- {desc}")
        return "\n".join(lines) if len(lines) > 1 else ""

    @staticmethod
    def get_writing_style_instructions(writing_style: WritingStyle | None) -> str:
        """文章スタイルの指示を取得（プロンプトで指示すべきもののみ）"""
        if not writing_style:
            return ""

        instructions = get_writing_style_prompt_instructions(writing_style)
        if not instructions:
            return ""

        lines = ["\n【文章の癖】"]
        for instruction in instructions:
            lines.append(f"- {instruction}")
        return "\n".join(lines)

    @staticmethod
    def get_prompt_instructions(prompts: Prompts | None) -> str:
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

    @staticmethod
    def get_preferences_context(interests: Interests) -> str:
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

    @staticmethod
    def get_rejection_feedback(rejected_posts: list[dict[str, str]] | None) -> str:
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
