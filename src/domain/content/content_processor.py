"""
コンテンツ処理ロジック
"""

import re


class ContentProcessor:
    """生成されたコンテンツの処理を担当"""

    @staticmethod
    def clean(content: str, use_markdown: bool = False, use_code_blocks: bool = False) -> str:
        """生成されたコンテンツをクリーンアップ"""
        # Markdown非対応の場合のみ記号を削除
        if not use_markdown:
            content = content.replace("###", "").strip()
            # コードブロック非対応の場合のみ```を削除
            if not use_code_blocks:
                content = content.replace("```", "").strip()

        # 改行の処理
        if use_markdown or use_code_blocks:
            # Markdown対応時は二重改行（段落）を保持、3つ以上は2つに
            content = re.sub(r"\n{3,}", "\n\n", content)
            # 連続空白を1つに（改行は保持）
            content = re.sub(r"[^\S\n]+", " ", content).strip()
        else:
            # Markdown非対応時は改行を1つに圧縮
            content = re.sub(r"\n{2,}", "\n", content)
            # 連続空白を1つに
            content = re.sub(r"\s+", " ", content).strip()

        return content

    @staticmethod
    def validate(content: str, use_markdown: bool = False, use_code_blocks: bool = False) -> bool:
        """コンテンツが有効かチェック"""
        # Markdown非対応の場合のみヘッダー・強調をチェック
        if not use_markdown:
            if "###" in content or "**" in content:
                return False
        # コードブロック非対応の場合のみ```をチェック
        if not use_code_blocks and not use_markdown:
            if "```" in content:
                return False
        return True

    @staticmethod
    def adjust_length(
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
