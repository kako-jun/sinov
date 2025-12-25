#!/usr/bin/env python
"""
投稿削除スクリプト

使い方:
  # 最近の投稿を確認
  python scripts/delete_posts.py list

  # 特定の投稿を削除
  python scripts/delete_posts.py delete <event_id>

  # 特定ボットの全投稿を削除
  python scripts/delete_posts.py delete-all --bot bot001

  # 全ボットの全投稿を削除（危険）
  python scripts/delete_posts.py delete-all --confirm
"""

import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv


def load_posted_entries() -> list[dict]:
    """posted.jsonから投稿済みエントリーを読み込む"""
    posted_file = Path("bots/data/queue/posted.json")
    if not posted_file.exists():
        return []

    with open(posted_file) as f:
        return json.load(f)


def save_posted_entries(entries: list[dict]) -> None:
    """posted.jsonを保存"""
    posted_file = Path("bots/data/queue/posted.json")
    with open(posted_file, "w") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)


async def delete_event(event_id: str, bot_id: int) -> bool:
    """Nostrイベントを削除（kind:5）"""
    import httpx
    from nostr_sdk import EventBuilder, Keys, Kind, Tag

    from src.domain import BotKey

    load_dotenv()
    load_dotenv(".env.keys")

    try:
        bot_key = BotKey.from_env(bot_id)
        keys = Keys.parse(bot_key.nsec)
    except ValueError as e:
        print(f"  ❌ 鍵取得エラー: {e}")
        return False

    # kind:5 削除イベントを作成
    tags = [Tag.parse(["e", event_id])]
    event = EventBuilder(Kind(5), "").tags(tags).sign_with_keys(keys)

    # MYPACE APIに送信
    import os
    api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")

    event_json = json.loads(event.as_json())

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                f"{api_endpoint}/api/publish",
                json={"event": event_json},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return True

            print(f"  ⚠️  API応答: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ 送信エラー: {e}")
        return False


def cmd_list(args: argparse.Namespace) -> None:
    """投稿済みエントリーを一覧表示"""
    entries = load_posted_entries()

    if not entries:
        print("投稿済みエントリーはありません")
        return

    # フィルタ
    if args.bot:
        bot_id = int(args.bot.replace("bot", ""))
        entries = [e for e in entries if e.get("bot_id") == bot_id]

    # 最新N件
    entries = entries[-args.limit:]

    print(f"\n📋 投稿済み ({len(entries)}件):\n")
    for entry in entries:
        event_id = entry.get("event_id", "???")[:16]
        bot_name = entry.get("bot_name", "???")
        content = entry.get("content", "")[:40]
        posted_at = entry.get("posted_at", "???")[:16]

        print(f"[{event_id}...] {bot_name} ({posted_at})")
        print(f"    {content}...")
        print()


def cmd_delete(args: argparse.Namespace) -> None:
    """特定の投稿を削除"""
    entries = load_posted_entries()

    # event_idで検索
    target = None
    for entry in entries:
        if entry.get("event_id", "").startswith(args.event_id):
            target = entry
            break

    if not target:
        print(f"❌ イベントが見つかりません: {args.event_id}")
        return

    print(f"削除対象:")
    print(f"  ボット: {target.get('bot_name')}")
    print(f"  内容: {target.get('content', '')[:60]}...")
    print(f"  event_id: {target.get('event_id')}")
    print()

    if not args.yes:
        confirm = input("削除しますか？ [y/N]: ")
        if confirm.lower() != "y":
            print("キャンセルしました")
            return

    # 削除実行
    success = asyncio.run(delete_event(
        target["event_id"],
        target["bot_id"]
    ))

    if success:
        # posted.jsonから削除
        entries = [e for e in entries if e.get("event_id") != target["event_id"]]
        save_posted_entries(entries)
        print("✅ 削除しました")
    else:
        print("❌ 削除に失敗しました")


def cmd_delete_all(args: argparse.Namespace) -> None:
    """複数の投稿を一括削除"""
    entries = load_posted_entries()

    if args.bot:
        bot_id = int(args.bot.replace("bot", ""))
        targets = [e for e in entries if e.get("bot_id") == bot_id]
        print(f"削除対象: {args.bot} の {len(targets)}件")
    else:
        targets = entries
        print(f"削除対象: 全 {len(targets)}件")

    if not targets:
        print("削除対象がありません")
        return

    if not args.confirm:
        print("\n⚠️  --confirm オプションを付けて実行してください")
        print("例: python scripts/delete_posts.py delete-all --bot bot001 --confirm")
        return

    # 削除実行
    deleted = 0
    for target in targets:
        event_id = target.get("event_id")
        if not event_id:
            continue

        print(f"  削除中: {event_id[:16]}... ", end="")
        success = asyncio.run(delete_event(event_id, target["bot_id"]))

        if success:
            deleted += 1
            print("✅")
        else:
            print("❌")

    # posted.jsonを更新
    if args.bot:
        remaining = [e for e in entries if e.get("bot_id") != bot_id]
    else:
        remaining = []

    save_posted_entries(remaining)
    print(f"\n✅ {deleted}/{len(targets)}件 削除完了")


def main() -> None:
    parser = argparse.ArgumentParser(description="投稿削除ツール")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # list
    list_parser = subparsers.add_parser("list", help="投稿済み一覧")
    list_parser.add_argument("--bot", "-b", help="ボットでフィルタ (bot001)")
    list_parser.add_argument("--limit", "-n", type=int, default=20, help="表示件数")

    # delete
    del_parser = subparsers.add_parser("delete", help="投稿を削除")
    del_parser.add_argument("event_id", help="イベントID（前方一致）")
    del_parser.add_argument("--yes", "-y", action="store_true", help="確認をスキップ")

    # delete-all
    delall_parser = subparsers.add_parser("delete-all", help="一括削除")
    delall_parser.add_argument("--bot", "-b", help="ボットでフィルタ (bot001)")
    delall_parser.add_argument("--confirm", action="store_true", help="実行確認")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "delete-all":
        cmd_delete_all(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
