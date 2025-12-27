"""
活動ログ（日報）のドメインモデル

キャラクターの活動を記録し、後から人間が確認できるようにする。
キャラ自身はこのログを入力として使用しない。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


def _truncate(text: str, max_len: int) -> str:
    """テキストを指定長で切り詰め"""
    return text[:max_len] + "..." if len(text) > max_len else text


class LogEventType(Enum):
    """ログイベントの種類"""

    POST_GENERATE = "post_generate"  # 投稿生成
    POST_REVIEW = "post_review"  # レビュー結果
    POST_PUBLISHED = "post_published"  # 投稿完了
    REPLY_RECEIVED = "reply_received"  # リプライ受信
    REPLY_SENT = "reply_sent"  # リプライ送信
    REACTION_RECEIVED = "reaction_received"  # リアクション受信
    REACTION_SENT = "reaction_sent"  # リアクション送信
    AFFINITY_CHANGE = "affinity_change"  # 好感度変化
    MOOD_CHANGE = "mood_change"  # 気分変化
    MEMORY_CHANGE = "memory_change"  # 記憶変化
    SERIES_START = "series_start"  # 連作開始
    SERIES_END = "series_end"  # 連作完了
    EXTERNAL_REACTION = "external_reaction"  # 外部ユーザーへの反応


@dataclass
class ParameterChange:
    """パラメータ変化の記録"""

    name: str  # パラメータ名（affinity, mood, memory.strengthなど）
    old_value: float
    new_value: float
    reason: str  # 変化理由（「bot005からリプライを受けた」など）
    target: str | None = None  # 対象（他NPC IDなど）


@dataclass
class LogEntry:
    """1つのログエントリー"""

    timestamp: datetime
    event_type: LogEventType
    summary: str  # 人間が読める要約（1行）
    details: dict[str, Any] = field(default_factory=dict)  # 詳細情報
    parameter_changes: list[ParameterChange] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Markdown形式に変換"""
        lines = []
        time_str = self.timestamp.strftime("%H:%M:%S")
        event_label = self._get_event_label()

        lines.append(f"## {time_str} {event_label}")
        lines.append("")

        # 詳細情報
        for key, value in self.details.items():
            label = self._get_detail_label(key)
            # プロンプトは省略せずに出力
            lines.append(f"- **{label}**: {value}")

        # パラメータ変化
        for change in self.parameter_changes:
            target_str = f" ({change.target})" if change.target else ""
            lines.append(
                f"- **{change.name}変化**{target_str}: "
                f"{change.old_value:.2f} → {change.new_value:.2f} ({change.reason})"
            )

        lines.append("")
        return "\n".join(lines)

    def _get_event_label(self) -> str:
        """イベントタイプの日本語ラベル"""
        labels = {
            LogEventType.POST_GENERATE: "投稿生成",
            LogEventType.POST_REVIEW: "レビュー",
            LogEventType.POST_PUBLISHED: "投稿完了",
            LogEventType.REPLY_RECEIVED: "リプライ受信",
            LogEventType.REPLY_SENT: "リプライ送信",
            LogEventType.REACTION_RECEIVED: "リアクション受信",
            LogEventType.REACTION_SENT: "リアクション送信",
            LogEventType.AFFINITY_CHANGE: "好感度変化",
            LogEventType.MOOD_CHANGE: "気分変化",
            LogEventType.MEMORY_CHANGE: "記憶変化",
            LogEventType.SERIES_START: "連作開始",
            LogEventType.SERIES_END: "連作完了",
        }
        return labels.get(self.event_type, self.event_type.value)

    def _get_detail_label(self, key: str) -> str:
        """詳細キーの日本語ラベル"""
        labels = {
            "prompt": "プロンプト",
            "content": "内容",
            "generated_content": "生成内容",
            "status": "ステータス",
            "event_id": "イベントID",
            "sender": "送信者",
            "recipient": "宛先",
            "reason": "理由",
            "result": "結果",
            "theme": "テーマ",
            "total_posts": "予定投稿数",
            "relationship": "関係",
        }
        return labels.get(key, key)


@dataclass
class DailyLog:
    """1日分のログ"""

    npc_id: int
    date: datetime
    entries: list[LogEntry] = field(default_factory=list)

    def add_entry(self, entry: LogEntry) -> None:
        """エントリーを追加"""
        self.entries.append(entry)

    def to_markdown(self) -> str:
        """Markdown形式に変換"""
        lines = []
        npc_name = f"npc{self.npc_id:03d}"
        date_str = self.date.strftime("%Y-%m-%d")

        lines.append(f"# {npc_name} 活動ログ - {date_str}")
        lines.append("")

        if not self.entries:
            lines.append("*この日の活動はありません*")
            lines.append("")
        else:
            # 時系列でソート
            sorted_entries = sorted(self.entries, key=lambda e: e.timestamp)
            for entry in sorted_entries:
                lines.append(entry.to_markdown())

        return "\n".join(lines)


