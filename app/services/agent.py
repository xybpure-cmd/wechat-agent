from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import AgentReply, IncomingTextMessage
from app.services.allowlist import ContactAllowlist
from app.services.bridge import WechatBridge
from app.services.dedup import MessageDeduplicator
from app.services.logger import InteractionLogger
from app.services.openai_client import OpenAIKnowledgeService


class WechatKnowledgeAgent:
    def __init__(
        self,
        bridge: WechatBridge,
        allowlist: ContactAllowlist,
        deduplicator: MessageDeduplicator,
        knowledge_service: OpenAIKnowledgeService,
        interaction_logger: InteractionLogger,
        confidence_threshold: float,
    ) -> None:
        self.bridge = bridge
        self.allowlist = allowlist
        self.deduplicator = deduplicator
        self.knowledge_service = knowledge_service
        self.interaction_logger = interaction_logger
        self.confidence_threshold = confidence_threshold

    async def handle_incoming(self, message: IncomingTextMessage) -> AgentReply:
        if not self.allowlist.is_allowed(message.sender_id):
            reply = AgentReply(
                answer="当前账号未开通自动回复，请联系管理员。",
                confidence=1.0,
                needs_handoff=True,
                reason="contact_not_allowlisted",
            )
            self._log(message, reply)
            return reply

        if self.deduplicator.is_duplicate(message.message_id):
            reply = AgentReply(answer="", confidence=1.0, needs_handoff=False, reason="duplicate")
            self._log(message, reply)
            return reply

        reply = await self.knowledge_service.answer(message.content)
        if reply.confidence < self.confidence_threshold:
            reply.needs_handoff = True
            reply.reason = reply.reason or "low_confidence"
            reply.answer = "这个问题我把握不高，已为你转人工跟进。"

        if reply.answer:
            await self.bridge.send_text(message.sender_id, reply.answer)

        self._log(message, reply)
        return reply

    def _log(self, message: IncomingTextMessage, reply: AgentReply) -> None:
        self.interaction_logger.log(
            {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "sender_id": message.sender_id,
                "message_id": message.message_id,
                "question": message.content,
                "answer": reply.answer,
                "confidence": reply.confidence,
                "needs_handoff": reply.needs_handoff,
                "reason": reply.reason,
            }
        )
