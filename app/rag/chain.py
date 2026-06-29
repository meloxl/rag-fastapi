from typing import Any

from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, RAG_PROVIDER, RETRIEVE_K
from app.models import AskResponse, SourceItem
from app.rag.bailian import ask_bailian


def _format_context(documents: list[Any]) -> str:
    blocks: list[str] = []
    for index, doc in enumerate(documents, start=1):
        category = doc.metadata.get("category", "未知")
        source = doc.metadata.get("source", "未知")
        question = doc.metadata.get("question", "")
        header = f"[{index}] 分类：{category} | 来源：{source}"
        if question:
            header += f" | 问题：{question}"
        blocks.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)


def _to_sources(documents: list[Any], preview_len: int = 120) -> list[SourceItem]:
    sources: list[SourceItem] = []
    for doc in documents:
        preview = doc.page_content.replace("\n", " ").strip()
        if len(preview) > preview_len:
            preview = preview[:preview_len] + "..."
        sources.append(
            SourceItem(
                category=doc.metadata.get("category", "未知"),
                source=doc.metadata.get("source", "未知"),
                preview=preview,
            )
        )
    return sources


def ask_question(question: str) -> AskResponse:
    if RAG_PROVIDER == "bailian":
        return ask_bailian(question)

    if RAG_PROVIDER != "local":
        raise ValueError("不支持的 RAG_PROVIDER，请设置为 local 或 bailian")

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    from app.rag.writer import load_vector_store

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

    vectordb = load_vector_store()
    retriever = vectordb.as_retriever(search_kwargs={"k": RETRIEVE_K})
    docs = retriever.invoke(question)

    if not LLM_API_KEY:
        raise ValueError("调用生成模型时，请设置 LLM_API_KEY 或 SILICONFLOW_LLM_API_KEY")

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=LLM_API_KEY,
        openai_api_base=LLM_API_BASE,
    )

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "context": _format_context(docs),
            "question": question,
        }
    )

    return AskResponse(
        question=question,
        answer=answer.strip(),
        sources=_to_sources(docs),
    )
