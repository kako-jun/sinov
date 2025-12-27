"""
generate コマンド - 投稿を生成してキューに追加
"""

import argparse

from ...application import ServiceFactory
from ...domain import QueueEntry, QueueStatus, extract_npc_id
from ..base import init_env, init_llm


async def cmd_generate(args: argparse.Namespace) -> None:
    """投稿を生成してキューに追加"""
    settings = init_env()
    llm = init_llm(settings)
    if not llm:
        return

    # ServiceFactoryを使ってサービスを構築
    factory = ServiceFactory(settings, llm)
    service = await factory.create_npc_service()

    # dry_run の場合は dry_run.json に追加
    target_status = QueueStatus.DRY_RUN if args.dry_run else QueueStatus.PENDING

    # 対象NPCを決定
    if args.all:
        npc_ids = list(service.npcs.keys())
    elif args.npc:
        npc_id = extract_npc_id(args.npc)
        if npc_id is None or npc_id not in service.npcs:
            print(f"NPC not found: {args.npc}")
            return
        npc_ids = [npc_id]
    else:
        print("Specify --all or --npc <name>")
        return

    print(f"\nGenerating posts ({target_status.value})...")
    generated = 0

    for npc_id in npc_ids:
        _, profile, _ = service.npcs[npc_id]
        try:
            content = await service.generate_post_content(npc_id)

            entry = QueueEntry(
                npc_id=npc_id,
                npc_name=profile.name,
                content=content,
                status=target_status,
            )
            factory.queue_repo.add(entry)

            print(f"  [{entry.id}] {profile.name}: {content[:40]}...")
            generated += 1
        except Exception as e:
            print(f"  ⚠️  {profile.name}: {e}")

    print(f"\n✅ Generated {generated} posts → {target_status.value}.json")
