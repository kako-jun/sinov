"""
generate コマンド - 投稿を生成してキューに追加
"""

import argparse

from ...domain import QueueEntry, QueueStatus, extract_bot_id
from ...infrastructure import QueueRepository
from ..base import init_env, init_llm, init_service


async def cmd_generate(args: argparse.Namespace) -> None:
    """投稿を生成してキューに追加"""
    settings = init_env()
    llm = init_llm(settings)
    if not llm:
        return

    service = await init_service(settings, llm)
    queue_repo = QueueRepository(settings.queue_dir)

    # dry_run の場合は dry_run.json に追加
    target_status = QueueStatus.DRY_RUN if args.dry_run else QueueStatus.PENDING

    # 対象NPCを決定
    if args.all:
        bot_ids = list(service.bots.keys())
    elif args.bot:
        bot_id = extract_bot_id(args.bot)
        if bot_id is None or bot_id not in service.bots:
            print(f"Bot not found: {args.bot}")
            return
        bot_ids = [bot_id]
    else:
        print("Specify --all or --bot <name>")
        return

    print(f"\nGenerating posts ({target_status.value})...")
    generated = 0

    for bot_id in bot_ids:
        _, profile, _ = service.bots[bot_id]
        try:
            content = await service.generate_post_content(bot_id)

            entry = QueueEntry(
                bot_id=bot_id,
                bot_name=profile.name,
                content=content,
                status=target_status,
            )
            queue_repo.add(entry)

            print(f"  [{entry.id}] {profile.name}: {content[:40]}...")
            generated += 1
        except Exception as e:
            print(f"  ⚠️  {profile.name}: {e}")

    print(f"\n✅ Generated {generated} posts → {target_status.value}.json")
