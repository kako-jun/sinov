"""
活動ログリポジトリ

住人ごとの活動ログをMarkdownファイルとして保存・管理する。
7日分のログを保持し、古いログは自動削除する。
"""

from datetime import datetime, timedelta
from pathlib import Path

from ...domain import DailyLog, LogEntry


class LogRepository:
    """活動ログリポジトリ"""

    RETENTION_DAYS = 7  # ログ保持日数

    def __init__(self, residents_dir: str):
        self.residents_dir = Path(residents_dir)

    def _get_log_dir(self, npc_id: int) -> Path:
        """ログディレクトリのパスを取得"""
        npc_name = f"npc{npc_id:03d}"
        return self.residents_dir / npc_name / "logs"

    def _get_log_path(self, npc_id: int, date: datetime) -> Path:
        """ログファイルのパスを取得"""
        date_str = date.strftime("%Y-%m-%d")
        return self._get_log_dir(npc_id) / f"{date_str}.md"

    def _ensure_log_dir(self, npc_id: int) -> None:
        """ログディレクトリを作成"""
        log_dir = self._get_log_dir(npc_id)
        log_dir.mkdir(parents=True, exist_ok=True)

    def add_entry(self, npc_id: int, entry: LogEntry) -> None:
        """ログエントリーを追加"""
        self._ensure_log_dir(npc_id)
        today = datetime.now().date()
        log_path = self._get_log_path(npc_id, datetime.now())

        # 既存のログを読み込むか、新規作成
        if log_path.exists():
            # 既存ファイルに追記
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(entry.to_markdown())
        else:
            # 新規作成（ヘッダー付き）
            daily_log = DailyLog(
                npc_id=npc_id,
                date=datetime.combine(today, datetime.min.time()),
                entries=[entry],
            )
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(daily_log.to_markdown())

    def add_entries(self, npc_id: int, entries: list[LogEntry]) -> None:
        """複数のログエントリーを追加"""
        for entry in entries:
            self.add_entry(npc_id, entry)

    def get_daily_log(self, npc_id: int, date: datetime) -> DailyLog | None:
        """指定日のログを取得"""
        log_path = self._get_log_path(npc_id, date)
        if not log_path.exists():
            return None

        # Markdownファイルを読み込む（パースはしない、表示用）
        return DailyLog(
            npc_id=npc_id,
            date=date,
            entries=[],  # 既にMarkdownとして保存されているため空
        )

    def get_log_content(self, npc_id: int, date: datetime) -> str | None:
        """指定日のログ内容（Markdown）を取得"""
        log_path = self._get_log_path(npc_id, date)
        if not log_path.exists():
            return None

        with open(log_path, encoding="utf-8") as f:
            return f.read()

    def get_recent_logs(self, npc_id: int, days: int = 7) -> dict[str, str]:
        """直近N日分のログを取得

        Returns:
            日付文字列 -> ログ内容のマッピング
        """
        logs = {}
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            content = self.get_log_content(npc_id, date)
            if content:
                date_str = date.strftime("%Y-%m-%d")
                logs[date_str] = content

        return logs

    def cleanup_old_logs(self, npc_id: int) -> int:
        """古いログを削除

        Returns:
            削除したファイル数
        """
        log_dir = self._get_log_dir(npc_id)
        if not log_dir.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        deleted = 0

        for log_file in log_dir.glob("*.md"):
            try:
                # ファイル名から日付を抽出
                date_str = log_file.stem  # e.g., "2025-12-26"
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted += 1
            except ValueError:
                # 日付形式でないファイルは無視
                continue

        return deleted

    def cleanup_all_old_logs(self) -> int:
        """全住人の古いログを削除

        Returns:
            削除したファイル数
        """
        total_deleted = 0

        for bot_dir in self.residents_dir.iterdir():
            if not bot_dir.is_dir():
                continue

            # npc001形式のディレクトリのみ処理
            if not bot_dir.name.startswith("npc"):
                continue

            try:
                npc_id = int(bot_dir.name[3:])
                total_deleted += self.cleanup_old_logs(npc_id)
            except ValueError:
                continue

        return total_deleted

    def list_log_dates(self, npc_id: int) -> list[str]:
        """ログが存在する日付のリストを取得"""
        log_dir = self._get_log_dir(npc_id)
        if not log_dir.exists():
            return []

        dates = []
        for log_file in sorted(log_dir.glob("*.md"), reverse=True):
            dates.append(log_file.stem)

        return dates
