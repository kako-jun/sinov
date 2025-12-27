"""
コンテンツ処理ロジック
"""

import re


class ContentProcessor:
    """生成されたコンテンツの処理を担当"""

    # LLMが生成しがちなプレースホルダーパターン
    PLACEHOLDER_PATTERNS = [
        r"\[リンク[:：].*?\]",
        r"\[ハッシュタグ[:：].*?\]",
        r"\[URL[:：].*?\]",
        r"\[画像[:：].*?\]",
        r"\[添付[:：].*?\]",
        r"\[参考[:：].*?\]",
        r"\[出典[:：].*?\]",
        r"\[注[:：].*?\]",
        r"\d+[/／]\d+投稿目",  # 1/3投稿目
        r"\d+投稿目[:：]?",  # 2投稿目
        r"^投稿[:：]",  # 行頭の「投稿:」
    ]

    @staticmethod
    def clean(content: str, use_markdown: bool = False, use_code_blocks: bool = False) -> str:
        """生成されたコンテンツをクリーンアップ"""
        # プレースホルダーを除去
        for pattern in ContentProcessor.PLACEHOLDER_PATTERNS:
            content = re.sub(pattern, "", content, flags=re.MULTILINE)

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
            # 最大長を超える場合は句点・読点で切る
            truncated = content[:max_length]
            # 最後の句点・読点・感嘆符・疑問符を探す
            for punct in ["。", "！", "？", "!", "?", "、", ","]:
                last_pos = truncated.rfind(punct)
                if last_pos > max_length // 2:  # 半分より後ろにあれば採用
                    return truncated[: last_pos + 1]
            # 見つからなければそのまま切る（...は付けない）
            content = truncated

        return content
