from __future__ import annotations

from typing import Any

import httpx

from app.schemas import AgentReply


class OpenAIKnowledgeService:
    def __init__(self, api_key: str, base_url: str, model: str, vector_store_id: str, timeout: float = 30.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.vector_store_id = vector_store_id
        self.timeout = timeout

    async def answer(self, user_message: str) -> AgentReply:
        if not self.api_key or not self.vector_store_id:
            return AgentReply(
                answer="我暂时无法访问知识库，请稍后联系人工处理。",
                confidence=0.0,
                needs_handoff=True,
                reason="missing_openai_config",
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "你是个人微信知识助理。仅根据知识库回答，输出简洁中文（1-4句）。若不确定必须明确说明。",
                        }
                    ],
                },
                {"role": "user", "content": [{"type": "input_text", "text": user_message}]},
            ],
            "tools": [
                {
                    "type": "file_search",
                    "vector_store_ids": [self.vector_store_id],
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/responses", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        answer_text = data.get("output_text", "").strip()
        confidence = self._estimate_confidence(answer_text)

        return AgentReply(
            answer=answer_text or "我没找到可靠答案，建议转人工处理。",
            confidence=confidence,
            needs_handoff=False,
        )

    @staticmethod
    def _estimate_confidence(answer: str) -> float:
        if not answer:
            return 0.0
        low_confidence_tokens = ["不确定", "可能", "无法确认", "建议咨询人工", "不清楚"]
        if any(token in answer for token in low_confidence_tokens):
            return 0.3
        if len(answer) < 8:
            return 0.45
        return 0.8
