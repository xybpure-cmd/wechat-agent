from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from app.config import get_settings
from app.services.agent import WechatKnowledgeAgent
from app.services.allowlist import ContactAllowlist
from app.services.bridge import GewechatBridge
from app.services.dedup import MessageDeduplicator
from app.services.logger import InteractionLogger
from app.services.openai_client import OpenAIKnowledgeService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    http_client = httpx.AsyncClient()

    bridge = GewechatBridge(
        api_base=settings.gewechat_api_base,
        token=settings.gewechat_token,
        webhook_secret=settings.gewechat_webhook_secret,
        http_client=http_client,
    )
    app.state.bridge = bridge
    app.state.agent = WechatKnowledgeAgent(
        bridge=bridge,
        allowlist=ContactAllowlist(settings.allowed_contact_set),
        deduplicator=MessageDeduplicator(),
        knowledge_service=OpenAIKnowledgeService(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            vector_store_id=settings.openai_vector_store_id,
        ),
        interaction_logger=InteractionLogger(settings.interaction_log_path),
        confidence_threshold=settings.confidence_threshold,
    )

    yield
    await http_client.aclose()


app = FastAPI(title="Personal WeChat Knowledge Agent", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/gewechat")
async def gewechat_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> dict[str, str]:
    bridge: GewechatBridge = request.app.state.bridge
    if not bridge.verify_signature(x_webhook_secret):
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    payload = await request.json()
    msg = bridge.parse_incoming_text(payload)
    if msg is None:
        return {"status": "ignored"}

    await request.app.state.agent.handle_incoming(msg)
    return {"status": "processed"}
