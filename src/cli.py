"""
CLIツール - ボット投稿管理
"""

import argparse
import asyncio

from dotenv import load_dotenv

from .application import BotService, InteractionService
from .config import Settings
from .domain import QueueEntry, QueueStatus
from .infrastructure import (
    MemoryRepository,
    NostrPublisher,
    OllamaProvider,
    ProfileRepository,
    QueueRepository,
    RelationshipRepository,
    StateRepository,
    TickStateRepository,
)


def init_env() -> Settings:
    """環境変数とSettingsを初期化"""
    load_dotenv()
    load_dotenv(".env.keys")
    return Settings()


def init_llm(settings: Settings) -> OllamaProvider | None:
    """LLMプロバイダーを初期化"""
    print("Initializing LLM...")
    try:
        llm = OllamaProvider(settings.ollama_host, settings.ollama_model)
        if not llm.is_available():
            print("⚠️  Ollama is not available")
            return None
        print(f"  Model: {settings.ollama_model}")
        return llm
    except Exception as e:
        print(f"⚠️  Could not connect to Ollama: {e}")
        return None


async def init_service(settings: Settings, llm: OllamaProvider) -> BotService:
    """BotServiceを初期化"""
    publisher = NostrPublisher(settings.api_endpoint, dry_run=True)
    profile_repo = ProfileRepository(settings.residents_dir, settings.backend_dir)
    state_repo = StateRepository(settings.residents_dir)
    memory_repo = MemoryRepository(settings.residents_dir)

    service = BotService(
        settings=settings,
        llm_provider=llm,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
        memory_repo=memory_repo,
    )

    print("Loading bots...")
    await service.load_bots()
    await service.initialize_keys()

    return service


# =============================================================================
# generate コマンド
# =============================================================================


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

    # 対象ボットを決定
    if args.all:
        bot_ids = list(service.bots.keys())
    elif args.bot:
        bot_id = _parse_bot_name(args.bot)
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


def _parse_bot_name(name: str) -> int | None:
    """bot001 -> 1, 1 -> 1"""
    if name.startswith("bot"):
        try:
            return int(name[3:])
        except ValueError:
            return None
    try:
        return int(name)
    except ValueError:
        return None


def _get_target_pubkey(resident: str) -> str | None:
    """住人名（bot001形式）からpubkeyを取得"""
    from .domain import BotKey

    bot_id = _parse_bot_name(resident)
    if bot_id is None:
        return None

    try:
        target_key = BotKey.from_env(bot_id)
        return target_key.pubkey
    except ValueError:
        # 鍵が見つからない場合
        return None


# =============================================================================
# queue コマンド
# =============================================================================


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


# =============================================================================
# review コマンド
# =============================================================================


def cmd_review(args: argparse.Namespace) -> None:
    """エントリーをレビュー（approve/reject）"""
    settings = init_env()
    queue_repo = QueueRepository(settings.queue_dir)

    if args.action == "approve":
        if args.dry_run:
            # dry run: 移動せずチェックのみ
            result = queue_repo.get_by_id(args.id)
            if result is None:
                print(f"Entry not found: {args.id}")
                return
            entry, status = result
            if status != QueueStatus.PENDING:
                print(f"⚠️  Entry is not pending (current: {status.value})")
            else:
                print(f"✅ [DRY RUN] Would approve: {entry.bot_name}")
                print(f"    {entry.content[:60]}...")
        else:
            approved = queue_repo.approve(args.id, args.note)
            if approved:
                print(f"✅ Approved: [{approved.id}] {approved.bot_name}")
            else:
                print(f"Entry not found in pending: {args.id}")

    elif args.action == "reject":
        if args.dry_run:
            result = queue_repo.get_by_id(args.id)
            if result is None:
                print(f"Entry not found: {args.id}")
                return
            entry, status = result
            if status != QueueStatus.PENDING:
                print(f"⚠️  Entry is not pending (current: {status.value})")
            else:
                print(f"❌ [DRY RUN] Would reject: {entry.bot_name}")
        else:
            rejected = queue_repo.reject(args.id, args.note)
            if rejected:
                print(f"❌ Rejected: [{rejected.id}] {rejected.bot_name}")
            else:
                print(f"Entry not found in pending: {args.id}")

    elif args.action == "list":
        # pending のリスト（queue list のエイリアス）
        args.status = "pending"
        args.summary = False
        cmd_queue(args)


