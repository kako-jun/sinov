"""
CLIツール - NPC投稿管理（メインエントリーポイント）
"""

import argparse
import asyncio

from .commands import cmd_generate, cmd_post, cmd_queue, cmd_review, cmd_tick


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinov NPC CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # generate コマンド
    gen_parser = subparsers.add_parser("generate", help="Generate posts to queue")
    gen_parser.add_argument("--all", "-a", action="store_true", help="All NPCs")
    gen_parser.add_argument("--npc", type=str, help="NPC name (e.g., npc001)")
    gen_parser.add_argument("--dry-run", "-d", action="store_true", help="Save to dry_run.json")

    # queue コマンド
    queue_parser = subparsers.add_parser("queue", help="Show queue status")
    queue_parser.add_argument(
        "--status", "-s", type=str, help="Filter by status (pending/approved/...)"
    )
    queue_parser.add_argument("--summary", action="store_true", help="Show summary only")

    # review コマンド
    review_parser = subparsers.add_parser("review", help="Review entries")
    review_parser.add_argument("action", choices=["approve", "reject", "list"], help="Action")
    review_parser.add_argument("id", nargs="?", help="Entry ID")
    review_parser.add_argument("--note", "-m", type=str, help="Review note")
    review_parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Check only, don't move"
    )

    # post コマンド
    post_parser = subparsers.add_parser("post", help="Post approved entries")
    post_parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Show what would be posted"
    )

    # tick コマンド
    tick_parser = subparsers.add_parser("tick", help="Run one tick: process N residents + reviewer")
    tick_parser.add_argument(
        "--count", "-c", type=int, default=10, help="Number of NPCs to process (default: 10)"
    )

    # 旧 preview コマンド（後方互換）
    preview_parser = subparsers.add_parser(
        "preview", help="(Legacy) Preview posts - use 'generate --dry-run' instead"
    )
    preview_parser.add_argument("--all", "-a", action="store_true")
    preview_parser.add_argument("--bot", "-b", type=str)
    preview_parser.add_argument("--output", "-o", type=str)

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(cmd_generate(args))
    elif args.command == "queue":
        cmd_queue(args)
    elif args.command == "review":
        if args.action in ["approve", "reject"] and not args.id:
            print("Error: ID required for approve/reject")
            return
        cmd_review(args)
    elif args.command == "post":
        asyncio.run(cmd_post(args))
    elif args.command == "tick":
        asyncio.run(cmd_tick(args))
    elif args.command == "preview":
        # 後方互換: generate --dry-run にリダイレクト
        args.dry_run = True
        asyncio.run(cmd_generate(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
