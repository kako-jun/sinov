"""
ベースリポジトリ（共通機能）
"""

import json
from abc import ABC
from pathlib import Path


class ResidentJsonRepository(ABC):
    """住人ごとのJSONファイルを扱うリポジトリの基底クラス"""

    def __init__(self, residents_dir: Path):
        self.residents_dir = residents_dir

    def _get_resident_dir(self, npc_id: int) -> Path:
        """住人ディレクトリを取得（存在しない場合は作成）"""
        from ...domain.npc_utils import format_npc_name

        resident_dir = self.residents_dir / format_npc_name(npc_id)
        resident_dir.mkdir(parents=True, exist_ok=True)
        return resident_dir

    def _get_resident_file(self, npc_id: int, filename: str) -> Path:
        """住人ごとのファイルパスを取得"""
        return self._get_resident_dir(npc_id) / filename

    def _load_json(self, file_path: Path) -> dict | None:
        """JSONファイルを読み込み"""
        if not file_path.exists():
            return None
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_json(self, file_path: Path, data: dict) -> None:
        """JSONファイルに保存"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
