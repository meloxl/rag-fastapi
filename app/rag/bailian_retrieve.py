"""百炼云知识库 Retrieve API（2023-12-29）检索客户端。

鉴权：通过 alibabacloud-credentials 默认凭据链获取 RAM AccessKey，
不在本模块向 SDK 显式传入 access_key_secret。不使用百炼控制台 sk- API Key。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.config import (
    BAILIAN_ENDPOINT,
    BAILIAN_INDEX_ID,
    BAILIAN_RETRIEVE_ENABLE_RERANKING,
    BAILIAN_REGION_ID,
    BAILIAN_WORKSPACE_ID,
    RETRIEVE_K,
)
from app.rag.aliyun_credentials import get_credential_client, get_credential_status, validate_ram_credential


@dataclass
class RetrievedChunk:
    text: str
    score: float | None
    metadata: dict[str, Any]


def _validate_retrieve_config() -> None:
    validate_ram_credential()
    if not BAILIAN_WORKSPACE_ID:
        raise ValueError("调用百炼 Retrieve API 时，请设置 BAILIAN_WORKSPACE_ID")
    if not BAILIAN_INDEX_ID:
        raise ValueError("调用百炼 Retrieve API 时，请设置 BAILIAN_INDEX_ID")


def _create_client():
    """创建百炼 SDK 客户端，凭证由 Credentials 默认凭据链注入。"""
    from alibabacloud_bailian20231229.client import Client as BailianClient
    from alibabacloud_tea_openapi import models as open_api_models

    credential_client = get_credential_client()
    config = open_api_models.Config(credential=credential_client)
    config.endpoint = BAILIAN_ENDPOINT
    config.region_id = BAILIAN_REGION_ID
    return BailianClient(config)


def _parse_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def _nodes_from_response(body: Any) -> list[RetrievedChunk]:
    data = getattr(body, "data", None) or getattr(body, "Data", None) or {}
    if hasattr(data, "to_map"):
        data = data.to_map()
    if not isinstance(data, dict):
        data = {}

    nodes = data.get("Nodes") or data.get("nodes") or []
    chunks: list[RetrievedChunk] = []
    for node in nodes:
        if hasattr(node, "to_map"):
            node = node.to_map()
        if not isinstance(node, dict):
            continue
        text = str(node.get("Text") or node.get("text") or "").strip()
        if not text:
            continue
        score_raw = node.get("Score") if "Score" in node else node.get("score")
        score = float(score_raw) if score_raw is not None else None
        metadata = _parse_metadata(node.get("Metadata") or node.get("metadata"))
        chunks.append(RetrievedChunk(text=text, score=score, metadata=metadata))
    return chunks


def retrieve_chunks(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """从百炼云知识库检索文本切片（Credentials 默认凭据链鉴权）。"""
    _validate_retrieve_config()

    from alibabacloud_bailian20231229 import models as bailian_models
    from alibabacloud_tea_util import models as util_models

    k = top_k if top_k is not None else RETRIEVE_K
    client = _create_client()
    request = bailian_models.RetrieveRequest(
        index_id=BAILIAN_INDEX_ID,
        query=question,
        dense_similarity_top_k=k,
        sparse_similarity_top_k=0,
        enable_reranking=BAILIAN_RETRIEVE_ENABLE_RERANKING,
        rerank_top_n=min(max(k, 1), 20),
    )
    runtime = util_models.RuntimeOptions()
    response = client.retrieve_with_options(BAILIAN_WORKSPACE_ID, request, {}, runtime)

    body = response.body
    success = getattr(body, "success", None)
    if success is False:
        code = getattr(body, "code", None) or getattr(body, "Code", None) or "Unknown"
        message = getattr(body, "message", None) or getattr(body, "Message", None) or str(body)
        raise RuntimeError(f"百炼 Retrieve 调用失败：{code} {message}")

    chunks = _nodes_from_response(body)
    if not chunks:
        code = getattr(body, "code", None) or getattr(body, "Code", None)
        message = getattr(body, "message", None) or getattr(body, "Message", None)
        if code or message:
            raise RuntimeError(f"百炼 Retrieve 未返回切片：{code} {message}")
    return chunks


def test_retrieve_connection(query: str = "测试") -> dict[str, Any]:
    """诊断用：测试 Retrieve API 连通性。"""
    cred_status = get_credential_status()
    result: dict[str, Any] = {
        "mode": "retrieve",
        **cred_status,
        "workspace_id": BAILIAN_WORKSPACE_ID,
        "index_id": BAILIAN_INDEX_ID,
        "endpoint": BAILIAN_ENDPOINT,
        "region_id": BAILIAN_REGION_ID,
        "connection_test": None,
        "chunk_count": 0,
    }
    if cred_status.get("error"):
        result["connection_test"] = "失败"
        result["error"] = cred_status["error"]
        return result

    try:
        chunks = retrieve_chunks(query, top_k=1)
        result["connection_test"] = "成功"
        result["chunk_count"] = len(chunks)
        result["error"] = None
    except Exception as exc:
        result["connection_test"] = "失败"
        error_text = str(exc)
        if "SignatureDoesNotMatch" in error_text:
            error_text += (
                "\n\n【提示】请核对 RAM AccessKey 是否配对、是否授权 AliyunBailianDataFullAccess，"
                "且子账号已加入业务空间。生产环境建议使用 ECS/ACK 实例角色或 OIDC，避免在代码中硬编码 AK/SK。"
            )
        result["error"] = error_text
    return result
