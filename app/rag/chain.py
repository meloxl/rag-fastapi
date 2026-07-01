from typing import Any

from app.config import (
    BAILIAN_CALL_MODE,
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    RAG_PROVIDER,
    RETRIEVE_K,
)
from app.models import AskResponse, SourceItem
from app.rag.bailian import ask_bailian
from app.rag.bailian_retrieve import RetrievedChunk, retrieve_chunks


def _format_context(documents: list[Any]) -> str:
    blocks: list[str] = []
    for index, doc in enumerate(documents, start=1):
        if isinstance(doc, RetrievedChunk):
            category = doc.metadata.get("category") or _guess_category(doc.metadata)
            source = (
                doc.metadata.get("doc_name")
                or doc.metadata.get("title")
                or doc.metadata.get("hier_title")
                or doc.metadata.get("source")
                or "百炼云知识库"
            )
            question = doc.metadata.get("question", "")
            content = doc.text
        else:
            category = doc.metadata.get("category", "未知")
            source = doc.metadata.get("source", "未知")
            question = doc.metadata.get("question", "")
            content = doc.page_content

        header = f"[{index}] 分类：{category} | 来源：{source}"
        if question:
            header += f" | 问题：{question}"
        blocks.append(f"{header}\n{content}")
    return "\n\n---\n\n".join(blocks)


def _guess_category(metadata: dict[str, Any]) -> str:
    for key in ("doc_name", "title", "hier_title", "file_path"):
        value = str(metadata.get(key, ""))
        for label in ("单身", "恋爱", "已婚"):
            if label in value:
                return label
    return "百炼云知识库"


def _to_sources(documents: list[Any], preview_len: int = 120) -> list[SourceItem]:
    sources: list[SourceItem] = []
    for doc in documents:
        if isinstance(doc, RetrievedChunk):
            preview = doc.text.replace("\n", " ").strip()
            category = doc.metadata.get("category") or _guess_category(doc.metadata)
            source = (
                doc.metadata.get("doc_name")
                or doc.metadata.get("title")
                or doc.metadata.get("hier_title")
                or "百炼云知识库"
            )
        else:
            preview = doc.page_content.replace("\n", " ").strip()
            category = doc.metadata.get("category", "未知")
            source = doc.metadata.get("source", "未知")

        if len(preview) > preview_len:
            preview = preview[:preview_len] + "..."
        sources.append(SourceItem(category=str(category), source=str(source), preview=preview))
    return sources


def _generate_answer(question: str, context_docs: list[Any]) -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    if not LLM_API_KEY:
        raise ValueError("调用生成模型时，请设置 LLM_API_KEY 或 SILICONFLOW_LLM_API_KEY")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一位专业的恋爱关系顾问。请严格根据下面提供的知识库内容回答用户问题。"
                "如果知识库中没有相关信息，请明确说明「知识库中未找到相关内容」，不要编造。"
                "回答应专业、温和、实用，不要虚构课程或链接。",
            ),
            (
                "human",
                "知识库内容：\n{context}\n\n用户问题：{question}",
            ),
        ]
    )

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=LLM_API_KEY,
        openai_api_base=LLM_API_BASE,
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {
            "context": _format_context(context_docs),
            "question": question,
        }
    ).strip()


def ask_bailian_retrieve(question: str) -> AskResponse:
    chunks = retrieve_chunks(question, top_k=RETRIEVE_K)
    answer = _generate_answer(question, chunks)
    return AskResponse(
        question=question,
        answer=answer,
        sources=_to_sources(chunks),
    )


def ask_question(question: str) -> AskResponse:
    if RAG_PROVIDER == "bailian":
        if BAILIAN_CALL_MODE == "app":
            return ask_bailian(question)
        if BAILIAN_CALL_MODE == "retrieve":
            return ask_bailian_retrieve(question)
        raise ValueError("不支持的 BAILIAN_CALL_MODE，请设置为 retrieve 或 app")

    if RAG_PROVIDER != "local":
        raise ValueError("不支持的 RAG_PROVIDER，请设置为 local 或 bailian")

    from app.rag.writer import load_vector_store

    vectordb = load_vector_store()
    retriever = vectordb.as_retriever(search_kwargs={"k": RETRIEVE_K})
    docs = retriever.invoke(question)
    answer = _generate_answer(question, docs)

    return AskResponse(
        question=question,
        answer=answer,
        sources=_to_sources(docs),
    )
