"""
LLMプロバイダー抽象基底クラス
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLMプロバイダーのインターフェース"""

    @abstractmethod
    async def generate(self, prompt: str, max_length: int | None = None) -> str:
        """プロンプトから文章を生成"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        ...
