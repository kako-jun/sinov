"""
記憶リポジトリ - NPCの記憶をJSONファイルで永続化
"""

from datetime import datetime
from pathlib import Path

from ...domain.memory import NpcMemory
from ...domain.npc_utils import format_npc_name
from .base_repo import ResidentJsonRepository


class MemoryRepository(ResidentJsonRepository):
    """NPCの記憶をファイルで管理（住人フォルダごと）"""

    def _get_file_path(self, bot_id: int) -> Path:
        """NPC IDに対応するファイルパス"""
        return self._get_resident_file(bot_id, "memory.json")

    def load(self, bot_id: int) -> NpcMemory:
        """記憶を読み込み（ファイルがなければデフォルト）"""
        file_path = self._get_file_path(bot_id)

        if not file_path.exists():
            return NpcMemory(bot_id=bot_id)

        try:
            data = self._load_json(file_path)
            if data is None:
                return NpcMemory(bot_id=bot_id)
            return NpcMemory.model_validate(data)
        except Exception as e:
            print(f"⚠️  Failed to load memory for {format_npc_name(bot_id)}: {e}")
            return NpcMemory(bot_id=bot_id)

    def save(self, memory: NpcMemory) -> None:
        """記憶を保存"""
        file_path = self._get_file_path(memory.bot_id)
        memory.last_updated = datetime.now().isoformat()
        self._save_json(file_path, memory.model_dump(mode="json"))

    def load_all(self) -> dict[int, NpcMemory]:
        """全NPCの記憶を読み込み"""
        memories: dict[int, NpcMemory] = {}

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
    ) -> NpcMemory:
        """プロフィールから長期記憶を初期化"""
        memory = self.load(bot_id)

        # コア長期記憶を設定（履歴書から）
        if occupation:
            memory.long_term_core["occupation"] = occupation
        if experience:
            memory.long_term_core["experience"] = experience

        self.save(memory)
        return memory
