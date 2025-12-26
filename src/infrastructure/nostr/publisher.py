"""
Nostr投稿パブリッシャー
"""

import json
from typing import Any

import httpx
from nostr_sdk import EventBuilder, Keys, Kind, Tag


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

        return await self._send_event(event)

    async def publish_reply(
        self,
        keys: Keys,
        content: str,
        bot_name: str,
        reply_to_event_id: str,
        reply_to_pubkey: str | None = None,
    ) -> str | None:
        """
        リプライを投稿

        Args:
            keys: 署名用の鍵
            content: 投稿内容
            bot_name: NPC名（ログ用）
            reply_to_event_id: リプライ先のイベントID
            reply_to_pubkey: リプライ先の著者pubkey（任意）

        Returns:
            イベントID（成功時）、None（dry_run時）
        """
        if not content or len(content.strip()) == 0:
            raise ValueError("Reply content is empty")

        if self.dry_run:
            print(f"[DRY RUN] {bot_name} (reply to {reply_to_event_id[:8]}...):")
            print(f"  {content}")
            print()
            return None

        # タグを作成
        tags = [
            Tag.hashtag("mypace"),
            Tag.parse(["client", "sinov"]),
            # リプライ先のイベントID（rootとreplyを同じにする = 直接リプライ）
            Tag.parse(["e", reply_to_event_id, "", "root"]),
            Tag.parse(["e", reply_to_event_id, "", "reply"]),
        ]

        # リプライ先の著者pubkeyがあれば追加
        if reply_to_pubkey:
            tags.append(Tag.parse(["p", reply_to_pubkey]))

        # イベント作成・署名
        event = EventBuilder.text_note(content).tags(tags).sign_with_keys(keys)

        return await self._send_event(event)

    async def publish_reaction(
        self,
        keys: Keys,
        emoji: str,
        bot_name: str,
        target_event_id: str,
        target_pubkey: str,
    ) -> str | None:
        """
        リアクションを投稿（NIP-25）

        Args:
            keys: 署名用の鍵
            emoji: リアクション絵文字（+, -, または絵文字）
            bot_name: NPC名（ログ用）
            target_event_id: リアクション対象のイベントID
            target_pubkey: リアクション対象の著者pubkey

        Returns:
            イベントID（成功時）、None（dry_run時）
        """
        if self.dry_run:
            print(f"[DRY RUN] {bot_name} (react {emoji} to {target_event_id[:8]}...):")
            print()
            return None

        # タグを作成
        tags = [
            Tag.parse(["e", target_event_id]),
            Tag.parse(["p", target_pubkey]),
        ]

        # kind:7 リアクションイベントを作成
        event = EventBuilder(Kind(7), emoji).tags(tags).sign_with_keys(keys)

        return await self._send_event(event)

    async def _send_event(self, event: Any) -> str:
        """署名済みイベントをMYPACE APIに送信"""
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
