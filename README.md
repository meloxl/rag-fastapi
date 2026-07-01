# 恋爱知识 RAG 问答

基于 **FastAPI + LangChain + Chroma + OpenAI 兼容模型 API** 的恋爱知识库问答服务。支持两种 RAG 后端：

| 模式 | 说明 |
|------|------|
| `local`（默认） | 本地 `docs/` + Chroma 向量库，自建 ETL 与检索 |
| `bailian` | 阿里云百炼云知识库「恋爱大师集合」，默认 **Retrieve API 检索 + LLM 生成** |

## 前置条件

1. **Python 3.11**（与 FastAPI 推荐环境一致；见 `pyproject.toml`、`.python-version`）
2. 硅基流动或其他 OpenAI 兼容服务的 API Key（生成模型；`local` 模式向量化也可使用）
3. `local` 模式若使用 Ollama 向量化，需安装 [Ollama](https://ollama.com/) 并拉取 `nomic-embed-text`
4. `bailian` 模式额外需要：百炼云知识库 IndexId、RAM AccessKey（AK/SK），详见下方配置

## 项目文档

需求与设计说明（供后续扩展与 AI 参考）见 [`documentation/`](documentation/)：

- [需求分析.md](documentation/需求分析.md) — 背景、功能边界、验收用例、扩展方向
- [方案设计.md](documentation/方案设计.md) — 架构、模块职责、API、配置、扩展接入指南
- [百炼_403问题排查指南.md](documentation/百炼_403问题排查指南.md) — 百炼应用 API（备用模式）403 排查

## 安装与启动

```bash
cd rag-fastapi
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env   # 按需修改模型与 RAG 后端配置
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://127.0.0.1:8000/docs

## 使用流程

### 1. 健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 2. 构建向量库（`local` 模式首次必做）

```bash
curl -X POST http://127.0.0.1:8000/build_kb
```

`bailian` 模式下无需调用 `/build_kb`；文档在百炼控制台维护。

### 2.1 切换到百炼云知识库（推荐：Retrieve 模式）

默认 `RAG_PROVIDER=local`。使用百炼云知识库时，在 `.env` 中配置：

```env
RAG_PROVIDER=bailian
BAILIAN_CALL_MODE=retrieve          # 默认，可省略

# 云知识库 Retrieve（2023-12-29）
BAILIAN_INDEX_ID=your-index-id      # 控制台「恋爱大师集合」知识库 ID
BAILIAN_WORKSPACE_ID=ws-kjehcatf1uzce0xp
AK=your-ram-access-key-id
SK=your-ram-access-key-secret

# 生成模型（与 local 模式相同）
LLM_MODEL=Qwen/Qwen3-VL-8B-Instruct
LLM_API_KEY=your-siliconflow-api-key
LLM_API_BASE=https://api.siliconflow.cn/v1
```

**调用链路**：百炼 Retrieve 检索云知识库切片 → 硅基流动等 LLM 生成回答。

**凭证说明**：

- `AK`/`SK`：RAM AccessKey，用于 Retrieve API（与 DashScope `sk-` Key 不同）
- `BAILIAN_INDEX_ID`：知识库 ID，需在百炼控制台获取（**通常与应用 App ID 不同**）
- `LLM_API_KEY`：OpenAI 兼容 Chat API，用于最终回答生成

诊断连通性：

```bash
python diagnose_bailian.py
# 或
curl http://127.0.0.1:8000/diagnostics
```

### 2.2 百炼应用 API（备用）

若需回退到百炼应用 completion API（曾遇 `App.AccessDenied` 问题，见排查指南）：

```env
RAG_PROVIDER=bailian
BAILIAN_CALL_MODE=app
BAILIAN_APP_ID=w6gsdtpq67
BAILIAN_WORKSPACE_ID=ws-kjehcatf1uzce0xp
BAILIAN_API_KEY=your-dashscope-api-key
BAILIAN_API_BASE=https://dashscope.aliyuncs.com/api/v1
```

### 3. 提问

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "恋爱中如何有效处理双方的争吵？"}'
```

如果返回 500/503，优先检查：

- **local 模式**：是否已 `POST /build_kb`；`LLM_API_KEY`、embedding 配置是否正确
- **bailian retrieve 模式**：`AK`/`SK`、`BAILIAN_INDEX_ID` 是否正确；运行 `python diagnose_bailian.py`
- **bailian app 模式**：`BAILIAN_API_KEY` 是否有效；参考 [百炼_403问题排查指南.md](documentation/百炼_403问题排查指南.md)

```bash
curl http://127.0.0.1:8000/health
python -c "from app.config import LLM_MODEL, LLM_API_BASE, RAG_PROVIDER, BAILIAN_CALL_MODE; print(RAG_PROVIDER, BAILIAN_CALL_MODE, LLM_MODEL, LLM_API_BASE)"
```

`local` 模式下若修改过 `EMBED_PROVIDER` 或 `EMBED_MODEL_ID`，需重新 `POST /build_kb`。

### 4. 上传新文档（`local` 模式，可选）

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@docs/恋爱常见问题和回答 - 单身篇.md"
```

上传后需再次调用 `POST /build_kb` 重建向量库。

## 项目结构

```
app/
├── main.py              # FastAPI 路由
├── config.py            # 配置
├── models.py            # 请求/响应模型
└── rag/
    ├── reader.py        # DocumentReader：读取 docs/*.md
    ├── transformer.py   # DocumentTransformer：Markdown 标题切分
    ├── writer.py        # DocumentWriter：Chroma 向量存储
    ├── embeddings.py    # Embedding 工厂
    ├── bailian_retrieve.py  # 百炼云知识库 Retrieve（bailian 默认）
    ├── bailian.py       # 百炼应用 completion（bailian 备用）
    ├── diagnostics.py   # 百炼 RAG 诊断
    └── chain.py         # 查询增强：检索 + Prompt + LLM
docs/                    # 内置恋爱知识 Markdown（local 模式）
chroma_db/               # 向量库（local 模式，自动生成）
diagnose_bailian.py      # 百炼命令行诊断脚本
documentation/           # 需求/设计文档
```

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/build_kb` | 构建本地向量库（local） |
| POST | `/ask` | 恋爱知识问答 |
| POST | `/upload` | 上传 Markdown（local） |
| GET | `/diagnostics` | 百炼 RAG 诊断（bailian） |

## 验收建议

| 问题 | 期望来源 |
|------|----------|
| 如何在社交场合主动结识心仪异性？ | 单身篇 |
| 恋爱中如何有效处理双方的争吵？ | 恋爱篇 |
| 婚后如何平衡工作与家庭责任？ | 已婚篇 |

检查返回的 `sources` 字段是否指向对应篇章（`bailian` 模式下为云知识库文档名）。

## 配置项

见 `.env.example`。

### 向量化（`local` 模式，切换后需重新 `POST /build_kb`）

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

也可使用别名 `SILICONFLOW_API_KEY`、`SILICONFLOW_API_BASE`。

### RAG 与百炼

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PROVIDER` | `local` | RAG 后端：`local` / `bailian` |
| `BAILIAN_CALL_MODE` | `retrieve` | bailian 子模式：`retrieve` / `app`（备用） |
| `BAILIAN_INDEX_ID` | 同 `BAILIAN_APP_ID` | 云知识库 IndexId（retrieve 必填） |
| `BAILIAN_WORKSPACE_ID` | `ws-kjehcatf1uzce0xp` | 百炼业务空间 ID |
| `AK` / `SK` | — | RAM AccessKey（retrieve 必填） |
| `BAILIAN_ENDPOINT` | `bailian.cn-beijing.aliyuncs.com` | 百炼 OpenAPI 端点 |
| `BAILIAN_RETRIEVE_ENABLE_RERANKING` | `true` | Retrieve 是否开启重排序 |
| `BAILIAN_APP_ID` | `w6gsdtpq67` | 百炼应用 ID（app 模式） |
| `BAILIAN_API_KEY` | — | DashScope API Key（app 模式） |
| `BAILIAN_API_BASE` | `https://dashscope.aliyuncs.com/api/v1` | 百炼应用 API 地址（app 模式） |

### 生成模型（local 与 bailian retrieve 共用）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_MODEL` | `Qwen/Qwen3-VL-8B-Instruct` | 生成模型 |
| `LLM_API_BASE` | `OPENAI_COMPATIBLE_API_BASE` | 生成模型 API 地址 |
| `LLM_API_KEY` | `OPENAI_COMPATIBLE_API_KEY` | 生成模型 API Key |
| `RETRIEVE_K` | `3` | 检索条数（local Chroma / bailian Retrieve） |
| `LLM_TEMPERATURE` | `0` | 生成温度 |
