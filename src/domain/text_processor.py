"""
文章スタイル加工処理

生成された文章にwriting_styleに基づく加工を適用する。
誤字、改行、句読点、特殊な癖などを後処理で追加。
"""

import random
import re

from .models import LineBreakStyle, PunctuationStyle, WritingQuirk, WritingStyle

# 誤字変換テーブル（打ち間違いやすい文字の組み合わせ）
TYPO_MAP = {
    "す": ["そ", "さ"],
    "い": ["う", "お"],
    "た": ["と", "ち"],
    "て": ["と", "ち"],
    "な": ["の", "に"],
    "に": ["の", "な"],
    "の": ["な", "に"],
    "か": ["き", "く"],
    "し": ["す", "さ"],
    "で": ["ど", "て"],
    "れ": ["る", "ら"],
    "る": ["れ", "ら"],
    "を": ["お", "ほ"],
    "っ": ["つ", ""],
    "ー": ["ｰ", "-"],
}


class TextProcessor:
    """文章スタイル加工プロセッサ"""

    def __init__(self, writing_style: WritingStyle | None = None):
        self.style = writing_style or WritingStyle()

    def process(self, text: str) -> str:
        """
        文章にスタイル加工を適用

        処理順序:
        1. 句読点の調整
        2. 改行スタイルの適用
        3. 癖の追加
        4. 誤字の挿入（最後に行う）
        """
        if not text:
            return text

        # 1. 句読点の調整
        text = self._apply_punctuation(text)

        # 2. 改行スタイルの適用
        text = self._apply_line_breaks(text)

        # 3. 癖の追加
        text = self._apply_quirks(text)

        # 4. 誤字の挿入
        text = self._apply_typos(text)

        return text

    def _apply_punctuation(self, text: str) -> str:
        """句読点スタイルを適用"""
        style = self.style.punctuation

        if style == PunctuationStyle.FULL:
            # そのまま
            return text
        elif style == PunctuationStyle.COMMA_ONLY:
            # 「。」を削除
            return text.replace("。", "")
        elif style == PunctuationStyle.PERIOD_ONLY:
            # 「、」を削除
            return text.replace("、", "")
        elif style == PunctuationStyle.NONE:
            # 両方削除
            return text.replace("。", "").replace("、", "")
        return text

    def _apply_line_breaks(self, text: str) -> str:
        """改行スタイルを適用"""
        style = self.style.line_break

        if style == LineBreakStyle.NONE:
            # すべての改行を削除（陰キャスタイル）
            return text.replace("\n", "")

        elif style == LineBreakStyle.MINIMAL:
            # 最小限（デフォルト）- そのまま
            return text

        elif style == LineBreakStyle.SENTENCE:
            # 一文ごとに改行
            # 。！？の後に改行を挿入
            text = re.sub(r"([。！？])", r"\1\n", text)
            # 末尾の余分な改行を削除
            return text.rstrip("\n")

        elif style == LineBreakStyle.PARAGRAPH:
            # 段落形式（複数改行で区切る）
            # 。の後に2つの改行を挿入
            text = re.sub(r"([。])", r"\1\n\n", text)
            # ！？の後は1つの改行
            text = re.sub(r"([！？])", r"\1\n", text)
            # 末尾の余分な改行を削除
            return text.rstrip("\n")

        return text

    def _apply_quirks(self, text: str) -> str:
        """癖を適用"""
        for quirk in self.style.quirks:
            text = self._apply_single_quirk(text, quirk)
        return text

    def _apply_single_quirk(self, text: str, quirk: WritingQuirk) -> str:
        """個別の癖を適用"""

        if quirk == WritingQuirk.W_HEAVY:
            # 文末に「w」を追加
            text = self._add_to_sentence_end(text, "w", probability=0.4)

        elif quirk == WritingQuirk.KUSA:
            # 「笑」「w」を「草」に変換
            text = text.replace("笑", "草")
            text = re.sub(r"w+", "草", text)

        elif quirk == WritingQuirk.ELLIPSIS_HEAVY:
            # 文末に「…」を追加
            text = self._add_to_sentence_end(text, "…", probability=0.3)

        elif quirk == WritingQuirk.SUFFIX_NE:
            # 文末に「ね」を追加
            text = self._add_suffix_to_sentences(text, "ね", probability=0.3)

        elif quirk == WritingQuirk.SUFFIX_NA:
            # 文末に「な」を追加
            text = self._add_suffix_to_sentences(text, "な", probability=0.3)

        elif quirk == WritingQuirk.EXCLAMATION_HEAVY:
            # 「。」を「！」に変換
            text = self._replace_randomly(text, "。", "！", probability=0.4)

        elif quirk == WritingQuirk.QUESTION_HEAVY:
            # 文末に「？」を追加
            text = self._add_to_sentence_end(text, "？", probability=0.2)

        elif quirk == WritingQuirk.TILDE_HEAVY:
            # 語尾に「〜」を追加
            text = self._add_to_sentence_end(text, "〜", probability=0.3)

        elif quirk == WritingQuirk.PARENTHESES:
            # （）で補足を入れる（これはプロンプトで指示）
            pass

        elif quirk == WritingQuirk.ARROW:
            # 「→」を使う（これはプロンプトで指示）
            pass

        elif quirk == WritingQuirk.KATAKANA_ENGLISH:
            # カタカナ英語を使う（これはプロンプトで指示）
            pass

        elif quirk == WritingQuirk.ABBREVIATION:
            # 略語を使う（これはプロンプトで指示）
            pass

        return text

    def _apply_typos(self, text: str) -> str:
        """誤字を挿入"""
        if self.style.typo_rate <= 0:
            return text

        result = []
        for char in text:
            if char in TYPO_MAP and random.random() < self.style.typo_rate:
                # 誤字に置換
                typo_options = TYPO_MAP[char]
                result.append(random.choice(typo_options))
            else:
                result.append(char)

        return "".join(result)

    def _add_to_sentence_end(self, text: str, suffix: str, probability: float) -> str:
        """文末に文字を追加"""
        # 文末（。！？の前、または最後）に追加
        def replace_end(match: re.Match[str]) -> str:
            matched: str = match.group(0)
            if random.random() < probability:
                return suffix + matched
            return matched

        text = re.sub(r"([。！？])", replace_end, text)

        # 最後が句読点でない場合
        if text and text[-1] not in "。！？" and random.random() < probability:
            text += suffix

        return text

    def _add_suffix_to_sentences(
        self, text: str, suffix: str, probability: float
    ) -> str:
        """文末に語尾を追加（句読点の前）"""

        def replace_end(match: re.Match[str]) -> str:
            matched: str = match.group(0)
            if random.random() < probability:
                return suffix + matched
            return matched

        return re.sub(r"([。！？])", replace_end, text)

    def _replace_randomly(
        self, text: str, old: str, new: str, probability: float
    ) -> str:
        """確率的に文字を置換"""
        result = []
        for char in text:
            if char == old and random.random() < probability:
                result.append(new)
            else:
                result.append(char)
        return "".join(result)


