"""向量化模型工厂：支持本地 Ollama 与 OpenAI 兼容 API（如硅基流动）。"""

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from app.config import (
    EMBED_MODEL_ID,
    EMBED_PROVIDER,
    OLLAMA_BASE_URL,
    OPENAI_COMPATIBLE_API_BASE,
    OPENAI_COMPATIBLE_API_KEY,
)

SUPPORTED_EMBED_PROVIDERS = frozenset({"ollama", "openai_compatible", "siliconflow"})


def get_embeddings() -> Embeddings:
    """按 EMBED_PROVIDER 创建 LangChain Embeddings 实例。"""
    provider = EMBED_PROVIDER
    if provider == "siliconflow":
        provider = "openai_compatible"

    if provider == "ollama":
        return OllamaEmbeddings(
            model=EMBED_MODEL_ID,
            base_url=OLLAMA_BASE_URL,
        )

    if provider == "openai_compatible":
        if not OPENAI_COMPATIBLE_API_KEY:
            raise ValueError(
                "使用 openai_compatible / siliconflow 向量化时，"
                "请设置 OPENAI_COMPATIBLE_API_KEY 或 SILICONFLOW_API_KEY"
            )
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=EMBED_MODEL_ID,
            openai_api_key=OPENAI_COMPATIBLE_API_KEY,
            openai_api_base=OPENAI_COMPATIBLE_API_BASE,
            check_embedding_ctx_length=False,
        )

    raise ValueError(
        f"不支持的 EMBED_PROVIDER={EMBED_PROVIDER!r}，"
        f"可选：{', '.join(sorted(SUPPORTED_EMBED_PROVIDERS))}"
    )


def get_embed_info() -> dict[str, str]:
    """供 /health 展示当前向量化配置。"""
    provider = EMBED_PROVIDER
    if provider == "siliconflow":
        provider = "openai_compatible"
    return {
        "embed_provider": provider,
        "embed_model": EMBED_MODEL_ID,
    }
