#!/usr/bin/env python3
"""
段階的リリース管理スクリプト

各週10人ずつNPCを有効化する。
ジャンルバランスを考慮した配置。
"""

import argparse
from pathlib import Path

import yaml

# 週ごとの有効化リスト
# Week 1: 各ジャンル代表 + reviewer
# Week 2-10: 残りを順次追加 + reporters
ROLLOUT_SCHEDULE = {
    1: {
        "residents": [1, 2, 3, 4, 6, 10, 18, 24],  # 8人
        "backend": ["reviewer", "reporter_general"],  # レビューア + 記者1人
    },
    2: {
        "residents": [5, 7, 8, 9, 11, 12, 15, 30],  # +8人
        "backend": ["reporter_tech"],  # +記者1人
    },
    3: {
        "residents": [13, 14, 16, 17, 19, 20, 21, 22, 23],  # +9人
        "backend": ["reporter_game"],  # +記者1人
    },
    4: {
        "residents": [25, 26, 27, 28, 29, 31, 32, 33, 34],  # +9人
        "backend": ["reporter_creative"],  # +記者1人
    },
    5: {
        "residents": [35, 36, 37, 38, 39, 40, 41, 42, 43, 44],  # +10人
        "backend": ["reporter_trend"],  # +記者1人（これで記者全員）
    },
    6: {
        "residents": [45, 46, 47, 48, 49, 50, 51, 52, 53, 54],  # +10人
        "backend": [],
    },
    7: {
        "residents": [55, 56, 57, 58, 59, 60, 61, 62, 63, 64],  # +10人
        "backend": [],
    },
    8: {
        "residents": [65, 66, 67, 68, 69, 70, 71, 72, 73, 74],  # +10人
        "backend": [],
    },
    9: {
        "residents": [75, 76, 77, 78, 79, 80, 81, 82, 83, 84],  # +10人
        "backend": [],
    },
    10: {
        "residents": [85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95],  # +11人
        "backend": [],
    },
}


def get_npcs_dir() -> Path:
    return Path(__file__).parent.parent / "npcs"


def get_enabled_ids_up_to_week(week: int) -> tuple[set[int], set[str]]:
    """指定週までに有効化されるNPC IDを取得"""
    resident_ids: set[int] = set()
    backend_names: set[str] = set()

    for w in range(1, week + 1):
        if w in ROLLOUT_SCHEDULE:
            resident_ids.update(ROLLOUT_SCHEDULE[w]["residents"])
            backend_names.update(ROLLOUT_SCHEDULE[w]["backend"])

    return resident_ids, backend_names


def update_profile(profile_path: Path, posts: bool) -> bool:
    """profile.yamlのpostsフラグを更新"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["posts"] = posts

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


def apply_rollout(week: int, dry_run: bool = False) -> None:
    """指定週までのロールアウトを適用"""
    npcs_dir = get_npcs_dir()
    enabled_residents, enabled_backend = get_enabled_ids_up_to_week(week)

    print(f"🚀 Applying rollout up to Week {week}")
    print(f"   Residents: {len(enabled_residents)} NPCs")
    print(f"   Backend: {enabled_backend}")
    print()

    enabled_count = 0
    disabled_count = 0

    # Residents
    residents_dir = npcs_dir / "residents"
    for npc_dir in sorted(residents_dir.iterdir()):
        if not npc_dir.is_dir() or not npc_dir.name.startswith("npc"):
            continue

        npc_id = int(npc_dir.name.replace("npc", ""))
        profile_path = npc_dir / "profile.yaml"
        should_enable = npc_id in enabled_residents

        if dry_run:
            status = "✅" if should_enable else "⏸️"
            print(f"  {status} {npc_dir.name}: posts={should_enable}")
        else:
            update_profile(profile_path, should_enable)

        if should_enable:
            enabled_count += 1
        else:
            disabled_count += 1

    # Backend
    backend_dir = npcs_dir / "backend"
    for npc_dir in sorted(backend_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_path = npc_dir / "profile.yaml"
        should_enable = npc_dir.name in enabled_backend

        if dry_run:
            status = "✅" if should_enable else "⏸️"
            print(f"  {status} {npc_dir.name}: posts={should_enable}")
        else:
            update_profile(profile_path, should_enable)

        if should_enable:
            enabled_count += 1
        else:
            disabled_count += 1

    print()
    print(f"{'[DRY RUN] ' if dry_run else ''}✅ Enabled: {enabled_count}")
    print(f"{'[DRY RUN] ' if dry_run else ''}⏸️  Disabled: {disabled_count}")


def show_status() -> None:
    """現在の有効化状況を表示"""
    npcs_dir = get_npcs_dir()

    enabled = []
    disabled = []

    # Residents
    residents_dir = npcs_dir / "residents"
    for npc_dir in sorted(residents_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_path = npc_dir / "profile.yaml"
        if not profile_path.exists():
            continue

        with open(profile_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        posts = data.get("posts", True)  # デフォルトはTrue（後方互換）
        name = data.get("name", npc_dir.name)

        if posts:
            enabled.append(f"{npc_dir.name}: {name}")
        else:
            disabled.append(f"{npc_dir.name}: {name}")

    # Backend
    backend_dir = npcs_dir / "backend"
    for npc_dir in sorted(backend_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_path = npc_dir / "profile.yaml"
        if not profile_path.exists():
            continue

        with open(profile_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        posts = data.get("posts", True)

        if posts:
            enabled.append(f"{npc_dir.name}")
        else:
            disabled.append(f"{npc_dir.name}")

    print("📊 Current Status")
    print(f"   Enabled: {len(enabled)}")
    print(f"   Disabled: {len(disabled)}")
    print()
    print("✅ Enabled NPCs:")
    for name in enabled[:20]:
        print(f"   {name}")
    if len(enabled) > 20:
        print(f"   ... (+{len(enabled) - 20})")


def show_schedule() -> None:
    """リリーススケジュールを表示"""
    print("📅 Rollout Schedule")
    print()

    total = 0
    for week, data in sorted(ROLLOUT_SCHEDULE.items()):
        residents = data["residents"]
        backend = data["backend"]
        total += len(residents) + len(backend)
        print(f"Week {week}: +{len(residents)} residents, +{len(backend)} backend = {total} total")


def main():
    parser = argparse.ArgumentParser(description="NPC段階的リリース管理")
    parser.add_argument("--week", type=int, help="有効化する週（1-10）")
    parser.add_argument("--status", action="store_true", help="現在の状況を表示")
    parser.add_argument("--schedule", action="store_true", help="スケジュールを表示")
    parser.add_argument("--dry-run", action="store_true", help="実際には変更しない")

    args = parser.parse_args()

    if args.schedule:
        show_schedule()
    elif args.status:
        show_status()
    elif args.week:
        if args.week < 1 or args.week > 10:
            print("❌ Week must be between 1 and 10")
            return
        apply_rollout(args.week, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
