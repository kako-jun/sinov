"""TextProcessor のユニットテスト"""

from src.domain import (
    LineBreakStyle,
    PunctuationStyle,
    TextProcessor,
    WritingStyle,
)


class TestTextProcessorPunctuation:
    """句読点スタイルのテスト"""

    def test_punctuation_full_keeps_all(self) -> None:
        """FULL: 句読点をそのまま維持"""
        style = WritingStyle(punctuation=PunctuationStyle.FULL)
        processor = TextProcessor(style)
        result = processor._apply_punctuation("こんにちは、世界。")
        assert result == "こんにちは、世界。"

    def test_punctuation_comma_only_removes_period(self) -> None:
        """COMMA_ONLY: 句点を削除"""
        style = WritingStyle(punctuation=PunctuationStyle.COMMA_ONLY)
        processor = TextProcessor(style)
        result = processor._apply_punctuation("こんにちは、世界。")
        assert result == "こんにちは、世界"

    def test_punctuation_period_only_removes_comma(self) -> None:
        """PERIOD_ONLY: 読点を削除"""
        style = WritingStyle(punctuation=PunctuationStyle.PERIOD_ONLY)
        processor = TextProcessor(style)
        result = processor._apply_punctuation("こんにちは、世界。")
        assert result == "こんにちは世界。"

    def test_punctuation_none_removes_all(self) -> None:
        """NONE: 句読点を全て削除"""
        style = WritingStyle(punctuation=PunctuationStyle.NONE)
        processor = TextProcessor(style)
        result = processor._apply_punctuation("こんにちは、世界。元気、ですか。")
        assert result == "こんにちは世界元気ですか"


class TestTextProcessorLineBreaks:
    """改行スタイルのテスト"""

    def test_line_break_none_removes_all(self) -> None:
        """NONE: 改行を全て削除"""
        style = WritingStyle(line_break=LineBreakStyle.NONE)
        processor = TextProcessor(style)
        result = processor._apply_line_breaks("こんにちは\n世界")
        assert result == "こんにちは世界"

    def test_line_break_minimal_keeps_as_is(self) -> None:
        """MINIMAL: そのまま維持"""
        style = WritingStyle(line_break=LineBreakStyle.MINIMAL)
        processor = TextProcessor(style)
        result = processor._apply_line_breaks("こんにちは\n世界")
        assert result == "こんにちは\n世界"

    def test_line_break_sentence_adds_after_punctuation(self) -> None:
        """SENTENCE: 句点・感嘆符・疑問符の後に改行"""
        style = WritingStyle(line_break=LineBreakStyle.SENTENCE)
        processor = TextProcessor(style)
        result = processor._apply_line_breaks("こんにちは。元気？はい！")
        assert result == "こんにちは。\n元気？\nはい！"

    def test_line_break_paragraph_adds_double_after_period(self) -> None:
        """PARAGRAPH: 句点の後に2つ改行"""
        style = WritingStyle(line_break=LineBreakStyle.PARAGRAPH)
        processor = TextProcessor(style)
        result = processor._apply_line_breaks("こんにちは。元気？")
        assert result == "こんにちは。\n\n元気？"


class TestTextProcessorProcess:
    """process メソッドの統合テスト"""

    def test_empty_text_returns_empty(self) -> None:
        """空文字列はそのまま返す"""
        processor = TextProcessor()
        assert processor.process("") == ""

    def test_default_style_minimal_changes(self) -> None:
        """デフォルトスタイルは最小限の変更"""
        # typo_rate=0 で誤字なし
        style = WritingStyle(typo_rate=0.0)
        processor = TextProcessor(style)
        result = processor.process("こんにちは、世界。")
        assert result == "こんにちは、世界。"

    def test_combined_styles(self) -> None:
        """複合スタイルの適用"""
        style = WritingStyle(
            punctuation=PunctuationStyle.COMMA_ONLY,
            line_break=LineBreakStyle.NONE,
            typo_rate=0.0,
        )
        processor = TextProcessor(style)
        result = processor.process("こんにちは、\n世界。")
        # 句点削除 + 改行削除
        assert result == "こんにちは、世界"


class TestTextProcessorTypos:
    """誤字挿入のテスト"""

    def test_typo_rate_zero_no_changes(self) -> None:
        """typo_rate=0 なら変更なし"""
        style = WritingStyle(typo_rate=0.0)
        processor = TextProcessor(style)
        result = processor._apply_typos("すいません")
        assert result == "すいません"

    def test_typo_rate_max_with_low_random(self) -> None:
        """typo_rate=0.1 で random が低い値なら変換される"""
        from unittest.mock import patch

        style = WritingStyle(typo_rate=0.1)
        processor = TextProcessor(style)

        # random.random() が常に 0.05 を返す（0.1 より小さい）
        with patch("src.domain.text_processor.random.random", return_value=0.05):
            with patch("src.domain.text_processor.random.choice", return_value="そ"):
                result = processor._apply_typos("す")

        # 「す」は「そ」に変換される
        assert result == "そ"
