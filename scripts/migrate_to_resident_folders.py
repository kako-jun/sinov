#!/usr/bin/env python3
"""
住民ごとのフォルダ構造への移行スクリプト

旧構造:
  bots/profiles/bot001.yaml
  bots/data/memories/bot001.json
  bots/data/states.json

新構造:
  bots/residents/bot001/profile.yaml
  bots/residents/bot001/memory.json
  bots/residents/bot001/state.json
  bots/backend/reporter_tech/profile.yaml
"""

import json
import re
import shutil
from pathlib import Path


def migrate():
    base_dir = Path(__file__).parent.parent
    old_profiles_dir = base_dir / "bots" / "profiles"
    old_memories_dir = base_dir / "bots" / "data" / "memories"
    old_states_file = base_dir / "bots" / "data" / "states.json"

    new_residents_dir = base_dir / "bots" / "residents"
    new_backend_dir = base_dir / "bots" / "backend"

    # 裏方ボットのプレフィックス
    backend_patterns = ["reporter_", "reviewer", "bot_news_collector"]

    # 古い状態ファイルを読み込み
    old_states = {}
    if old_states_file.exists():
        with open(old_states_file, encoding="utf-8") as f:
            old_states = json.load(f)

    # プロファイルを移行
    print("Migrating profiles...")
    for profile_file in old_profiles_dir.glob("*.yaml"):
        if profile_file.name == "_common.yaml":
            continue

        name = profile_file.stem

        # 裏方ボットかどうか判定
        is_backend = any(name.startswith(p) or name == p.rstrip("_") for p in backend_patterns)

        if is_backend:
            # 裏方 -> bots/backend/{name}/profile.yaml
            target_dir = new_backend_dir / name
        else:
            # 住人 -> bots/residents/{name}/profile.yaml
            target_dir = new_residents_dir / name

        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "profile.yaml"

        shutil.copy2(profile_file, target_file)
        print(f"  {profile_file.name} -> {target_file.relative_to(base_dir)}")

        # 住人の場合、メモリと状態も移行
        if not is_backend:
            # bot001 -> 1
            match = re.match(r"bot(\d+)", name)
            if match:
                bot_id = int(match.group(1))

                # メモリファイル
                old_memory = old_memories_dir / f"{name}.json"
                if old_memory.exists():
                    new_memory = target_dir / "memory.json"
                    shutil.copy2(old_memory, new_memory)
                    print(f"    + memory.json")

                # 状態（states.json から抽出）
                bot_id_str = str(bot_id)
                if bot_id_str in old_states:
                    new_state = target_dir / "state.json"
                    with open(new_state, "w", encoding="utf-8") as f:
                        json.dump(old_states[bot_id_str], f, indent=2, ensure_ascii=False)
                    print(f"    + state.json")

    print("\nMigration complete!")
    print(f"\nNew structure:")
    print(f"  Residents: {new_residents_dir}")
    print(f"  Backend: {new_backend_dir}")


if __name__ == "__main__":
    migrate()