class ActivityLogger:
    """活動ログを記録するヘルパークラス"""

    @staticmethod
    def log_post_generate(
        content: str,
        prompt_summary: str,
        series_info: str | None = None,
    ) -> LogEntry:
        """投稿生成をログ"""
        details = {
            "prompt": prompt_summary,
            "generated_content": content,
            "status": "pending",
        }
        if series_info:
            details["series"] = series_info

        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.POST_GENERATE,
            summary=f"投稿を生成: {content[:30]}...",
            details=details,
        )

    @staticmethod
    def log_review(
        content: str,
        approved: bool,
        reason: str | None = None,
    ) -> LogEntry:
        """レビュー結果をログ"""
        result = "approved" if approved else "rejected"
        details = {
            "content": content,
            "result": result,
        }
        if reason:
            details["reason"] = reason

        summary = f"レビュー: {result}"
        if reason:
            summary += f" - {reason[:30]}"

        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.POST_REVIEW,
            summary=summary,
            details=details,
        )

    @staticmethod
    def log_post_published(
        content: str,
        event_id: str,
    ) -> LogEntry:
        """投稿完了をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.POST_PUBLISHED,
            summary=f"投稿完了: {content[:30]}...",
            details={
                "content": content,
                "event_id": event_id,
            },
        )

    @staticmethod
    def log_reply_received(
        sender: str,
        content: str,
        relationship: str | None = None,
        parameter_changes: list[ParameterChange] | None = None,
    ) -> LogEntry:
        """リプライ受信をログ"""
        details = {
            "sender": sender,
            "content": content,
        }
        if relationship:
            details["relationship"] = relationship

        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.REPLY_RECEIVED,
            summary=f"{sender}からリプライ: {content[:20]}...",
            details=details,
            parameter_changes=parameter_changes or [],
        )

    @staticmethod
    def log_reply_sent(
        recipient: str,
        content: str,
        relationship: str | None = None,
        parameter_changes: list[ParameterChange] | None = None,
    ) -> LogEntry:
        """リプライ送信をログ"""
        details = {
            "recipient": recipient,
            "content": content,
        }
        if relationship:
            details["relationship"] = relationship

        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.REPLY_SENT,
            summary=f"{recipient}へリプライ: {content[:20]}...",
            details=details,
            parameter_changes=parameter_changes or [],
        )

    @staticmethod
    def log_affinity_decay(
        target: str,
        old_value: float,
        new_value: float,
        reason: str,
    ) -> LogEntry:
        """好感度減衰をログ"""
        change = ParameterChange(
            name="好感度",
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            target=target,
        )
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.AFFINITY_CHANGE,
            summary=f"{target}への好感度減衰: {reason}",
            details={},
            parameter_changes=[change],
        )

    @staticmethod
    def log_series_start(theme: str, total_posts: int) -> LogEntry:
        """連作開始をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.SERIES_START,
            summary=f"連作開始: 「{theme}」({total_posts}投稿)",
            details={
                "theme": theme,
                "total_posts": total_posts,
            },
        )

    @staticmethod
    def log_series_end(theme: str) -> LogEntry:
        """連作完了をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.SERIES_END,
            summary=f"連作完了: 「{theme}」",
            details={
                "theme": theme,
            },
        )

    @staticmethod
    def log_reaction_received(
        sender: str,
        emoji: str,
        target_content: str,
        parameter_changes: list[ParameterChange] | None = None,
    ) -> LogEntry:
        """リアクション受信をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.REACTION_RECEIVED,
            summary=f"{sender}からリアクション: {emoji}",
            details={
                "sender": sender,
                "emoji": emoji,
                "target_content": _truncate(target_content, 50),
            },
            parameter_changes=parameter_changes or [],
        )

    @staticmethod
    def log_reaction_sent(
        recipient: str,
        emoji: str,
        target_content: str,
    ) -> LogEntry:
        """リアクション送信をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.REACTION_SENT,
            summary=f"{recipient}へリアクション: {emoji}",
            details={
                "recipient": recipient,
                "emoji": emoji,
                "target_content": _truncate(target_content, 50),
            },
        )

    @staticmethod
    def log_external_reaction(
        reaction_type: str,
        target: str,
        content: str,
    ) -> LogEntry:
        """外部ユーザーへの反応をログ"""
        return LogEntry(
            timestamp=datetime.now(),
            event_type=LogEventType.EXTERNAL_REACTION,
            summary=f"外部ユーザー({target})へ{reaction_type}: {content[:30]}...",
            details={
                "reaction_type": reaction_type,
                "target": target,
                "content": content,
            },
        )
