"""
ボット状態リポジトリ
"""

import json
from pathlib import Path

from ...domain.models import BotState


class StateRepository:
    """住人フォルダごとにボット状態を永続化"""

    def __init__(self, residents_dir: Path):
        self.residents_dir = residents_dir

    def _get_file_path(self, bot_id: int) -> Path:
        """ボットIDに対応するファイルパス"""
        resident_dir = self.residents_dir / f"bot{bot_id:03d}"
        resident_dir.mkdir(parents=True, exist_ok=True)
        return resident_dir / "state.json"

    def load_all(self) -> dict[int, BotState]:
        """全ボットの状態を読み込み"""
        states: dict[int, BotState] = {}

        if not self.residents_dir.exists():
            return states

        for resident_dir in self.residents_dir.iterdir():
            if not resident_dir.is_dir() or not resident_dir.name.startswith("bot"):
                continue

            state_file = resident_dir / "state.json"
            if not state_file.exists():
                continue

            try:
                bot_id = int(resident_dir.name[3:])
                state = self.load(bot_id)
                if state:
                    states[bot_id] = state
            except (ValueError, Exception) as e:
                print(f"⚠️  Failed to load state from {resident_dir.name}: {e}")

        return states

    def load(self, bot_id: int) -> BotState | None:
        """単一ボットの状態を読み込み"""
        file_path = self._get_file_path(bot_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return BotState.model_validate(data)
        except Exception as e:
            print(f"⚠️  Failed to load state for bot{bot_id:03d}: {e}")
            return None

    def create_initial(self, bot_id: int) -> BotState:
        """初期状態を作成"""
        return BotState(
            id=bot_id,
            last_post_time=0,
            next_post_time=0,
            total_posts=0,
        )

    def save_all(self, states: dict[int, BotState]) -> None:
        """全ボットの状態を保存"""
        for state in states.values():
            self.save(state)

    def save(self, state: BotState) -> None:
        """単一ボットの状態を保存"""
        file_path = self._get_file_path(state.id)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
