from datetime import datetime, timezone
from hashlib import sha256

from pydantic import BaseModel, Field


class GewechatWebhookEvent(BaseModel):
    msg_id: str | None = Field(default=None, alias="MsgId")
    from_user: str = Field(alias="FromUserName")
    to_user: str | None = Field(default=None, alias="ToUserName")
    msg_type: str | int = Field(alias="MsgType")
    content: str = Field(default="", alias="Content")
    create_time: int | None = Field(default=None, alias="CreateTime")
    is_group: bool = Field(default=False, alias="IsGroup")

    model_config = {"populate_by_name": True, "extra": "allow"}

    def dedup_key(self) -> str:
        if self.msg_id:
            return self.msg_id
        payload = f"{self.from_user}|{self.content}|{self.create_time or 0}"
        return sha256(payload.encode("utf-8")).hexdigest()

    def created_at_iso(self) -> str:
        if self.create_time:
            dt = datetime.fromtimestamp(self.create_time, tz=timezone.utc)
            return dt.isoformat()
        return datetime.now(tz=timezone.utc).isoformat()


class IncomingTextMessage(BaseModel):
    sender_id: str
    content: str
    message_id: str
    created_at: str


class AgentReply(BaseModel):
    answer: str
    confidence: float
    needs_handoff: bool = False
    reason: str | None = None
