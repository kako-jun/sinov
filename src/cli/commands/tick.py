"""
tick コマンド - 活動時刻のNPCを処理 + 相互作用 + レビュー + 投稿
"""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import TYPE_CHECKING

from ...application import NpcService, ServiceFactory
from ...domain import QueueEntry, QueueStatus, Scheduler
from ..base import init_env, init_llm

if TYPE_CHECKING:
    from ...infrastructure import QueueRepository

# キューの上限（これ以上たまったら生成しない）
MAX_APPROVED_QUEUE = 20


async def cmd_tick(args: argparse.Namespace) -> None:
    """活動時刻のNPCを処理 + 相互作用 + レビュー + 投稿"""
    settings = init_env()
    llm = init_llm(settings)
    if not llm:
        return

    # ServiceFactoryを使ってサービスを構築
    factory = ServiceFactory(settings, llm)
    service = await factory.create_npc_service()

    # approved キューの件数をチェック
    approved_count = len(factory.queue_repo.get_all(QueueStatus.APPROVED))
    if approved_count >= MAX_APPROVED_QUEUE:
        print(
            f"⏸️  Approved queue full ({approved_count}/{MAX_APPROVED_QUEUE}), skipping generation"
        )
        # 投稿処理だけ行う
        posted = await post_approved(service, factory)
        print(f"✅ Posted {posted} entries")
        return

    # 「今が活動時間」かつ「投稿すべき時刻」のNPCを選ぶ（通常投稿用）
    target_ids = []
    current_hour = datetime.now().hour
    for npc_id, (_, profile, state) in service.npcs.items():
        if Scheduler.should_post_now(profile, state):
            target_ids.append(npc_id)

    # 上限を設定（一度に処理しすぎない）
    max_generate = getattr(args, "count", 10)
    if len(target_ids) > max_generate:
        target_ids = target_ids[:max_generate]

    tick_state = factory.tick_state_repo.load()
    factory.tick_state_repo.advance(len(target_ids), len(service.npcs))  # カウンタ更新
    print(f"\n🔄 Tick #{tick_state.total_ticks + 1}")
    print(f"   {len(target_ids)} NPCs ready to post (hour: {current_hour}:00)")

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
    # リプライチェーンは全NPC対象（target_ids関係なく返信可能）
    chain_replies = await interaction_service.process_reply_chains()
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

    # --- 投稿処理（approved キューから投稿）---
    print("\n   📤 Posting approved entries...")
    posted = await post_approved(service, factory)

    print(
        f"\n✅ Tick complete: {generated} generated, {total_interactions} interactions, "
        f"{external_reactions} external, {reviewed} reviewed, {posted} posted"
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


async def post_approved(service: NpcService, factory: "ServiceFactory") -> int:
    """approved キューから投稿（活動時刻のNPCのみ）"""
    from dotenv import load_dotenv
    from nostr_sdk import Keys

    from ...domain import NpcKey, PostType, Scheduler
    from ...infrastructure import NostrPublisher

    load_dotenv(".env.keys")

    approved_entries = factory.queue_repo.get_all(QueueStatus.APPROVED)
    if not approved_entries:
        print("      No approved entries")
        return 0

    publisher = NostrPublisher(factory.settings.api_endpoint, dry_run=factory.settings.dry_run)
    posted = 0

    for entry in approved_entries:
        # このNPCが今投稿すべき時刻かチェック
        if entry.npc_id not in service.npcs:
            continue

        _, profile, state = service.npcs[entry.npc_id]

        # リアクションは活動時間内ならすぐ投稿（next_post_timeを無視）
        # 通常投稿・リプライはnext_post_timeもチェック
        if entry.post_type == PostType.REACTION:
            # 活動時間・曜日のみチェック
            current_hour = datetime.now().hour
            current_weekday = datetime.now().weekday()
            if current_hour not in profile.behavior.active_hours:
                continue
            if hasattr(profile.behavior, "active_days") and profile.behavior.active_days:
                if current_weekday not in profile.behavior.active_days:
                    continue
        else:
            # 通常投稿・リプライは完全チェック
            if not Scheduler.should_post_now(profile, state):
                continue

        try:
            npc_key = NpcKey.from_env(entry.npc_id)
            keys = Keys.parse(npc_key.nsec)

            # ウィンドウカラーのauroraタグを取得
            aurora_tag = None
            if profile.window_color:
                aurora_tag = profile.window_color.to_aurora_tag()

            # 投稿タイプに応じて投稿
            if entry.post_type == PostType.NORMAL:
                event_id = await publisher.publish(
                    keys, entry.content, entry.npc_name, aurora_tag=aurora_tag
                )
            elif entry.post_type == PostType.REACTION and entry.reply_to:
                event_id = await publisher.publish_reaction(
                    keys=keys,
                    emoji=entry.content,
                    npc_name=entry.npc_name,
                    target_event_id=entry.reply_to.event_id,
                    target_pubkey=entry.reply_to.pubkey or "",
                )
            elif entry.post_type == PostType.REPLY and entry.reply_to:
                event_id = await publisher.publish_reply(
                    keys=keys,
                    content=entry.content,
                    npc_name=entry.npc_name,
                    reply_to_event_id=entry.reply_to.event_id,
                    reply_to_pubkey=entry.reply_to.pubkey or "",
                    aurora_tag=aurora_tag,
                )
            else:
                event_id = await publisher.publish(
                    keys, entry.content, entry.npc_name, aurora_tag=aurora_tag
                )

            if event_id:
                factory.queue_repo.mark_posted(entry.id, event_id)
                # リアクション以外は次回投稿時刻を更新
                if entry.post_type != PostType.REACTION:
                    state.next_post_time = Scheduler.calculate_next_post_time(profile)
                    factory.state_repo.save(state)
                print(f"      ✅ {entry.npc_name}: {entry.content[:30]}...")
                posted += 1

        except Exception as e:
            print(f"      ❌ {entry.npc_name}: {e}")

    return posted
