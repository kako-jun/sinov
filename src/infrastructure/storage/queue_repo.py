"""
投稿キューリポジトリ
"""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ...domain.queue import QueueEntry, QueueStatus


class QueueRepository:
    """ステータスごとにファイルを分けてキューを管理"""

    def __init__(self, queue_dir: Path):
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, status: QueueStatus) -> Path:
        """ステータスに対応するファイルパスを取得"""
        return self.queue_dir / f"{status.value}.json"

    def _load_file(self, status: QueueStatus) -> list[QueueEntry]:
        """指定ステータスのファイルを読み込み"""
        file_path = self._get_file_path(status)
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                return [QueueEntry.model_validate(entry) for entry in data]
        except Exception as e:
            print(f"⚠️  Failed to load {file_path}: {e}")
            return []

    def _save_file(self, status: QueueStatus, entries: list[QueueEntry]) -> None:
        """指定ステータスのファイルに保存"""
        file_path = self._get_file_path(status)
        data = [entry.model_dump(mode="json") for entry in entries]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def add(self, entry: QueueEntry) -> None:
        """エントリーを追加"""
        entries = self._load_file(entry.status)
        entries.append(entry)
        self._save_file(entry.status, entries)

    def get_by_id(self, entry_id: str) -> tuple[QueueEntry, QueueStatus] | None:
        """IDでエントリーを検索（全ステータスを横断）"""
        for status in QueueStatus:
            entries = self._load_file(status)
            for entry in entries:
                if entry.id == entry_id:
                    return entry, status
        return None

    def get_all(self, status: QueueStatus) -> list[QueueEntry]:
        """指定ステータスの全エントリーを取得"""
        return self._load_file(status)

    def move(
        self,
        entry_id: str,
        from_status: QueueStatus,
        to_status: QueueStatus,
        update_fn: Callable[[QueueEntry], None] | None = None,
    ) -> QueueEntry | None:
        """エントリーを別ステータスに移動"""
        # 元のファイルから削除
        from_entries = self._load_file(from_status)
        entry_to_move = None
        remaining = []

        for entry in from_entries:
            if entry.id == entry_id:
                entry_to_move = entry
            else:
                remaining.append(entry)

        if entry_to_move is None:
            return None

        # ステータス更新
        entry_to_move.status = to_status

        # 追加の更新があれば適用
        if update_fn:
            update_fn(entry_to_move)

        # 保存
        self._save_file(from_status, remaining)

        to_entries = self._load_file(to_status)
        to_entries.append(entry_to_move)
        self._save_file(to_status, to_entries)

        return entry_to_move

    def approve(self, entry_id: str, note: str | None = None) -> QueueEntry | None:
        """エントリーを承認"""

        def update(entry: QueueEntry) -> None:
            entry.reviewed_at = datetime.now()
            entry.review_note = note

        return self.move(
            entry_id,
            QueueStatus.PENDING,
            QueueStatus.APPROVED,
            update,
        )

    def reject(self, entry_id: str, note: str | None = None) -> QueueEntry | None:
        """エントリーを拒否"""

        def update(entry: QueueEntry) -> None:
            entry.reviewed_at = datetime.now()
            entry.review_note = note

        return self.move(
            entry_id,
            QueueStatus.PENDING,
            QueueStatus.REJECTED,
            update,
        )

    def mark_posted(self, entry_id: str, event_id: str | None = None) -> QueueEntry | None:
        """エントリーを投稿済みにする"""

        def update(entry: QueueEntry) -> None:
            entry.posted_at = datetime.now()
            entry.event_id = event_id

        return self.move(
            entry_id,
            QueueStatus.APPROVED,
            QueueStatus.POSTED,
            update,
        )

    def count(self, status: QueueStatus) -> int:
        """指定ステータスのエントリー数を取得"""
        return len(self._load_file(status))

    def summary(self) -> dict[str, int]:
        """全ステータスの件数サマリー"""
        return {status.value: self.count(status) for status in QueueStatus}
