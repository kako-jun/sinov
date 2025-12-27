"""
post コマンド - approvedのエントリーを投稿
"""

import argparse
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from nostr_sdk import Keys

from ...domain import NpcKey, PostType, QueueEntry, QueueStatus
from ...infrastructure import NostrPublisher, QueueRepository
from ..base import get_target_pubkey, init_env

if TYPE_CHECKING:
    pass


def _get_target_pubkey_for_entry(entry: QueueEntry) -> str | None:
    """エントリーから対象のpubkeyを取得"""
    if not entry.reply_to:
        return None
    if entry.reply_to.resident.startswith("external:"):
        return entry.reply_to.pubkey
    return get_target_pubkey(entry.reply_to.resident)


async def _post_reply(
    publisher: NostrPublisher,
    keys: Keys,
    entry: QueueEntry,
    target_pubkey: str,
) -> str | None:
    """リプライを投稿"""
    if not entry.reply_to:
        return None
    event_id = await publisher.publish_reply(
        keys=keys,
        content=entry.content,
        npc_name=entry.npc_name,
        reply_to_event_id=entry.reply_to.event_id,
        reply_to_pubkey=target_pubkey,
    )
    print(f"  💬 {entry.npc_name}: {entry.content[:40]}... → {entry.reply_to.resident}")
    return event_id


async def _post_reaction(
    publisher: NostrPublisher,
    keys: Keys,
    entry: QueueEntry,
    target_pubkey: str,
) -> str | None:
    """リアクションを投稿"""
    if not entry.reply_to:
        return None
    event_id = await publisher.publish_reaction(
        keys=keys,
        emoji=entry.content,
        npc_name=entry.npc_name,
        target_event_id=entry.reply_to.event_id,
        target_pubkey=target_pubkey,
    )
    print(f"  ❤️  {entry.npc_name}: {entry.content} → {entry.reply_to.resident}")
    return event_id


async def _post_normal(
    publisher: NostrPublisher,
    keys: Keys,
    entry: QueueEntry,
) -> str | None:
    """通常投稿"""
    event_id = await publisher.publish(keys, entry.content, entry.npc_name)
    print(f"  ✅ {entry.npc_name}: {entry.content[:40]}...")
    return event_id


async def _post_entry(
    publisher: NostrPublisher,
    entry: QueueEntry,
) -> str | None:
    """エントリーを投稿"""
    npc_key = NpcKey.from_env(entry.npc_id)
    keys = Keys.parse(npc_key.nsec)

    if entry.post_type == PostType.REPLY and entry.reply_to:
        target_pubkey = _get_target_pubkey_for_entry(entry)
        if not target_pubkey:
            print(f"  ⏭️  {entry.npc_name}: Reply skipped (pubkey not found)")
            return None
        return await _post_reply(publisher, keys, entry, target_pubkey)

    if entry.post_type == PostType.REACTION and entry.reply_to:
        target_pubkey = _get_target_pubkey_for_entry(entry)
        if not target_pubkey:
            print(f"  ⏭️  {entry.npc_name}: Reaction skipped (pubkey not found)")
            return None
        return await _post_reaction(publisher, keys, entry, target_pubkey)

    return await _post_normal(publisher, keys, entry)


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

    load_dotenv(".env.keys")
    publisher = NostrPublisher(settings.api_endpoint, dry_run=False)

    print(f"\n📤 Posting {len(entries)} entries...\n")
    posted = 0

    for entry in entries:
        try:
            event_id = await _post_entry(publisher, entry)
            if event_id:
                queue_repo.mark_posted(entry.id, event_id)
                posted += 1
        except Exception as e:
            print(f"  ❌ {entry.npc_name}: {e}")

    print(f"\n✅ Posted {posted}/{len(entries)} entries")
