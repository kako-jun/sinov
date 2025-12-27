"""ContentProcessor のユニットテスト"""

from src.domain.content.content_processor import ContentProcessor


class TestContentProcessorClean:
    """clean メソッドのテスト"""

    def test_removes_markdown_headers(self) -> None:
        """マークダウンヘッダーを削除"""
        result = ContentProcessor.clean("### タイトル")
        assert result == "タイトル"

    def test_removes_code_blocks(self) -> None:
        """コードブロック記号を削除"""
        result = ContentProcessor.clean("```python\nprint('hello')\n```")
        assert "```" not in result

    def test_collapses_multiple_newlines(self) -> None:
        """複数の改行を1つに"""
        result = ContentProcessor.clean("こんにちは\n\n\n世界")
        assert result == "こんにちは 世界"  # 空白に変換

    def test_collapses_multiple_spaces(self) -> None:
        """複数の空白を1つに"""
        result = ContentProcessor.clean("こんにちは    世界")
        assert result == "こんにちは 世界"

    def test_strips_whitespace(self) -> None:
        """前後の空白を削除"""
        result = ContentProcessor.clean("  こんにちは  ")
        assert result == "こんにちは"

    def test_empty_string(self) -> None:
        """空文字列"""
        result = ContentProcessor.clean("")
        assert result == ""


class TestContentProcessorValidate:
    """validate メソッドのテスト"""

    def test_valid_content(self) -> None:
        """通常のコンテンツは有効"""
        assert ContentProcessor.validate("こんにちは、世界！") is True

    def test_invalid_code_block(self) -> None:
        """コードブロックを含むと無効"""
        assert ContentProcessor.validate("```python```") is False

    def test_invalid_markdown_header(self) -> None:
        """マークダウンヘッダーを含むと無効"""
        assert ContentProcessor.validate("### タイトル") is False

    def test_invalid_bold(self) -> None:
        """太字記号を含むと無効"""
        assert ContentProcessor.validate("**強調**") is False

    def test_empty_is_valid(self) -> None:
        """空文字列は有効"""
        assert ContentProcessor.validate("") is True


class TestContentProcessorAdjustLength:
    """adjust_length メソッドのテスト"""

    def test_within_range_no_change(self) -> None:
        """範囲内ならそのまま"""
        result = ContentProcessor.adjust_length("こんにちは", 3, 10)
        assert result == "こんにちは"

    def test_too_short_pads_with_spaces(self) -> None:
        """短すぎる場合はスペースで埋める"""
        result = ContentProcessor.adjust_length("Hi", 5, 10)
        assert len(result) == 5
        assert result.startswith("Hi")

    def test_too_long_truncates_with_ellipsis(self) -> None:
        """長すぎる場合は切り詰めて省略記号"""
        result = ContentProcessor.adjust_length("これは長い文章です", 1, 5)
        assert len(result) <= 8  # max + "..."
        assert result.endswith("...")

    def test_exact_min_length(self) -> None:
        """ちょうど最小長"""
        result = ContentProcessor.adjust_length("abc", 3, 10)
        assert result == "abc"

    def test_exact_max_length(self) -> None:
        """ちょうど最大長"""
        result = ContentProcessor.adjust_length("abcde", 1, 5)
        assert result == "abcde"
