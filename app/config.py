import os
from pathlib import Path

from dotenv import load_dotenv


def _normalize_bailian_api_base(api_base: str) -> str:
    base = api_base.rstrip("/")
    if ".maas.aliyuncs.com" in base:
        return "https://dashscope.aliyuncs.com/api/v1"
    return base


def _normalize_credential(value: str) -> str:
    """去除首尾空白及常见引号，避免 .env 复制带入导致签名失败。"""
    return value.strip().strip('"').strip("'")


def _sync_ram_credentials_to_env() -> None:
    """将 .env 中 AK/SK 别名同步为标准环境变量，供 Credentials 默认凭据链读取。"""
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"):
        ak = _normalize_credential(os.getenv("AK", ""))
        if ak:
            os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"] = ak
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        sk = _normalize_credential(os.getenv("SK", ""))
        if sk:
            os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"] = sk


def _load_ram_access_key_id() -> str:
    raw = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID") or os.getenv("AK") or ""
    return _normalize_credential(raw)


def _load_ram_access_key_secret() -> str:
    raw = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET") or os.getenv("SK") or ""
    return _normalize_credential(raw)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
_sync_ram_credentials_to_env()

DOCS_DIR = os.getenv("DOCS_DIR", str(BASE_DIR / "docs"))
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))

# RAG 后端：local（本地 Chroma）| bailian（阿里云百炼应用/云知识库）
RAG_PROVIDER = os.getenv("RAG_PROVIDER", "local").strip().lower()

# 向量化：ollama（本地）| openai_compatible（硅基流动等 OpenAI 兼容 API）
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama").strip().lower()
EMBED_MODEL_ID = os.getenv(
    "EMBED_MODEL_ID",
    os.getenv("EMBED_MODEL", "nomic-embed-text"),
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# OpenAI 兼容 Embedding（硅基流动、OpenAI、其他厂商）
OPENAI_COMPATIBLE_API_BASE = os.getenv(
    "OPENAI_COMPATIBLE_API_BASE",
    os.getenv(
        "SILICONFLOW_API_BASE",
        os.getenv("SILICONFLOW_LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
    ),
).rstrip("/")
OPENAI_COMPATIBLE_API_KEY = os.getenv(
    "OPENAI_COMPATIBLE_API_KEY",
    os.getenv(
        "SILICONFLOW_API_KEY",
        os.getenv("SILICONFLOW_LLM_API_KEY", ""),
    ),
)

# 生成模型：OpenAI 兼容 Chat API（硅基流动、OpenAI、其他厂商）
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
LLM_API_BASE = os.getenv(
    "LLM_API_BASE",
    os.getenv("SILICONFLOW_LLM_BASE_URL", OPENAI_COMPATIBLE_API_BASE),
).rstrip("/")
LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    os.getenv("SILICONFLOW_LLM_API_KEY", OPENAI_COMPATIBLE_API_KEY),
)

# 阿里云百炼应用 API。百炼应用需在控制台绑定云知识库。
BAILIAN_API_BASE = _normalize_bailian_api_base(
    os.getenv(
        "BAILIAN_API_BASE",
        os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/api/v1"),
    )
)
BAILIAN_API_KEY = os.getenv(
    "BAILIAN_API_KEY",
    os.getenv("DASHSCOPE_API_KEY", ""),
)
BAILIAN_APP_ID = os.getenv("BAILIAN_APP_ID", "w6gsdtpq67")
BAILIAN_INDEX_ID = os.getenv("BAILIAN_INDEX_ID", BAILIAN_APP_ID)
BAILIAN_WORKSPACE_ID = os.getenv(
    "BAILIAN_WORKSPACE_ID",
    os.getenv("DASHSCOPE_WORKSPACE_ID", "ws-kjehcatf1uzce0xp"),
)
BAILIAN_TIMEOUT = float(os.getenv("BAILIAN_TIMEOUT", "60"))
# bailian 调用模式：retrieve（云知识库 Retrieve + LLM，默认）| app（百炼应用 completion，备用）
BAILIAN_CALL_MODE = os.getenv("BAILIAN_CALL_MODE", "retrieve").strip().lower()
BAILIAN_ENDPOINT = os.getenv("BAILIAN_ENDPOINT", "bailian.cn-beijing.aliyuncs.com")
BAILIAN_REGION_ID = os.getenv("BAILIAN_REGION_ID", "cn-beijing")
BAILIAN_RETRIEVE_ENABLE_RERANKING = os.getenv("BAILIAN_RETRIEVE_ENABLE_RERANKING", "true").lower() in (
    "1",
    "true",
    "yes",
)
# Retrieve 鉴权由 Credentials 默认凭据链提供（见 app/rag/aliyun_credentials.py），
# 不在业务代码中直接读取 Secret；以下仅用于诊断是否已配置环境变量。
ALIBABA_CLOUD_ACCESS_KEY_ID = _load_ram_access_key_id()
ALIBABA_CLOUD_ACCESS_KEY_SECRET = _load_ram_access_key_secret()

RETRIEVE_K = int(os.getenv("RETRIEVE_K", "3"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

ALLOWED_UPLOAD_SUFFIX = {".md"}

# 兼容旧引用
EMBED_MODEL = EMBED_MODEL_ID