# プロンプトで指示する癖の説明文
QUIRK_PROMPT_DESCRIPTIONS: dict[WritingQuirk, str] = {
    WritingQuirk.PARENTHESES: "（）で補足説明を入れることがある",
    WritingQuirk.ARROW: "「→」を使って流れを説明することがある",
    WritingQuirk.KATAKANA_ENGLISH: "カタカナ英語をよく使う（例：リスペクト、エモい）",
    WritingQuirk.ABBREVIATION: "略語や口語表現を使う（例：それな、わかる、まじ）",
}


def get_quirk_prompt_instructions(quirks: list[WritingQuirk]) -> list[str]:
    """プロンプトに含めるべき癖の指示を取得"""
    instructions = []
    for quirk in quirks:
        if quirk in QUIRK_PROMPT_DESCRIPTIONS:
            instructions.append(QUIRK_PROMPT_DESCRIPTIONS[quirk])
    return instructions


# 改行・句読点スタイルのプロンプト説明
LINE_BREAK_PROMPT_DESCRIPTIONS: dict[LineBreakStyle, str] = {
    LineBreakStyle.NONE: "改行せずに一気に書く",
    LineBreakStyle.SENTENCE: "一文ごとに改行する",
    LineBreakStyle.PARAGRAPH: "段落を作って書く（話題が変わるときに空行を入れる）",
}

PUNCTUATION_PROMPT_DESCRIPTIONS: dict[PunctuationStyle, str] = {
    PunctuationStyle.COMMA_ONLY: "句点（。）は使わない",
    PunctuationStyle.PERIOD_ONLY: "読点（、）は使わない",
    PunctuationStyle.NONE: "句読点は使わない",
}


def get_writing_style_prompt_instructions(style: WritingStyle | None) -> list[str]:
    """WritingStyleからプロンプト指示を生成"""
    if not style:
        return []

    instructions = []

    # 改行スタイル
    if style.line_break in LINE_BREAK_PROMPT_DESCRIPTIONS:
        instructions.append(LINE_BREAK_PROMPT_DESCRIPTIONS[style.line_break])

    # 句読点スタイル
    if style.punctuation in PUNCTUATION_PROMPT_DESCRIPTIONS:
        instructions.append(PUNCTUATION_PROMPT_DESCRIPTIONS[style.punctuation])

    # 癖（プロンプトで指示するもの）
    instructions.extend(get_quirk_prompt_instructions(style.quirks))

    return instructions
