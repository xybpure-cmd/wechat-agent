# 微信知识助手（GitHub 版）快速开始

这份说明给**非技术用户**。  
你只需要按步骤准备文件，后面交给开发者或自动化流程部署即可。

---

## 1. 这个项目是做什么的？

这个项目是一个“微信自动问答助手”：

- 你在微信里收到别人提问
- 系统会去你的知识文档里找答案
- 然后自动回复简短中文
- 如果它不确定，会提示转人工

简单说：**它会按你写的资料自动回消息**。

---

## 2. 你需要准备哪些文件？

你主要准备两类文件：

### A) 知识内容文件（最重要）

位置：`data/kb/`

建议一个主题一个文件，例如：

- `data/kb/faq_project.md`
- `data/kb/faq_identity.md`
- `data/kb/faq_contact.md`

文件格式建议：

```markdown
## Q1：问题
A：答案

## Q2：问题
A：答案
```

> 你可以先用仓库里现成的示例文件，直接改文字即可。

### B) 环境变量模板文件

文件：`.env.example`

你后续需要把它复制为 `.env`，并填写自己的真实值（比如密钥、接口地址）。

---

## 3. 我的知识文档应该放哪里？

请把你的 Markdown 文档放在：

- `data/kb/`

可以放子目录，例如：

- `data/kb/product/basic.md`
- `data/kb/product/price.md`

系统会读取这个目录下的 `.md` 文件。

---

## 4. 之后你会用到哪些环境变量？

下面这些是你后续部署时要准备的：

### 必填（建议优先准备）

- `OPENAI_API_KEY`：OpenAI 密钥
- `OPENAI_VECTOR_STORE_ID`：OpenAI 知识库（向量库）ID
- `GEWECHAT_API_BASE`：Gewechat 服务地址
- `ALLOWED_CONTACTS`：允许自动回复的微信 ID（多个用逗号分隔）

### 建议填写

- `GEWECHAT_TOKEN`
- `GEWECHAT_WEBHOOK_SECRET`
- `OPENAI_MODEL`
- `CONFIDENCE_THRESHOLD`
- `INTERACTION_LOG_PATH`
- `KB_MANIFEST_PATH`

---

## 5. 你现在可以先做什么？

只做这 3 件事就够了：

1. 把你的问答内容写进 `data/kb/*.md`
2. 确认 `.env.example` 里你能提供哪些变量
3. 把仓库提交到 GitHub

完成后，把仓库链接给开发者或自动化部署流程即可。
