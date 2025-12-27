"""
NPC状態リポジトリ
"""

from pathlib import Path

from ...domain import NpcState, format_npc_name
from .base_repo import ResidentJsonRepository


class StateRepository(ResidentJsonRepository):
    """住人フォルダごとにNPC状態を永続化"""

    def _get_file_path(self, npc_id: int) -> Path:
        """NPC IDに対応するファイルパス"""
        return self._get_resident_file(npc_id, "state.json")

    def load_all(self) -> dict[int, NpcState]:
        """全NPCの状態を読み込み"""
        states: dict[int, NpcState] = {}

        if not self.residents_dir.exists():
            return states

        for resident_dir in self.residents_dir.iterdir():
            if not resident_dir.is_dir() or not resident_dir.name.startswith("npc"):
                continue

            state_file = resident_dir / "state.json"
            if not state_file.exists():
                continue

            try:
                npc_id = int(resident_dir.name[3:])
                state = self.load(npc_id)
                if state:
                    states[npc_id] = state
            except (ValueError, Exception) as e:
                print(f"⚠️  Failed to load state from {resident_dir.name}: {e}")

        return states

    def load(self, npc_id: int) -> NpcState | None:
        """単一NPCの状態を読み込み"""
        file_path = self._get_file_path(npc_id)

        if not file_path.exists():
            return None

        try:
            data = self._load_json(file_path)
            if data is None:
                return None
            return NpcState.model_validate(data)
        except Exception as e:
            print(f"⚠️  Failed to load state for {format_npc_name(npc_id)}: {e}")
            return None

    def create_initial(self, npc_id: int) -> NpcState:
        """初期状態を作成"""
        return NpcState(
            id=npc_id,
            last_post_time=0,
            next_post_time=0,
            total_posts=0,
        )

    def save_all(self, states: dict[int, NpcState]) -> None:
        """全NPCの状態を保存"""
        for state in states.values():
            self.save(state)

    def save(self, state: NpcState) -> None:
        """単一NPCの状態を保存"""
        file_path = self._get_file_path(state.id)
        self._save_json(file_path, state.model_dump(mode="json"))
