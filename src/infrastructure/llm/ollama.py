"""
Ollama LLMプロバイダー
"""

import ollama

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """ローカルLLM（Ollama）を使った文章生成"""

    def __init__(self, host: str, model: str):
        self.host = host
        self.model = model
        self.client = ollama.Client(host=host)

    async def generate(self, prompt: str, max_length: int | None = None) -> str:
        """プロンプトから文章を生成"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
            )

            content: str = str(response["response"]).strip()

            # 最大長でトリミング
            if max_length and len(content) > max_length:
                content = content[:max_length].rsplit(" ", 1)[0] + "..."

            return content
        except Exception as e:
            print(f"⚠️  LLM generation failed: {e}")
            raise

    def is_available(self) -> bool:
        """Ollamaが利用可能かチェック"""
        try:
            self.client.list()
            return True
        except Exception:
            return False
