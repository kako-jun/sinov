"""
ボット状態リポジトリ
"""

import json
from pathlib import Path

from ...domain.models import BotState


class StateRepository:
    """JSONファイルでボット状態を永続化"""

    def __init__(self, states_file: Path):
        self.states_file = states_file

    def load_all(self) -> dict[int, BotState]:
        """全ボットの状態を読み込み"""
        states: dict[int, BotState] = {}

        if not self.states_file.exists():
            return states

        try:
            with open(self.states_file) as f:
                states_data = json.load(f)

            for state_dict in states_data:
                state = BotState.model_validate(state_dict)
                states[state.id] = state
        except Exception as e:
            print(f"⚠️  Failed to load states: {e}")

        return states

    def load(self, bot_id: int) -> BotState | None:
        """単一ボットの状態を読み込み"""
        states = self.load_all()
        return states.get(bot_id)

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
        states_data = [state.model_dump(mode="json") for state in states.values()]

        with open(self.states_file, "w") as f:
            json.dump(states_data, f, indent=2, ensure_ascii=False)

    def save(self, state: BotState) -> None:
        """単一ボットの状態を保存（既存の状態とマージ）"""
        states = self.load_all()
        states[state.id] = state
        self.save_all(states)
