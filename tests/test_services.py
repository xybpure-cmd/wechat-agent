from pathlib import Path

from app.schemas import IncomingTextMessage
from app.services.agent import WechatKnowledgeAgent
from app.services.allowlist import ContactAllowlist
from app.services.dedup import MessageDeduplicator
from app.services.logger import InteractionLogger


class FakeBridge:
    def __init__(self) -> None:
        self.sent = []

    async def send_text(self, to_user: str, content: str) -> None:
        self.sent.append((to_user, content))


class FakeKnowledge:
    async def answer(self, user_message: str):
        from app.schemas import AgentReply

        return AgentReply(answer="知识库答案", confidence=0.9)


def test_allowlist_and_dedup(tmp_path: Path):
    bridge = FakeBridge()
    agent = WechatKnowledgeAgent(
        bridge=bridge,
        allowlist=ContactAllowlist({"wxid_ok"}),
        deduplicator=MessageDeduplicator(),
        knowledge_service=FakeKnowledge(),
        interaction_logger=InteractionLogger(tmp_path / "log.jsonl"),
        confidence_threshold=0.6,
    )

    msg = IncomingTextMessage(sender_id="wxid_ok", content="问题", message_id="m1", created_at="now")

    import asyncio

    first = asyncio.run(agent.handle_incoming(msg))
    second = asyncio.run(agent.handle_incoming(msg))

    assert first.needs_handoff is False
    assert second.reason == "duplicate"
    assert len(bridge.sent) == 1
