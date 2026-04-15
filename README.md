# Personal WeChat Knowledge Agent (MVP)

一个最小可用版本：用于 **微信 1 对 1 文本问答**，基于你自己的 Markdown 知识库回答。

## 1) v1 支持范围

✅ 支持
- 1:1 私聊文本消息
- 联系人白名单
- 消息去重
- OpenAI file_search 检索回答
- 低置信度转人工提示
- 交互日志记录

❌ 不支持
- 群聊
- 语音
- 图片

---

## 2) 目录说明

```text
app/                  FastAPI 服务
scripts/upload_kb.py  上传 data/kb/*.md 到 OpenAI 向量库
data/kb/              你的知识库 Markdown 文件
tests/                基础测试
```

---

## 3) 环境变量（先看这个）

复制模板：

```bash
cp .env.example .env
```

### A. 服务运行必须（Webhook + 自动回复）

- `OPENAI_API_KEY`
- `OPENAI_VECTOR_STORE_ID`
- `GEWECHAT_API_BASE`
- `ALLOWED_CONTACTS`（逗号分隔，例如 `wxid_a,wxid_b`）

### B. 建议配置

- `GEWECHAT_TOKEN`
- `GEWECHAT_WEBHOOK_SECRET`
- `OPENAI_MODEL`
- `CONFIDENCE_THRESHOLD`
- `INTERACTION_LOG_PATH`

### C. 上传脚本相关

- `KB_MANIFEST_PATH`（可选，默认 `data/.kb_upload_manifest.json`）
- `OPENAI_BASE_URL`（可选，默认 `https://api.openai.com/v1`）

---

## 4) 启动服务

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Webhook 地址：`POST /webhook/gewechat`

---

## 5) 如何上传你的 Markdown 知识库（最简单步骤）

1. 把你的 `.md` 文件放到 `data/kb/`（可分子目录）。
2. 先预览会上传哪些文件：

   ```bash
   python scripts/upload_kb.py --dry-run
   ```

3. 正式上传：

   ```bash
   python scripts/upload_kb.py
   ```

4. 下次再执行同一命令时：
   - 没改过的文件会自动跳过
   - 新增/修改的文件会上传
   - 本地删除的文件会从映射里清理

---

## 6) Gewechat webhook 最小字段示例

```json
{
  "MsgId": "123",
  "FromUserName": "wxid_xxx",
  "MsgType": 1,
  "Content": "问题文本",
  "CreateTime": 1710000000,
  "IsGroup": false
}
```

---

## 7) 说明

- 所有密钥都走环境变量。
- 当前去重是内存级别，生产建议改 Redis/DB。
- 桥接层已模块化，后续可替换 Gewechat。
