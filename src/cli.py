"""
CLIツール - ボット投稿管理
"""

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from .application import BotService
from .config import Settings
from .domain import QueueEntry, QueueStatus
from .infrastructure import (
    NostrPublisher,
    OllamaProvider,
    ProfileRepository,
    QueueRepository,
    StateRepository,
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
    profile_repo = ProfileRepository(settings.profiles_dir)
    state_repo = StateRepository(settings.states_file)

    service = BotService(
        settings=settings,
        llm_provider=llm,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
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
    queue_repo = QueueRepository(Path("bots/queue"))

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


# =============================================================================
# queue コマンド
# =============================================================================


def cmd_queue(args: argparse.Namespace) -> None:
    """キューの状態を表示"""
    queue_repo = QueueRepository(Path("bots/queue"))

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
    queue_repo = QueueRepository(Path("bots/queue"))

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
    queue_repo = QueueRepository(Path("bots/queue"))

    entries = queue_repo.get_all(QueueStatus.APPROVED)

    if not entries:
        print("No approved entries to post")
        return

    if args.dry_run:
        print(f"\n🔍 [DRY RUN] Would post {len(entries)} entries:\n")
        for entry in entries:
            print(f"  [{entry.id}] {entry.bot_name}: {entry.content[:50]}...")
        return

    # 実投稿
    publisher = NostrPublisher(settings.api_endpoint, dry_run=False)

    # Nostr署名鍵を初期化
    load_dotenv(".env.keys")
    from nostr_sdk import Keys

    from .domain import BotKey

    print(f"\n📤 Posting {len(entries)} entries...\n")
    posted = 0

    for entry in entries:
        try:
            # 鍵を取得
            bot_key = BotKey.from_env(entry.bot_id)
            keys = Keys.parse(bot_key.nsec)

            # 投稿
            event_id = await publisher.publish(keys, entry.content, entry.bot_name)

            # キューを更新
            queue_repo.mark_posted(entry.id, event_id)

            print(f"  ✅ {entry.bot_name}: {entry.content[:40]}...")
            posted += 1
        except Exception as e:
            print(f"  ❌ {entry.bot_name}: {e}")

    print(f"\n✅ Posted {posted}/{len(entries)} entries")


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
    elif args.command == "preview":
        # 後方互換: generate --dry-run にリダイレクト
        args.dry_run = True
        asyncio.run(cmd_generate(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
