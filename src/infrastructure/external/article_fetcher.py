"""
記事本文取得・要約クライアント
"""

import trafilatura


class ArticleFetcher:
    """URLから記事本文を取得（trafilatura使用）"""

    MAX_CONTENT_LENGTH = 5000  # LLMに渡す最大文字数

    def fetch_content(self, url: str) -> str | None:
        """
        URLから記事本文を取得

        Returns:
            記事本文（テキスト）、取得失敗時はNone
        """
        try:
            # trafilaturaでダウンロード＆本文抽出
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None

            text = trafilatura.extract(downloaded)
            if not text:
                return None

            # 長すぎる場合は切り詰め
            if len(text) > self.MAX_CONTENT_LENGTH:
                text = text[: self.MAX_CONTENT_LENGTH] + "..."

            return text
        except Exception as e:
            print(f"    ⚠️  記事取得失敗: {url[:50]}... ({e})")
            return None


class ArticleSummarizer:
    """記事を要約"""

    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def summarize(self, title: str, content: str) -> str:
        """
        記事を要約

        Args:
            title: 記事タイトル
            content: 記事本文

        Returns:
            要約文（200文字程度）
        """
        prompt = f"""以下の記事を200文字程度で要約してください。
結論や重要なポイントを含めてください。

【タイトル】
{title}

【本文】
{content[:3000]}

【要約】"""

        try:
            summary = await self.llm.generate(prompt, max_length=300)
            return summary.strip()
        except Exception as e:
            print(f"    ⚠️  要約生成失敗: {e}")
            return content[:200] + "..."  # フォールバック
