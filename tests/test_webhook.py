from fastapi.testclient import TestClient

from app.main import app


class DummyAgent:
    def __init__(self) -> None:
        self.calls = 0

    async def handle_incoming(self, message):
        self.calls += 1


def test_webhook_ignores_non_text():
    with TestClient(app) as client:
        payload = {
            "MsgId": "1",
            "FromUserName": "wxid_a",
            "MsgType": 3,
            "Content": "[image]",
            "IsGroup": False,
        }
        res = client.post("/webhook/gewechat", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "ignored"


def test_webhook_processes_text_and_deduplicates():
    with TestClient(app) as client:
        dummy = DummyAgent()
        client.app.state.agent = dummy

        payload = {
            "MsgId": "msg-001",
            "FromUserName": "wxid_a",
            "MsgType": 1,
            "Content": "你好",
            "IsGroup": False,
        }
        res1 = client.post("/webhook/gewechat", json=payload)
        res2 = client.post("/webhook/gewechat", json=payload)

        assert res1.status_code == 200
        assert res2.status_code == 200
        assert res1.json()["status"] == "processed"
        assert res2.json()["status"] == "processed"
        assert dummy.calls == 2


def test_webhook_secret_check():
    with TestClient(app) as client:
        client.app.state.bridge.webhook_secret = "abc"
        payload = {
            "MsgId": "1",
            "FromUserName": "wxid_a",
            "MsgType": 1,
            "Content": "你好",
            "IsGroup": False,
        }
        res = client.post("/webhook/gewechat", json=payload, headers={"X-Webhook-Secret": "bad"})
        assert res.status_code == 401
