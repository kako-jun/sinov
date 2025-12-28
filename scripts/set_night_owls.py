#!/usr/bin/env python3
"""夜型NPCを設定するスクリプト"""

from pathlib import Path

import yaml

NIGHT_OWL_IDS = [4, 6, 8, 9, 20, 21, 35, 39, 41, 55]
NIGHT_HOURS = [22, 23, 0, 1, 2]


def set_night_owl(profile_path: Path) -> bool:
    """プロファイルを夜型に設定"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return False

    # active_hoursに夜間を追加
    active_hours = data.get("behavior", {}).get("active_hours", [])
    for hour in NIGHT_HOURS:
        if hour not in active_hours:
            active_hours.append(hour)
    active_hours.sort(key=lambda x: (x < 9, x))  # 9時から順に、深夜は最後
    data["behavior"]["active_hours"] = active_hours

    # chronotypeをowlに
    data["behavior"]["chronotype"] = "owl"

    # hourly_weightに夜間を追加
    hourly_weight = data["behavior"].get("hourly_weight", {})
    for hour in NIGHT_HOURS:
        hourly_weight[hour] = 0.5
    data["behavior"]["hourly_weight"] = hourly_weight

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


def main():
    base_dir = Path(__file__).parent.parent / "npcs" / "residents"

    for npc_id in NIGHT_OWL_IDS:
        npc_dir = base_dir / f"npc{npc_id:03d}"
        profile_path = npc_dir / "profile.yaml"
        if set_night_owl(profile_path):
            print(f"  npc{npc_id:03d}: 夜型に設定")
        else:
            print(f"  npc{npc_id:03d}: スキップ")

    print(f"\n✅ {len(NIGHT_OWL_IDS)}人を夜型に設定")


if __name__ == "__main__":
    main()
