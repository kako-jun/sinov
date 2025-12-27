"""
review コマンド - エントリーをレビュー（approve/reject）
"""

import argparse

from ...domain import QueueStatus
from ...infrastructure import QueueRepository
from ..base import init_env
from .queue import cmd_queue


def _handle_dry_run(queue_repo: QueueRepository, entry_id: str, action: str) -> None:
    """dry runモードでのチェック"""
    result = queue_repo.get_by_id(entry_id)
    if result is None:
        print(f"Entry not found: {entry_id}")
        return

    entry, status = result
    if status != QueueStatus.PENDING:
        print(f"⚠️  Entry is not pending (current: {status.value})")
        return

    icon = "✅" if action == "approve" else "❌"
    print(f"{icon} [DRY RUN] Would {action}: {entry.npc_name}")
    if action == "approve":
        print(f"    {entry.content[:60]}...")


def _handle_approve(queue_repo: QueueRepository, entry_id: str, note: str | None) -> None:
    """承認処理"""
    approved = queue_repo.approve(entry_id, note)
    if approved:
        print(f"✅ Approved: [{approved.id}] {approved.npc_name}")
    else:
        print(f"Entry not found in pending: {entry_id}")


def _handle_reject(queue_repo: QueueRepository, entry_id: str, note: str | None) -> None:
    """却下処理"""
    rejected = queue_repo.reject(entry_id, note)
    if rejected:
        print(f"❌ Rejected: [{rejected.id}] {rejected.npc_name}")
    else:
        print(f"Entry not found in pending: {entry_id}")


def cmd_review(args: argparse.Namespace) -> None:
    """エントリーをレビュー（approve/reject）"""
    settings = init_env()
    queue_repo = QueueRepository(settings.queue_dir)

    if args.action == "list":
        args.status = "pending"
        args.summary = False
        cmd_queue(args)
        return

    if args.dry_run:
        _handle_dry_run(queue_repo, args.id, args.action)
        return

    if args.action == "approve":
        _handle_approve(queue_repo, args.id, args.note)
    elif args.action == "reject":
        _handle_reject(queue_repo, args.id, args.note)
