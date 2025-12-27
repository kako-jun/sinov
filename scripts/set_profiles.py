#!/usr/bin/env python
"""
NPCプロフィール設定スクリプト

使い方:
  # 全NPCの名前を設定
  python scripts/set_profiles.py

  # 特定のNPCだけ設定
  python scripts/set_profiles.py --npc 1

  # dry-runで確認
  python scripts/set_profiles.py --dry-run
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from nostr_sdk import EventBuilder, Keys, Kind


async def set_profile(npc_id: int, name: str, about: str = "", dry_run: bool = False) -> bool:
    """Nostrプロフィールを設定（kind:0）"""
    from src.domain import NpcKey

    load_dotenv()
    load_dotenv(".env.keys")

    try:
        npc_key = NpcKey.from_env(npc_id)
        keys = Keys.parse(npc_key.nsec)
    except ValueError as e:
        print(f"  ❌ 鍵取得エラー: {e}")
        return False

    # プロフィールJSON
    profile_data = {"name": name}
    if about:
        profile_data["about"] = about

    content = json.dumps(profile_data, ensure_ascii=False)

    if dry_run:
        print(f"  [DRY RUN] npc{npc_id:03d}: {name}")
        return True

    # kind:0 プロフィールイベントを作成
    event = EventBuilder(Kind(0), content).sign_with_keys(keys)

    # MYPACE APIに送信
    api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")
    event_json = json.loads(event.as_json())

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                f"{api_endpoint}/api/publish",
                json={"event": event_json},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return True

            print(f"  ⚠️  API応答: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ 送信エラー: {e}")
        return False


def load_npc_profiles() -> list[dict]:
    """全NPCのプロフィールを読み込む"""
    profiles = []

    # residents ディレクトリ
    residents_dir = Path("npcs/residents")
    for npc_dir in sorted(residents_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_file = npc_dir / "profile.yaml"
        if not profile_file.exists():
            continue

        with open(profile_file) as f:
            profile = yaml.safe_load(f)
            profiles.append(profile)

    # backend ディレクトリ（記者・レビューア）
    backend_dir = Path("npcs/backend")
    if backend_dir.exists():
        for npc_dir in sorted(backend_dir.iterdir()):
            if not npc_dir.is_dir():
                continue

            profile_file = npc_dir / "profile.yaml"
            if not profile_file.exists():
                continue

            with open(profile_file) as f:
                profile = yaml.safe_load(f)
                profiles.append(profile)

    return profiles


async def main() -> None:
    parser = argparse.ArgumentParser(description="NPCプロフィール設定")
    parser.add_argument("--npc", "-n", type=int, help="特定のNPC IDだけ設定")
    parser.add_argument("--dry-run", "-d", action="store_true", help="実行せず確認のみ")
    args = parser.parse_args()

    profiles = load_npc_profiles()
    print(f"📋 {len(profiles)}人のNPCプロフィールを読み込みました\n")

    success = 0
    failed = 0

    for profile in profiles:
        npc_id = profile.get("id")
        name = profile.get("name", f"npc{npc_id:03d}")
        about = profile.get("background", {}).get("occupation", "")

        if args.npc and npc_id != args.npc:
            continue

        print(f"  設定中: npc{npc_id:03d} -> {name}", end=" ")

        if await set_profile(npc_id, name, about, args.dry_run):
            print("✅")
            success += 1
        else:
            print("❌")
            failed += 1

        # レート制限対策
        if not args.dry_run:
            await asyncio.sleep(0.5)

    print(f"\n✅ 完了: {success}件成功, {failed}件失敗")


if __name__ == "__main__":
    asyncio.run(main())
