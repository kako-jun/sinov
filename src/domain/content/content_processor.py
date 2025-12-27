"""
コンテンツ処理ロジック
"""

import re


class ContentProcessor:
    """生成されたコンテンツの処理を担当"""

    @staticmethod
    def clean(content: str) -> str:
        """生成されたコンテンツをクリーンアップ"""
        # 余計な記号を削除
        content = content.replace("###", "").replace("```", "").strip()

        # 改行を整理（2つ以上の連続改行は1つに）
        content = re.sub(r"\n{2,}", "\n", content)

        # 連続空白を1つに
        content = re.sub(r"\s+", " ", content).strip()

        return content

    @staticmethod
    def validate(content: str) -> bool:
        """コンテンツが有効かチェック"""
        # 禁止文字チェック（マークダウン記号）
        if "```" in content or "###" in content or "**" in content:
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
