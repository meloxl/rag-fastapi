import json
import urllib.error
import urllib.request
from typing import Any

from app.config import (
    BAILIAN_API_BASE,
    BAILIAN_API_KEY,
    BAILIAN_APP_ID,
    BAILIAN_TIMEOUT,
    BAILIAN_WORKSPACE_ID,
)
from app.models import AskResponse, SourceItem


def _build_headers() -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {BAILIAN_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if BAILIAN_WORKSPACE_ID:
        headers["X-DashScope-WorkSpace"] = BAILIAN_WORKSPACE_ID
    return headers


def _extract_answer(payload: dict[str, Any]) -> str:
    output = payload.get("output") or {}
    answer = output.get("text") or output.get("answer") or payload.get("text")
    if not answer:
        raise ValueError(f"百炼响应中未找到回答内容：{payload}")
    return str(answer).strip()


def _extract_sources(payload: dict[str, Any], preview_len: int = 120) -> list[SourceItem]:
    output = payload.get("output") or {}
    candidates = (
        output.get("doc_references")
        or output.get("references")
        or output.get("documents")
        or payload.get("doc_references")
        or []
    )

    sources: list[SourceItem] = []
    if not isinstance(candidates, list):
        return sources

    for item in candidates:
        if not isinstance(item, dict):
            continue
        text = (
            item.get("text")
            or item.get("content")
            or item.get("chunk_text")
            or item.get("snippet")
            or ""
        )
        preview = str(text).replace("\n", " ").strip()
        if len(preview) > preview_len:
            preview = preview[:preview_len] + "..."

        source = (
            item.get("doc_name")
            or item.get("document_name")
            or item.get("title")
            or item.get("file_name")
            or "百炼云知识库"
        )
        category = item.get("category") or item.get("index_name") or "百炼云知识库"
        sources.append(SourceItem(category=str(category), source=str(source), preview=preview))

    return sources


def ask_bailian(question: str) -> AskResponse:
    if not BAILIAN_API_KEY:
        raise ValueError("调用百炼应用时，请设置 BAILIAN_API_KEY 或 DASHSCOPE_API_KEY")
    if not BAILIAN_APP_ID:
        raise ValueError("调用百炼应用时，请设置 BAILIAN_APP_ID")

    url = f"{BAILIAN_API_BASE}/apps/{BAILIAN_APP_ID}/completion"
    body = {
        "input": {"prompt": question},
        "parameters": {},
        "debug": {},
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=_build_headers(),
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=BAILIAN_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        error_msg = f"百炼应用调用失败：HTTP {exc.code} {detail}"
        
        # 诊断 403 错误
        if exc.code == 403:
            error_msg += (
                "\n\n【诊断信息】\n"
                "HTTP 403 表示访问被拒绝。常见原因：\n"
                f"1. API Key 已失效或被撤销 - 请在阿里云百炼控制台检查 BAILIAN_API_KEY\n"
                f"2. 应用 ID 不匹配 - 请确认 BAILIAN_APP_ID={BAILIAN_APP_ID} 与 API Key 对应\n"
                f"3. 子业务空间应用缺少 Workspace Header - 请确认 BAILIAN_WORKSPACE_ID={BAILIAN_WORKSPACE_ID or '未设置'}\n"
                f"4. 应用在云知识库中的权限被禁用 - 请在百炼平台检查应用配置\n"
                f"5. API Key 对应的账户配额已用尽 - 请检查账户余额和配额\n\n"
                f"【配置检查】\n"
                f"- API Base: {BAILIAN_API_BASE}\n"
                f"- App ID: {BAILIAN_APP_ID}\n"
                f"- Workspace ID: {BAILIAN_WORKSPACE_ID or '未设置'}\n"
                f"- API Key: {BAILIAN_API_KEY[:10]}...（已隐藏）"
            )
        
        raise RuntimeError(error_msg) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接百炼应用服务：{exc.reason}") from exc

    return AskResponse(
        question=question,
        answer=_extract_answer(payload),
        sources=_extract_sources(payload),
    )
