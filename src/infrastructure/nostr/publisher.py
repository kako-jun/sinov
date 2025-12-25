"""
Nostr投稿パブリッシャー
"""

import json

import httpx
from nostr_sdk import EventBuilder, Keys, Tag


class NostrPublisher:
    """MYPACE API経由でNostr投稿を行う"""

    def __init__(self, api_endpoint: str, dry_run: bool = False):
        self.api_endpoint = api_endpoint
        self.dry_run = dry_run

    async def publish(
        self,
        keys: Keys,
        content: str,
        bot_name: str,
    ) -> str | None:
        """
        投稿を実行

        Returns:
            イベントID（成功時）、None（dry_run時）
        """
        if not content or len(content.strip()) == 0:
            raise ValueError("Post content is empty")

        if self.dry_run:
            print(f"[DRY RUN] {bot_name}:")
            print(f"  {content}")
            print()
            return None

        # タグを作成
        mypace_tag = Tag.hashtag("mypace")
        client_tag = Tag.parse(["client", "sinov"])

        # イベント作成・署名
        event = EventBuilder.text_note(content).tags([mypace_tag, client_tag]).sign_with_keys(keys)

        # NostrイベントをJSON化
        event_json = json.loads(event.as_json())

        # MYPACE APIに送信
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False,
            trust_env=True,
        ) as client:
            response = await client.post(
                f"{self.api_endpoint}/api/publish",
                json={"event": event_json},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                error_data = (
                    response.json()
                    if response.headers.get("content-type") == "application/json"
                    else {}
                )
                raise RuntimeError(f"API error: {response.status_code} - {error_data}")

            result = response.json()
            if not result.get("success"):
                raise RuntimeError(f"Publish failed: {result}")

        event_id: str = event.id().to_hex()
        return event_id
