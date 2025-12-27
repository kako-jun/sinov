#!/usr/bin/env python3
"""
投稿頻度を大幅に削減するスクリプト
目標: 10人で1日6投稿程度 → 1人あたり0.6回/日
"""

import random
from pathlib import Path

import yaml


def reduce_frequency():
    """全NPCの投稿頻度を削減"""
    npcs_dir = Path("npcs/residents")

    # 曜日パターン（ばらつきを大きく：週1〜毎日まで）
    weekday_patterns = [
        # 週1（レア出現）
        [0],  # 月曜のみ
        [2],  # 水曜のみ
        [4],  # 金曜のみ
        [6],  # 日曜のみ
        # 週2
        [1, 4],  # 火金
        [2, 5],  # 水土
        [0, 6],  # 月日
        [3, 6],  # 木日
        # 週3
        [0, 2, 4],  # 月水金
        [1, 3, 5],  # 火木土
        [0, 3, 6],  # 月木日
        # 週4
        [0, 2, 4, 6],  # 月水金日
        [1, 2, 4, 5],  # 火水金土
        # 週5（平日のみ）
        [0, 1, 2, 3, 4],
        # 週末のみ
        [5, 6],
        # 毎日（少数のみ）
        [0, 1, 2, 3, 4, 5, 6],
    ]

    updated = 0
    for npc_dir in sorted(npcs_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_file = npc_dir / "profile.yaml"
        if not profile_file.exists():
            continue

        with open(profile_file, encoding="utf-8") as f:
            profile = yaml.safe_load(f)

        if "behavior" not in profile:
            continue

        behavior = profile["behavior"]
        old_freq = behavior.get("post_frequency", 3)

        # 頻度を0.3-1.0の範囲に削減（元の値に応じて調整）
        # 元が多い人ほど削減率を大きく
        if old_freq >= 6:
            new_freq = round(random.uniform(0.5, 0.8), 1)
        elif old_freq >= 4:
            new_freq = round(random.uniform(0.4, 0.7), 1)
        else:
            new_freq = round(random.uniform(0.3, 0.6), 1)

        behavior["post_frequency"] = new_freq

        # 曜日パターンを重み付きで割り当て（週1-2が多め、毎日は少数）
        r = random.random()
        if r < 0.15:  # 15%: 週1
            active_days = random.choice(weekday_patterns[0:4])
        elif r < 0.40:  # 25%: 週2
            active_days = random.choice(weekday_patterns[4:8])
        elif r < 0.65:  # 25%: 週3
            active_days = random.choice(weekday_patterns[8:11])
        elif r < 0.85:  # 20%: 週4-5
            active_days = random.choice(weekday_patterns[11:15])
        else:  # 15%: 毎日
            active_days = weekday_patterns[15]

        behavior["active_days"] = active_days

        # varianceも調整（より大きなばらつき）
        behavior["post_frequency_variance"] = 0.7

        with open(profile_file, "w", encoding="utf-8") as f:
            yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        days_str = "".join(weekday_names[d] for d in sorted(active_days))
        print(f"{npc_dir.name}: {old_freq}回/日 → {new_freq}回/日 (活動日: {days_str})")
        updated += 1

    print(f"\n✅ {updated} NPCs updated")

    # 概算を表示
    avg_freq = 0.5  # 平均0.5回/日
    avg_days = 4  # 平均4日/週活動
    npcs_per_week = 10  # Week 1のNPC数
    estimated_daily = npcs_per_week * avg_freq * (avg_days / 7)
    print(f"📊 概算: Week1の10人で約 {estimated_daily:.1f} 投稿/日")


if __name__ == "__main__":
    reduce_frequency()
