#!/usr/bin/env python3
"""朝型NPCを設定するスクリプト"""

from pathlib import Path

import yaml

EARLY_BIRD_IDS = [29, 23, 16, 69, 38, 40]
EARLY_HOURS = [5, 6, 7, 8]


def set_early_bird(profile_path: Path) -> bool:
    """プロファイルを朝型に設定"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return False

    # active_hoursに早朝を追加
    active_hours = data.get("behavior", {}).get("active_hours", [])
    for hour in EARLY_HOURS:
        if hour not in active_hours:
            active_hours.append(hour)
    active_hours.sort()
    data["behavior"]["active_hours"] = active_hours

    # chronotypeをlarkに
    data["behavior"]["chronotype"] = "lark"

    # hourly_weightに早朝を追加
    hourly_weight = data["behavior"].get("hourly_weight", {})
    for hour in EARLY_HOURS:
        hourly_weight[hour] = 0.5
    data["behavior"]["hourly_weight"] = hourly_weight

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


def main():
    base_dir = Path(__file__).parent.parent / "npcs" / "residents"

    for npc_id in EARLY_BIRD_IDS:
        npc_dir = base_dir / f"npc{npc_id:03d}"
        profile_path = npc_dir / "profile.yaml"
        if set_early_bird(profile_path):
            print(f"  npc{npc_id:03d}: 朝型に設定")
        else:
            print(f"  npc{npc_id:03d}: スキップ")

    print(f"\n✅ {len(EARLY_BIRD_IDS)}人を朝型に設定")


if __name__ == "__main__":
    main()
