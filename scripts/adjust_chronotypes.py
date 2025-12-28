#!/usr/bin/env python3
"""朝型・夜型NPCの活動時間を自然に調整"""

from pathlib import Path

import yaml

# 朝型: 5-17時
EARLY_BIRD_IDS = [29, 23, 16, 69, 38, 40]
EARLY_BIRD_HOURS = list(range(5, 18))  # 5-17

# 夜型: 14-2時
NIGHT_OWL_IDS = [4, 6, 8, 9, 20, 21, 35, 39, 41, 55]
NIGHT_OWL_HOURS = list(range(14, 24)) + [0, 1, 2]  # 14-23, 0-2


def update_profile(profile_path: Path, hours: list[int], chronotype: str) -> bool:
    """プロファイルの活動時間を更新"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return False

    # active_hoursを置き換え
    data["behavior"]["active_hours"] = sorted(hours, key=lambda x: (x < 5, x))
    data["behavior"]["chronotype"] = chronotype

    # hourly_weightも更新
    hourly_weight = {hour: 0.5 for hour in hours}
    data["behavior"]["hourly_weight"] = hourly_weight

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


def main():
    base_dir = Path(__file__).parent.parent / "npcs" / "residents"

    print("朝型NPC（5-17時）:")
    for npc_id in EARLY_BIRD_IDS:
        profile_path = base_dir / f"npc{npc_id:03d}" / "profile.yaml"
        if update_profile(profile_path, EARLY_BIRD_HOURS, "lark"):
            print(f"  npc{npc_id:03d}: 5-17時")

    print("\n夜型NPC（14-2時）:")
    for npc_id in NIGHT_OWL_IDS:
        profile_path = base_dir / f"npc{npc_id:03d}" / "profile.yaml"
        if update_profile(profile_path, NIGHT_OWL_HOURS, "owl"):
            print(f"  npc{npc_id:03d}: 14-2時")

    print("\n✅ 調整完了")


if __name__ == "__main__":
    main()
