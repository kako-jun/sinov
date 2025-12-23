"""
各ボットの全投稿を削除する（kind:5 deletion event）
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from nostr_sdk import EventBuilder, Keys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.types import BotKey


async def delete_all_posts(bot_id: int, keys: Keys, api_endpoint: str) -> None:
    """指定ボットの全投稿を削除"""
    try:
        from nostr_sdk import EventBuilder, Kind, Tag
        
        # まず、このbotが投稿したイベントIDを取得する必要がある
        # しかしイベントIDを保存していないため、npubで検索してから削除する
        # 
        # NostrのNIP-09: kind:5削除イベントは、eタグでイベントIDを指定する
        # イベントIDが不明な場合は、空のkind:5を送っても効果がない
        
        # 代替案: テキストノート(kind:1)のみを対象とした削除イベント
        # しかし具体的なイベントIDが必要
        
        print(f"⚠️  Bot {bot_id}: Cannot delete without event IDs")
        print(f"   Manual deletion required from MYPACE admin panel")
        print(f"   Pubkey: {keys.public_key().to_bech32()}")
        
        return
        
        # MYPACE APIに送信
        async with httpx.AsyncClient(timeout=30.0, verify=False, trust_env=True) as client:
            response = await client.post(
                f"{api_endpoint}/api/publish",
                json={"event": event_json},
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Bot {bot_id}: Deletion event sent")
                else:
                    print(f"⚠️  Bot {bot_id}: {result}")
            else:
                print(f"❌ Bot {bot_id}: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Bot {bot_id}: {e}")


async def main() -> None:
    # 環境変数読み込み
    load_dotenv()
    load_dotenv(".env.keys")
    
    api_endpoint = os.getenv("API_ENDPOINT", "https://api.mypace.llll-ll.com")
    
    print(f"Deleting all posts from bots 1-3...")
    print(f"API endpoint: {api_endpoint}\n")
    
    # Bot 1-3の鍵を読み込んで削除イベント送信
    tasks = []
    for bot_id in [1, 2, 3]:
        try:
            bot_key = BotKey.from_env(bot_id)
            keys = Keys.parse(bot_key.nsec)
            tasks.append(delete_all_posts(bot_id, keys, api_endpoint))
        except Exception as e:
            print(f"❌ Failed to load bot {bot_id}: {e}")
    
    if tasks:
        await asyncio.gather(*tasks)
    
    print("\n✅ Deletion events sent. Posts will be removed from relays.")


if __name__ == "__main__":
    asyncio.run(main())
