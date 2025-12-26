"""
post コマンド - approvedのエントリーを投稿
"""

import argparse

from dotenv import load_dotenv

from ...domain import NpcKey, PostType, QueueStatus
from ...infrastructure import NostrPublisher, QueueRepository
from ..base import get_target_pubkey, init_env


async def cmd_post(args: argparse.Namespace) -> None:
    """approvedのエントリーを投稿"""
    settings = init_env()
    queue_repo = QueueRepository(settings.queue_dir)

    entries = queue_repo.get_all(QueueStatus.APPROVED)

    if not entries:
        print("No approved entries to post")
        return

    if args.dry_run:
        print(f"\n🔍 [DRY RUN] Would post {len(entries)} entries:\n")
        for entry in entries:
            post_type = entry.post_type.value if entry.post_type else "normal"
            print(f"  [{entry.id}] {entry.npc_name} ({post_type}): {entry.content[:50]}...")
        return

    # 実投稿
    publisher = NostrPublisher(settings.api_endpoint, dry_run=False)

    # Nostr署名鍵を初期化
    load_dotenv(".env.keys")
    from nostr_sdk import Keys

    print(f"\n📤 Posting {len(entries)} entries...\n")
    posted = 0

    for entry in entries:
        try:
            # 鍵を取得
            npc_key = NpcKey.from_env(entry.npc_id)
            keys = Keys.parse(npc_key.nsec)

            event_id: str | None = None

            # 投稿タイプに応じて処理を分岐
            if entry.post_type == PostType.REPLY and entry.reply_to:
                # リプライ投稿
                # 外部ユーザーの場合はpubkeyを直接使用
                if entry.reply_to.resident.startswith("external:"):
                    target_pubkey = entry.reply_to.pubkey
                else:
                    target_pubkey = get_target_pubkey(entry.reply_to.resident)

                if not target_pubkey:
                    print(f"  ⏭️  {entry.npc_name}: Reply skipped (pubkey not found)")
                    continue

                event_id = await publisher.publish_reply(
                    keys=keys,
                    content=entry.content,
                    npc_name=entry.npc_name,
                    reply_to_event_id=entry.reply_to.event_id,
                    reply_to_pubkey=target_pubkey,
                )
                target_name = entry.reply_to.resident
                print(f"  💬 {entry.npc_name}: {entry.content[:40]}... → {target_name}")

            elif entry.post_type == PostType.REACTION and entry.reply_to:
                # リアクション投稿
                # 外部ユーザーの場合はpubkeyを直接使用
                if entry.reply_to.resident.startswith("external:"):
                    target_pubkey = entry.reply_to.pubkey
                else:
                    target_pubkey = get_target_pubkey(entry.reply_to.resident)

                if not target_pubkey:
                    print(f"  ⏭️  {entry.npc_name}: Reaction skipped (pubkey not found)")
                    continue

                event_id = await publisher.publish_reaction(
                    keys=keys,
                    emoji=entry.content,
                    npc_name=entry.npc_name,
                    target_event_id=entry.reply_to.event_id,
                    target_pubkey=target_pubkey,
                )
                print(f"  ❤️  {entry.npc_name}: {entry.content} → {entry.reply_to.resident}")

            else:
                # 通常投稿
                event_id = await publisher.publish(keys, entry.content, entry.npc_name)
                print(f"  ✅ {entry.npc_name}: {entry.content[:40]}...")

            # キューを更新
            queue_repo.mark_posted(entry.id, event_id)
            posted += 1

        except Exception as e:
            print(f"  ❌ {entry.npc_name}: {e}")

    print(f"\n✅ Posted {posted}/{len(entries)} entries")
