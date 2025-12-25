"""
queue コマンド - キューの状態を表示
"""

import argparse

from ...domain import QueueStatus
from ...infrastructure import QueueRepository
from ..base import init_env


def cmd_queue(args: argparse.Namespace) -> None:
    """キューの状態を表示"""
    settings = init_env()
    queue_repo = QueueRepository(settings.queue_dir)

    if args.summary:
        # サマリー表示
        summary = queue_repo.summary()
        print("\n📊 Queue Summary:")
        for status, count in summary.items():
            print(f"  {status}: {count}")
        return

    # 特定ステータスのリスト表示
    try:
        status = QueueStatus(args.status) if args.status else QueueStatus.PENDING
    except ValueError:
        print(f"Invalid status: {args.status}")
        print(f"Valid: {', '.join(s.value for s in QueueStatus)}")
        return

    entries = queue_repo.get_all(status)

    if not entries:
        print(f"\n{status.value}.json is empty")
        return

    print(f"\n📋 {status.value}.json ({len(entries)} entries):\n")
    for entry in entries:
        created = entry.created_at.strftime("%m/%d %H:%M")
        print(f"[{entry.id}] {entry.bot_name} ({created})")
        print(f"    {entry.content[:60]}...")
        if entry.review_note:
            print(f"    📝 {entry.review_note}")
        print()
