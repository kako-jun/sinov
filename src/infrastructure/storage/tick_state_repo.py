"""
tickコマンドのラウンドロビン状態を管理
"""

import json
from datetime import datetime
from pathlib import Path

from ...domain import TickState


class TickStateRepository:
    """tickの状態をJSONファイルで永続化"""

    def __init__(self, state_file: Path):
        self.state_file = state_file

    def load(self) -> TickState:
        """状態を読み込み（ファイルがなければデフォルト）"""
        if not self.state_file.exists():
            return TickState()

        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            return TickState.model_validate(data)
        except Exception as e:
            print(f"⚠️  Failed to load tick state: {e}")
            return TickState()

    def save(self, state: TickState) -> None:
        """状態を保存"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    def advance(self, count: int, total_bots: int) -> tuple[int, int]:
        """
        次のバッチのインデックス範囲を取得し、状態を更新

        Returns:
            (start_index, end_index): 処理対象のインデックス範囲
        """
        state = self.load()

        start = state.next_index
        end = min(start + count, total_bots)

        # 1周したらリセット
        next_index = end if end < total_bots else 0

        new_state = TickState(
            next_index=next_index,
            last_run_at=datetime.now().isoformat(),
            total_ticks=state.total_ticks + 1,
        )
        self.save(new_state)

        return start, end
