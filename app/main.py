import os

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import DOCS_DIR, LLM_MODEL
from app.rag.embeddings import get_embed_info
from app.models import (
    AskRequest,
    AskResponse,
    BuildKbResponse,
    HealthResponse,
    UploadResponse,
)
from app.rag.chain import ask_question
from app.rag.reader import list_markdown_files, load_documents, sanitize_upload_filename
from app.rag.transformer import split_documents
from app.rag.writer import build_vector_store, is_kb_built

app = FastAPI(
    title="恋爱知识 RAG 问答",
    description="基于本地 Markdown 知识库的恋爱关系问答服务",
    version="1.0.0",
)


@app.on_event("startup")
def ensure_docs_dir() -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)


@app.get("/health", response_model=HealthResponse, summary="健康检查")
def health() -> HealthResponse:
    embed_info = get_embed_info()
    return HealthResponse(
        status="ok",
        kb_built=is_kb_built(),
        docs_count=len(list_markdown_files()),
        embed_provider=embed_info["embed_provider"],
        embed_model=embed_info["embed_model"],
        llm_model=LLM_MODEL,
    )


@app.post("/build_kb", response_model=BuildKbResponse, summary="构建向量知识库")
def build_kb() -> BuildKbResponse:
    documents = load_documents()
    if not documents:
        raise HTTPException(status_code=400, detail=f"知识目录 {DOCS_DIR} 中没有 .md 文档")

    chunks = split_documents(documents)
    if not chunks:
        raise HTTPException(status_code=400, detail="文档切分后没有可用文本块")

    try:
        build_vector_store(chunks)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BuildKbResponse(
        status="success",
        message="向量库构建完成",
        chunk_count=len(chunks),
    )


@app.post("/ask", response_model=AskResponse, summary="恋爱知识问答")
def ask(body: AskRequest) -> AskResponse:
    if not is_kb_built():
        raise HTTPException(status_code=400, detail="请先调用 POST /build_kb 构建知识库")

    try:
        return ask_question(body.question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        message = str(exc)
        lower_message = message.lower()
        if (
            "connection refused" in lower_message
            or "failed to connect" in lower_message
            or "all connection attempts failed" in lower_message
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    f"无法连接生成模型服务（{LLM_MODEL}）。"
                    "请确认 LLM_API_BASE / SILICONFLOW_LLM_BASE_URL 配置正确。"
                ),
            ) from exc
        if "model" in lower_message and "not found" in lower_message:
            raise HTTPException(
                status_code=400,
                detail=f"生成模型不存在或当前账号无权限访问：{LLM_MODEL}。",
            ) from exc
        raise HTTPException(status_code=500, detail=f"问答失败：{exc}") from exc


@app.post("/upload", response_model=UploadResponse, summary="上传 Markdown 到知识库")
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    try:
        safe_name = sanitize_upload_filename(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    save_path = os.path.join(DOCS_DIR, safe_name)
    with open(save_path, "wb") as handle:
        handle.write(content)

    return UploadResponse(
        status="success",
        message="文件上传成功，请调用 POST /build_kb 重建向量库后生效",
        filename=safe_name,
    )
