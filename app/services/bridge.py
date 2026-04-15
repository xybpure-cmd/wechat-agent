from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import GewechatWebhookEvent, IncomingTextMessage


class WechatBridge(ABC):
    @abstractmethod
    def parse_incoming_text(self, payload: dict) -> IncomingTextMessage | None:
        raise NotImplementedError

    @abstractmethod
    async def send_text(self, to_user: str, content: str) -> None:
        raise NotImplementedError


class GewechatBridge(WechatBridge):
    def __init__(self, api_base: str, token: str, webhook_secret: str, http_client) -> None:
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.webhook_secret = webhook_secret
        self.http_client = http_client

    def verify_signature(self, incoming_secret: str | None) -> bool:
        if not self.webhook_secret:
            return True
        return incoming_secret == self.webhook_secret

    def parse_incoming_text(self, payload: dict) -> IncomingTextMessage | None:
        event = GewechatWebhookEvent.model_validate(payload)
        # v1 only supports 1:1 text chat
        if event.is_group:
            return None
        if str(event.msg_type) != "1":  # text
            return None
        content = (event.content or "").strip()
        if not content:
            return None
        return IncomingTextMessage(
            sender_id=event.from_user,
            content=content,
            message_id=event.dedup_key(),
            created_at=event.created_at_iso(),
        )

    async def send_text(self, to_user: str, content: str) -> None:
        if not self.api_base:
            return
        await self.http_client.post(
            f"{self.api_base}/message/sendText",
            json={"toWxid": to_user, "content": content},
            headers={"Authorization": f"Bearer {self.token}"} if self.token else None,
            timeout=20,
        )
