"""
tick コマンド - 1周の処理: 住人N人を順番に処理 + 相互作用 + 最後にレビューア
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from ...application import NpcService, ServiceFactory
from ...domain import QueueEntry, QueueStatus
from ..base import init_env, init_llm

if TYPE_CHECKING:
    from ...infrastructure import QueueRepository


async def cmd_tick(args: argparse.Namespace) -> None:
    """1周の処理: 住人N人を順番に処理 + 相互作用 + 最後にレビューア"""
    settings = init_env()
    llm = init_llm(settings)
    if not llm:
        return

    # ServiceFactoryを使ってサービスを構築
    factory = ServiceFactory(settings, llm)
    service = await factory.create_npc_service()

    # 対象NPCの一覧を取得（IDでソート）
    all_npc_ids = sorted(service.npcs.keys())
    total_bots = len(all_npc_ids)

    if total_bots == 0:
        print("No NPCs found")
        return

    # レビューア枠を除いた住人数を計算
    # count=10 なら 住人9人 + レビューア1回
    resident_count = max(1, args.count - 1)

    # ラウンドロビンで対象範囲を取得
    start_idx, end_idx = factory.tick_state_repo.advance(resident_count, total_bots)

    # 対象の住人を取得
    target_ids = all_npc_ids[start_idx:end_idx]

    # 端で折り返す場合
    if end_idx <= start_idx and start_idx < total_bots:
        target_ids = all_npc_ids[start_idx:]

    tick_state = factory.tick_state_repo.load()
    print(f"\n🔄 Tick #{tick_state.total_ticks}")
    idx_range = f"{start_idx}-{end_idx - 1}"
    print(f"   Processing {len(target_ids)} residents (index {idx_range} of {total_bots})")

    # --- 住人の処理（順番に） ---
    generated = 0
    for npc_id in target_ids:
        _, profile, _ = service.npcs[npc_id]
        try:
            content = await service.generate_post_content(npc_id)

            entry = QueueEntry(
                npc_id=npc_id,
                npc_name=profile.name,
                content=content,
                status=QueueStatus.PENDING,
            )
            factory.queue_repo.add(entry)

            print(f"   ✏️  {profile.name}: {content[:40]}...")
            generated += 1
        except Exception as e:
            print(f"   ⚠️  {profile.name}: {e}")

    # --- 相互作用処理 ---
    print("\n   💬 Processing interactions...")
    interaction_service = factory.create_interaction_service(service)
    interactions = await interaction_service.process_interactions(target_ids)
    chain_replies = await interaction_service.process_reply_chains(target_ids)
    total_interactions = interactions + chain_replies

    # --- 外部ユーザーへの反応処理 ---
    print("\n   🌐 Processing external reactions...")
    external_service = factory.create_external_reaction_service(service)
    external_reactions = await external_service.process_external_reactions(
        target_npc_ids=target_ids,
        max_posts_per_bot=1,  # 控えめに1人1投稿まで
    )
    if external_reactions > 0:
        print(f"   🌐 External reactions: {external_reactions}")

    # --- 好感度減衰処理 ---
    decay_count = interaction_service.process_affinity_decay(target_ids)
    ignored_count = interaction_service.process_ignored_posts(target_ids)
    if decay_count > 0 or ignored_count > 0:
        print(f"   📉 Affinity decay: {decay_count} (distant), {ignored_count} (ignored)")

    # --- レビューア処理 ---
    print("\n   📋 Running reviewer...")
    reviewed = await run_reviewer(service, factory.queue_repo)

    print(
        f"\n✅ Tick complete: {generated} generated, {total_interactions} interactions, "
        f"{external_reactions} external, {reviewed} reviewed"
    )


REVIEWER_NPC_ID = 101  # レビューアのNPC ID


async def run_reviewer(service: NpcService, queue_repo: QueueRepository) -> int:
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
                print(f"      ✅ {entry.npc_name}")
            else:
                queue_repo.reject(entry.id, reason)
                print(f"      ❌ {entry.npc_name}: {reason}")

            # 投稿者のログに記録
            service.log_review(entry.npc_id, entry.content, is_approved, reason)

            # レビューアの日報にも記録（rejectのみ）
            if not is_approved:
                service.log_review(REVIEWER_NPC_ID, entry.content, is_approved, reason)

            reviewed += 1
        except Exception as e:
            print(f"      ⚠️  {entry.npc_name}: {e}")

    return reviewed
