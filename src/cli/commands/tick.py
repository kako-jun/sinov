"""
tick コマンド - 1周の処理: 住人N人を順番に処理 + 相互作用 + 最後にレビューア
"""

import argparse

from ...application import BotService, InteractionService
from ...domain import QueueEntry, QueueStatus
from ...infrastructure import QueueRepository, RelationshipRepository, TickStateRepository
from ..base import init_env, init_llm, init_service


async def cmd_tick(args: argparse.Namespace) -> None:
    """1周の処理: 住人N人を順番に処理 + 相互作用 + 最後にレビューア"""
    settings = init_env()
    llm = init_llm(settings)
    if not llm:
        return

    service = await init_service(settings, llm)
    queue_repo = QueueRepository(settings.queue_dir)
    tick_state_repo = TickStateRepository(settings.tick_state_file)
    relationship_repo = RelationshipRepository(settings.relationships_dir)

    # 対象ボットの一覧を取得（IDでソート）
    all_bot_ids = sorted(service.bots.keys())
    total_bots = len(all_bot_ids)

    if total_bots == 0:
        print("No bots found")
        return

    # レビューア枠を除いた住人数を計算
    # count=10 なら 住人9人 + レビューア1回
    resident_count = max(1, args.count - 1)

    # ラウンドロビンで対象範囲を取得
    start_idx, end_idx = tick_state_repo.advance(resident_count, total_bots)

    # 対象の住人を取得
    target_ids = all_bot_ids[start_idx:end_idx]

    # 端で折り返す場合
    if end_idx <= start_idx and start_idx < total_bots:
        target_ids = all_bot_ids[start_idx:]

    tick_state = tick_state_repo.load()
    print(f"\n🔄 Tick #{tick_state.total_ticks}")
    print(
        f"   Processing {len(target_ids)} residents (index {start_idx}-{end_idx - 1} of {total_bots})"
    )

    # --- 住人の処理（順番に） ---
    generated = 0
    for bot_id in target_ids:
        _, profile, _ = service.bots[bot_id]
        try:
            content = await service.generate_post_content(bot_id)

            entry = QueueEntry(
                bot_id=bot_id,
                bot_name=profile.name,
                content=content,
                status=QueueStatus.PENDING,
            )
            queue_repo.add(entry)

            print(f"   ✏️  {profile.name}: {content[:40]}...")
            generated += 1
        except Exception as e:
            print(f"   ⚠️  {profile.name}: {e}")

    # --- 相互作用処理 ---
    print("\n   💬 Processing interactions...")
    interaction_service = InteractionService(
        llm_provider=llm,
        queue_repo=queue_repo,
        relationship_repo=relationship_repo,
        content_strategy=service.content_strategy,
        bots=service.bots,
        memory_repo=service.memory_repo,
        affinity_settings=settings.affinity,
        profile_repo=service.profile_repo,
        log_repo=service.log_repo,
    )
    interactions = await interaction_service.process_interactions(target_ids)
    chain_replies = await interaction_service.process_reply_chains(target_ids)
    total_interactions = interactions + chain_replies

    # --- 好感度減衰処理 ---
    decay_count = interaction_service.process_affinity_decay(target_ids)
    ignored_count = interaction_service.process_ignored_posts(target_ids)
    if decay_count > 0 or ignored_count > 0:
        print(f"   📉 Affinity decay: {decay_count} (distant), {ignored_count} (ignored)")

    # --- レビューア処理 ---
    print("\n   📋 Running reviewer...")
    reviewed = await run_reviewer(service, queue_repo)

    print(
        f"\n✅ Tick complete: {generated} generated, {total_interactions} interactions, {reviewed} reviewed"
    )


async def run_reviewer(service: BotService, queue_repo: QueueRepository) -> int:
    """pending のエントリーをレビュー（Gemmaを使用）"""
    pending_entries = queue_repo.get_all(QueueStatus.PENDING)

    if not pending_entries:
        print("      No pending entries")
        return 0

    reviewed = 0
    for entry in pending_entries:
        try:
            # LLMでレビュー
            is_approved, reason = await service.review_content(entry.content)

            if is_approved:
                queue_repo.approve(entry.id, reason)
                print(f"      ✅ {entry.bot_name}")
            else:
                queue_repo.reject(entry.id, reason)
                print(f"      ❌ {entry.bot_name}: {reason}")

            # ログ記録
            service.log_review(entry.bot_id, entry.content, is_approved, reason)

            reviewed += 1
        except Exception as e:
            print(f"      ⚠️  {entry.bot_name}: {e}")

    return reviewed
