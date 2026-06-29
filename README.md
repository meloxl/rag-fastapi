# 恋爱知识 RAG 问答

基于 **FastAPI + LangChain + Chroma + OpenAI 兼容模型 API** 的恋爱知识库问答服务。知识文档位于 `docs/`，支持上传 Markdown 后重建向量库。

## 前置条件

1. **Python 3.11**（与 FastAPI 推荐环境一致；见 `pyproject.toml`、`.python-version`）
2. 硅基流动或其他 OpenAI 兼容服务的 API Key
3. 如果使用本地 Ollama 做向量化，需要安装 [Ollama](https://ollama.com/) 并拉取 `nomic-embed-text`

## 项目文档

需求与设计说明（供后续扩展与 AI 参考）见 [`documentation/`](documentation/)：

- [需求分析.md](documentation/需求分析.md) — 背景、功能边界、验收用例、扩展方向
- [方案设计.md](documentation/方案设计.md) — 架构、模块职责、API、配置、扩展接入指南

## 安装与启动

```bash
cd rag-fastapi
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env   # 可选，按需修改模型名
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://127.0.0.1:8000/docs

## 使用流程

### 1. 健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 2. 构建向量库（首次必做）

```bash
curl -X POST http://127.0.0.1:8000/build_kb
```

### 2.1 切换到百炼云知识库

默认 `RAG_PROVIDER=local`，继续使用本地 Chroma 检索 + LLM 生成。若要使用阿里云百炼应用绑定的云知识库“恋爱大师集合”，在 `.env` 中配置：

```env
RAG_PROVIDER=bailian
BAILIAN_APP_ID=w6gsdtpq67
BAILIAN_WORKSPACE_ID=ws-kjehcatf1uzce0xp
BAILIAN_API_KEY=your-dashscope-api-key
BAILIAN_API_BASE=https://dashscope.aliyuncs.com/api/v1
```

百炼模式下 `/ask` 会直接调用百炼应用 API，跳过本地 `chroma_db` 检查；`/build_kb` 仍保留为本地模式专用。

### 3. 提问

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "恋爱中如何有效处理双方的争吵？"}'
```

如果这里返回 500/503，优先检查生成模型 API 配置：

```bash
curl http://127.0.0.1:8000/health
python -c "from app.config import LLM_MODEL, LLM_API_BASE; print(LLM_MODEL, LLM_API_BASE)"
```

`LLM_MODEL` 默认使用 `Qwen/Qwen3-VL-8B-Instruct`；需要配置 `LLM_API_KEY`，也可以复用
`OPENAI_COMPATIBLE_API_KEY` / `SILICONFLOW_API_KEY`。如果修改过 `EMBED_PROVIDER` 或
`EMBED_MODEL_ID`，需要重新调用 `POST /build_kb`，否则旧向量库可能和当前 embedding 模型不匹配。

### 4. 上传新文档（可选）

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@docs/恋爱常见问题和回答 - 单身篇.md"
```

上传后需再次调用 `POST /build_kb` 重建向量库。

## 项目结构

```
app/
├── main.py           # FastAPI 路由
├── config.py         # 配置
├── models.py         # 请求/响应模型
└── rag/
    ├── reader.py     # DocumentReader：读取 docs/*.md
    ├── transformer.py# DocumentTransformer：Markdown 标题切分
    ├── writer.py     # DocumentWriter：Chroma 向量存储
    └── chain.py      # 查询增强：检索 + Prompt + LLM
docs/                 # 内置恋爱知识 Markdown
chroma_db/            # 向量库（自动生成）
```

## 验收建议

| 问题 | 期望来源 |
|------|----------|
| 如何在社交场合主动结识心仪异性？ | 单身篇 |
| 恋爱中如何有效处理双方的争吵？ | 恋爱篇 |
| 婚后如何平衡工作与家庭责任？ | 已婚篇 |

检查返回的 `sources` 字段是否指向对应篇章。

## 配置项

见 `.env.example`。向量化支持两种 **EMBED_PROVIDER**（切换后需重新 `POST /build_kb`）：

| EMBED_PROVIDER | 场景 | 关键变量 |
|----------------|------|----------|
| `ollama`（默认） | 本地 Ollama | `EMBED_MODEL_ID=nomic-embed-text`，需 `ollama pull` |
| `openai_compatible` | 硅基流动等 | `EMBED_MODEL_ID=Qwen/Qwen3-Embedding-8B`，`OPENAI_COMPATIBLE_API_KEY` |

硅基流动示例：

```env
EMBED_PROVIDER=openai_compatible
EMBED_MODEL_ID=Qwen/Qwen3-Embedding-8B
OPENAI_COMPATIBLE_API_BASE=https://api.siliconflow.cn/v1
OPENAI_COMPATIBLE_API_KEY=your-api-key
```

也可使用别名 `SILICONFLOW_API_KEY`、`SILICONFLOW_API_BASE`。`siliconflow` 作为 provider 名与 `openai_compatible` 等价。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PROVIDER` | `local` | RAG 后端：`local` / `bailian` |
| `BAILIAN_APP_ID` | `w6gsdtpq67` | 百炼应用 ID，需在控制台绑定云知识库 |
| `BAILIAN_WORKSPACE_ID` | `ws-kjehcatf1uzce0xp` | 百炼子业务空间 ID，用于 `X-DashScope-WorkSpace` 请求头 |
| `BAILIAN_API_KEY` | — | 百炼 / DashScope API Key |
| `BAILIAN_API_BASE` | `https://dashscope.aliyuncs.com/api/v1` | 百炼应用 API 地址 |
| `LLM_MODEL` | `Qwen/Qwen3-VL-8B-Instruct` | 生成模型（OpenAI 兼容 Chat API） |
| `LLM_API_BASE` | `OPENAI_COMPATIBLE_API_BASE` | 生成模型 API 地址 |
| `LLM_API_KEY` | `OPENAI_COMPATIBLE_API_KEY` | 生成模型 API Key |
| `EMBED_MODEL_ID` | `nomic-embed-text` | 向量模型 ID |
| `RETRIEVE_K` | `3` | 检索条数 |
