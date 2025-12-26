"""
review コマンド - エントリーをレビュー（approve/reject）
"""

import argparse

from ...domain import QueueStatus
from ...infrastructure import QueueRepository
from ..base import init_env
from .queue import cmd_queue


def cmd_review(args: argparse.Namespace) -> None:
    """エントリーをレビュー（approve/reject）"""
    settings = init_env()
    queue_repo = QueueRepository(settings.queue_dir)

    if args.action == "approve":
        if args.dry_run:
            # dry run: 移動せずチェックのみ
            result = queue_repo.get_by_id(args.id)
            if result is None:
                print(f"Entry not found: {args.id}")
                return
            entry, status = result
            if status != QueueStatus.PENDING:
                print(f"⚠️  Entry is not pending (current: {status.value})")
            else:
                print(f"✅ [DRY RUN] Would approve: {entry.npc_name}")
                print(f"    {entry.content[:60]}...")
        else:
            approved = queue_repo.approve(args.id, args.note)
            if approved:
                print(f"✅ Approved: [{approved.id}] {approved.npc_name}")
            else:
                print(f"Entry not found in pending: {args.id}")

    elif args.action == "reject":
        if args.dry_run:
            result = queue_repo.get_by_id(args.id)
            if result is None:
                print(f"Entry not found: {args.id}")
                return
            entry, status = result
            if status != QueueStatus.PENDING:
                print(f"⚠️  Entry is not pending (current: {status.value})")
            else:
                print(f"❌ [DRY RUN] Would reject: {entry.npc_name}")
        else:
            rejected = queue_repo.reject(args.id, args.note)
            if rejected:
                print(f"❌ Rejected: [{rejected.id}] {rejected.npc_name}")
            else:
                print(f"Entry not found in pending: {args.id}")

    elif args.action == "list":
        # pending のリスト（queue list のエイリアス）
        args.status = "pending"
        args.summary = False
        cmd_queue(args)
