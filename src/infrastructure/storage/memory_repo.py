"""
記憶リポジトリ - ボットの記憶をJSONファイルで永続化
"""

import json
from datetime import datetime
from pathlib import Path

from ...domain.memory import BotMemory


class MemoryRepository:
    """ボットの記憶をファイルで管理（住人フォルダごと）"""

    def __init__(self, residents_dir: Path):
        self.residents_dir = residents_dir

    def _get_file_path(self, bot_id: int) -> Path:
        """ボットIDに対応するファイルパス"""
        resident_dir = self.residents_dir / f"bot{bot_id:03d}"
        resident_dir.mkdir(parents=True, exist_ok=True)
        return resident_dir / "memory.json"

    def load(self, bot_id: int) -> BotMemory:
        """記憶を読み込み（ファイルがなければデフォルト）"""
        file_path = self._get_file_path(bot_id)

        if not file_path.exists():
            return BotMemory(bot_id=bot_id)

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return BotMemory.model_validate(data)
        except Exception as e:
            print(f"⚠️  Failed to load memory for bot{bot_id:03d}: {e}")
            return BotMemory(bot_id=bot_id)

    def save(self, memory: BotMemory) -> None:
        """記憶を保存"""
        file_path = self._get_file_path(memory.bot_id)
        memory.last_updated = datetime.now().isoformat()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    def load_all(self) -> dict[int, BotMemory]:
        """全ボットの記憶を読み込み"""
        memories: dict[int, BotMemory] = {}

        if not self.residents_dir.exists():
            return memories

        for resident_dir in self.residents_dir.iterdir():
            if not resident_dir.is_dir() or not resident_dir.name.startswith("bot"):
                continue

            memory_file = resident_dir / "memory.json"
            if not memory_file.exists():
                continue

            try:
                bot_id = int(resident_dir.name[3:])
                memories[bot_id] = self.load(bot_id)
            except (ValueError, Exception) as e:
                print(f"⚠️  Failed to load memory from {resident_dir.name}: {e}")

        return memories

    def initialize_from_profile(
        self, bot_id: int, occupation: str | None, experience: str | None
    ) -> BotMemory:
        """プロフィールから長期記憶を初期化"""
        memory = self.load(bot_id)

        # コア長期記憶を設定（履歴書から）
        if occupation:
            memory.long_term_core["occupation"] = occupation
        if experience:
            memory.long_term_core["experience"] = experience

        self.save(memory)
        return memory
