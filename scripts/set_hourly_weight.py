#!/usr/bin/env python3
"""
全NPCにhourly_weightを設定するスクリプト

- 住民（residents）: 0.5（50%の確率で投稿）
- 記者・レビューア（backend）: 0.2（20%の確率で投稿）
"""

from pathlib import Path

import yaml


def set_hourly_weight(profile_path: Path, weight: float) -> bool:
    """profile.yamlにhourly_weightを設定"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return False

    # behaviorセクションがなければ作成
    if "behavior" not in data:
        data["behavior"] = {}

    # active_hoursを取得（なければデフォルト）
    active_hours = data["behavior"].get("active_hours", list(range(9, 22)))

    # hourly_weightを設定（active_hoursの時間帯のみ）
    data["behavior"]["hourly_weight"] = {hour: weight for hour in active_hours}

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


def main():
    base_dir = Path(__file__).parent.parent / "npcs"

    # 住民（residents）: 0.5
    residents_dir = base_dir / "residents"
    resident_count = 0
    for npc_dir in sorted(residents_dir.iterdir()):
        if npc_dir.is_dir() and npc_dir.name.startswith("npc"):
            profile_path = npc_dir / "profile.yaml"
            if set_hourly_weight(profile_path, 0.5):
                resident_count += 1
                print(f"  {npc_dir.name}: hourly_weight=0.5")

    print(f"\n✅ 住民: {resident_count}人に設定")

    # 記者・レビューア（backend）: 0.2
    backend_dir = base_dir / "backend"
    backend_count = 0
    for npc_dir in sorted(backend_dir.iterdir()):
        if npc_dir.is_dir():
            profile_path = npc_dir / "profile.yaml"
            if set_hourly_weight(profile_path, 0.2):
                backend_count += 1
                print(f"  {npc_dir.name}: hourly_weight=0.2")

    print(f"\n✅ バックエンド: {backend_count}人に設定")


if __name__ == "__main__":
    main()
