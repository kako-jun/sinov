#!/usr/bin/env python3
"""
NPC プロフィール画像設定スクリプト

画像をnostr.buildにアップロードし、kind:0プロフィールイベントを発行する。
NIP-98認証を使用。
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from nostr_sdk import EventBuilder, Keys, Kind, Tag

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

NOSTR_BUILD_UPLOAD_URL = "https://nostr.build/api/v2/upload/files"

# Week1 画像フォルダ
WEEK1_DIR = Path("/mnt/tp-share_g/アイコンと背景/week1")

# NPC と画像の割り当て
# 1は使用済み、2同士は同じNPCに、残りは自由組み合わせ
NPC_IMAGE_MAPPING = {
    # NPC001は使用済みなのでスキップ
    2: {  # nullpo
        "icon": "2.jpg",
        "bg": "2.jpg",
    },
    3: {  # mcΔt
        "icon": "DSC_0131.JPG",
        "bg": "IMG20250412130623.jpg",
    },
    4: {  # いちごミルク
        "icon": "IMG20250824192730.jpg",
        "bg": "IMG20251011131924.jpg",
    },
    6: {  # 鹿丸
        "icon": "IMG20250926173032.jpg",
        "bg": "IMG_20250412_133303741_MFNR.jpg",
    },
    10: {  # チョコP
        "icon": "IMG20251013071716.jpg",
        "bg": "PXL_20250505_015614201.jpg",
    },
    18: {  # cyan
        "icon": "Screenshot_2025-05-05-08-18-37-04_f8da0d17f671966b9c609eafd0d5a812.jpg",
        "bg": "PXL_20250618_112637710.jpg",
    },
    24: {  # momiji
        "icon": "_6707e8a9-0758-4b96-81bb-394b3375e59b.jpeg",
        "bg": "PXL_20250704_094808237.MP.jpg",
    },
    # 余った画像: 記者とレビューア
    96: {  # しまうー (reporter_tech)
        "icon": "_e0ca9380-98c3-45da-94d8-4c7a53ce50c6.jpeg",
        "bg": "VRChat_2023-10-22_23-18-16.326_1920x1080.png",
    },
    101: {  # Imposter (reviewer)
        "icon": "スクリーンショット 2025-05-23 210748.png",
        "bg": "スクリーンショット 2024-11-09 132814.png",
    },
}


async def create_nip98_auth_event(keys: Keys, url: str, method: str) -> dict:
    """NIP-98認証イベントを作成"""
    tags = [
        Tag.parse(["u", url]),
        Tag.parse(["method", method]),
    ]
    event = EventBuilder(Kind(27235), "").tags(tags).sign_with_keys(keys)
    return json.loads(event.as_json())


async def upload_to_nostr_build(keys: Keys, file_path: str) -> str | None:
    """nostr.buildに画像をアップロード"""
    if not os.path.exists(file_path):
        print(f"  ❌ ファイルが見つかりません: {file_path}")
        return None

    auth_event = await create_nip98_auth_event(keys, NOSTR_BUILD_UPLOAD_URL, "POST")
    auth_header = base64.b64encode(json.dumps(auth_event).encode()).decode()

    with open(file_path, "rb") as f:
        file_data = f.read()

    filename = os.path.basename(file_path)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                NOSTR_BUILD_UPLOAD_URL,
                headers={"Authorization": f"Nostr {auth_header}"},
                files={"file": (filename, file_data)},
            )

            if response.status_code != 200:
                print(f"  ❌ アップロード失敗: {response.status_code}")
                print(f"     {response.text[:200]}")
                return None

            data = response.json()
            if data.get("status") == "success" and data.get("data"):
                url = data["data"][0].get("url")
                print(f"  ✅ アップロード成功: {url}")
                return url
            else:
                print(f"  ❌ レスポンスエラー: {data}")
                return None

        except Exception as e:
            print(f"  ❌ アップロードエラー: {e}")
            return None


async def publish_profile_event(
    keys: Keys,
    api_endpoint: str,
    name: str,
    about: str = "",
    picture: str | None = None,
    banner: str | None = None,
) -> str | None:
    """kind:0 プロフィールイベントを発行"""
    profile_content = {"name": name}
    if about:
        profile_content["about"] = about
    if picture:
        profile_content["picture"] = picture
    if banner:
        profile_content["banner"] = banner

    content_json = json.dumps(profile_content, ensure_ascii=False)
    event = EventBuilder(Kind(0), content_json).sign_with_keys(keys)
    event_json = json.loads(event.as_json())

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            response = await client.post(
                f"{api_endpoint}/api/publish",
                json={"event": event_json},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                print(f"  ❌ プロフィール発行失敗: {response.status_code}")
                return None

            result = response.json()
            if result.get("success"):
                event_id = event.id().to_hex()
                print(f"  ✅ プロフィール発行成功: {event_id[:16]}...")
                return event_id
            else:
                print(f"  ❌ 発行エラー: {result}")
                return None

        except Exception as e:
            print(f"  ❌ 発行エラー: {e}")
            return None


async def set_npc_profile(
    npc_id: int,
    icon_filename: str,
    bg_filename: str,
    api_endpoint: str,
) -> bool:
    """NPCのプロフィールを設定"""
    import yaml

    nsec = os.getenv(f"NPC_{npc_id:03d}_NSEC")
    if not nsec:
        print(f"  ⚠️ NPC_{npc_id:03d}_NSEC が設定されていません")
        return False

    keys = Keys.parse(nsec)
    pubkey = keys.public_key().to_hex()

    # プロフィールパスを探す（residents または backend）
    profile_path = project_root / f"npcs/residents/npc{npc_id:03d}/profile.yaml"
    if not profile_path.exists():
        # backendを探す
        backend_dirs = {
            96: "reporter_tech",
            101: "reviewer",
        }
        if npc_id in backend_dirs:
            profile_path = project_root / f"npcs/backend/{backend_dirs[npc_id]}/profile.yaml"
    if not profile_path.exists():
        print(f"  ⚠️ プロフィールが見つかりません: {profile_path}")
        return False

    with open(profile_path) as f:
        profile = yaml.safe_load(f)

    name = profile.get("name", f"NPC{npc_id:03d}")
    occupation = profile.get("background", {}).get("occupation", "")
    about = occupation if occupation else ""

    print(f"\n📝 NPC{npc_id:03d} ({name})")
    print(f"   pubkey: {pubkey[:16]}...")

    icon_path = WEEK1_DIR / "icon" / icon_filename
    bg_path = WEEK1_DIR / "bg" / bg_filename

    print(f"   アイコン: {icon_filename}")
    picture_url = await upload_to_nostr_build(keys, str(icon_path))

    print(f"   背景: {bg_filename}")
    banner_url = await upload_to_nostr_build(keys, str(bg_path))

    if not picture_url and not banner_url:
        print("  ❌ 画像のアップロードに失敗しました")
        return False

    print("   プロフィールを発行中...")
    event_id = await publish_profile_event(
        keys=keys,
        api_endpoint=api_endpoint,
        name=name,
        about=about,
        picture=picture_url,
        banner=banner_url,
    )

    return event_id is not None


async def main():
    """メイン処理"""
    load_dotenv(project_root / ".env")
    load_dotenv(project_root / ".env.keys")

    api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")

    print("🖼️  NPC プロフィール設定 (Week1)")
    print(f"   API: {api_endpoint}")
    print(f"   画像フォルダ: {WEEK1_DIR}")

    success_count = 0
    for npc_id, images in NPC_IMAGE_MAPPING.items():
        try:
            if await set_npc_profile(npc_id, images["icon"], images["bg"], api_endpoint):
                success_count += 1
        except Exception as e:
            print(f"  ❌ NPC{npc_id:03d} エラー: {e}")

    print(f"\n✅ 完了: {success_count}/{len(NPC_IMAGE_MAPPING)} NPCs")


if __name__ == "__main__":
    asyncio.run(main())