# =============================================================================
# post コマンド
# =============================================================================


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
            print(f"  [{entry.id}] {entry.bot_name} ({post_type}): {entry.content[:50]}...")
        return

    # 実投稿
    publisher = NostrPublisher(settings.api_endpoint, dry_run=False)

    # Nostr署名鍵を初期化
    load_dotenv(".env.keys")
    from nostr_sdk import Keys

    from .domain import BotKey, PostType

    print(f"\n📤 Posting {len(entries)} entries...\n")
    posted = 0

    for entry in entries:
        try:
            # 鍵を取得
            bot_key = BotKey.from_env(entry.bot_id)
            keys = Keys.parse(bot_key.nsec)

            event_id: str | None = None

            # 投稿タイプに応じて処理を分岐
            if entry.post_type == PostType.REPLY and entry.reply_to:
                # リプライ投稿
                # ターゲットのpubkeyを取得（住人の場合）
                target_pubkey = _get_target_pubkey(entry.reply_to.resident)
                event_id = await publisher.publish_reply(
                    keys=keys,
                    content=entry.content,
                    bot_name=entry.bot_name,
                    reply_to_event_id=entry.reply_to.event_id,
                    reply_to_pubkey=target_pubkey,
                )
                print(f"  💬 {entry.bot_name}: {entry.content[:40]}...")

            elif entry.post_type == PostType.REACTION and entry.reply_to:
                # リアクション投稿
                target_pubkey = _get_target_pubkey(entry.reply_to.resident)
                if not target_pubkey:
                    print(f"  ⏭️  {entry.bot_name}: Reaction skipped (pubkey not found)")
                    continue

                event_id = await publisher.publish_reaction(
                    keys=keys,
                    emoji=entry.content,
                    bot_name=entry.bot_name,
                    target_event_id=entry.reply_to.event_id,
                    target_pubkey=target_pubkey,
                )
                print(f"  ❤️  {entry.bot_name}: {entry.content} → {entry.reply_to.resident}")

            else:
                # 通常投稿
                event_id = await publisher.publish(keys, entry.content, entry.bot_name)
                print(f"  ✅ {entry.bot_name}: {entry.content[:40]}...")

            # キューを更新
            queue_repo.mark_posted(entry.id, event_id)
            posted += 1

        except Exception as e:
            print(f"  ❌ {entry.bot_name}: {e}")

    print(f"\n✅ Posted {posted}/{len(entries)} entries")


# =============================================================================
# tick コマンド
# =============================================================================


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
    print(f"   Processing {len(target_ids)} residents (index {start_idx}-{end_idx - 1} of {total_bots})")

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

    print(f"\n✅ Tick complete: {generated} generated, {total_interactions} interactions, {reviewed} reviewed")


async def run_reviewer(service: "BotService", queue_repo: QueueRepository) -> int:
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

            reviewed += 1
        except Exception as e:
            print(f"      ⚠️  {entry.bot_name}: {e}")

    return reviewed


# =============================================================================
# メイン
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinov Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # generate コマンド
    gen_parser = subparsers.add_parser("generate", help="Generate posts to queue")
    gen_parser.add_argument("--all", "-a", action="store_true", help="All bots")
    gen_parser.add_argument("--bot", "-b", type=str, help="Bot name (e.g., bot001)")
    gen_parser.add_argument("--dry-run", "-n", action="store_true", help="Save to dry_run.json")

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
        "--count", "-c", type=int, default=10, help="Number of bots to process (default: 10)"
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
