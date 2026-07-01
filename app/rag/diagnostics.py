"""百炼 RAG 诊断：Retrieve API（默认）与百炼应用 API（备用）。"""

import json
import urllib.error
import urllib.request
from typing import Any

from app.config import (
    BAILIAN_API_BASE,
    BAILIAN_API_KEY,
    BAILIAN_APP_ID,
    BAILIAN_CALL_MODE,
    BAILIAN_INDEX_ID,
    BAILIAN_TIMEOUT,
    BAILIAN_WORKSPACE_ID,
)
from app.rag.bailian_retrieve import test_retrieve_connection


def check_bailian_app_config() -> dict[str, Any]:
    """检查百炼应用 completion API 配置和连接状态（备用模式）。"""
    results = {
        "mode": "app",
        "api_key_set": bool(BAILIAN_API_KEY),
        "app_id_set": bool(BAILIAN_APP_ID),
        "api_base": BAILIAN_API_BASE,
        "expected_api_base": "https://dashscope.aliyuncs.com/api/v1",
        "api_key_preview": f"{BAILIAN_API_KEY[:10]}...{BAILIAN_API_KEY[-4:]}" if BAILIAN_API_KEY else "未设置",
        "app_id": BAILIAN_APP_ID,
        "workspace_id": BAILIAN_WORKSPACE_ID or "未设置",
        "timeout": BAILIAN_TIMEOUT,
        "connection_test": None,
        "error": None,
    }

    if not BAILIAN_API_KEY or not BAILIAN_APP_ID:
        results["error"] = "API Key 或 App ID 未设置"
        return results

    url = f"{BAILIAN_API_BASE}/apps/{BAILIAN_APP_ID}/completion"
    body = {
        "input": {"prompt": "测试"},
        "parameters": {},
        "debug": {},
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {BAILIAN_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            **({"X-DashScope-WorkSpace": BAILIAN_WORKSPACE_ID} if BAILIAN_WORKSPACE_ID else {}),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=BAILIAN_TIMEOUT) as response:
            response.read()
            results["connection_test"] = "成功"
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        detail = exc.read().decode("utf-8", errors="replace")
        results["connection_test"] = f"失败 - HTTP {status_code}"
        results["error"] = f"HTTP {status_code} 错误：{detail}"
    except urllib.error.URLError as exc:
        results["error"] = f"无法连接：{exc.reason}"
    except Exception as exc:
        results["error"] = f"未知错误：{exc}"

    return results


def check_bailian_config() -> dict[str, Any]:
    """按 BAILIAN_CALL_MODE 检查当前百炼后端。"""
    if BAILIAN_CALL_MODE == "app":
        return check_bailian_app_config()
    return test_retrieve_connection()


def print_diagnostics() -> None:
    """打印诊断信息到控制台。"""
    results = check_bailian_config()

    print("\n" + "=" * 60)
    if BAILIAN_CALL_MODE == "app":
        print("百炼应用诊断信息（completion API，备用模式）")
    else:
        print("百炼云知识库诊断信息（Retrieve API，默认模式）")
    print("=" * 60)
    print(f"调用模式: {BAILIAN_CALL_MODE}")

    if BAILIAN_CALL_MODE == "app":
        print(f"API Base URL: {results.get('api_base')}")
        print(f"API Key: {results.get('api_key_preview')}")
        print(f"App ID: {results.get('app_id')}")
    else:
        print("鉴权方式: Credentials 默认凭据链（不使用百炼 sk- API Key）")
        print(f"Endpoint: {results.get('endpoint')}")
        print(f"Region: {results.get('region_id')}")
        print(f"Workspace ID: {results.get('workspace_id')}")
        print(f"Index ID: {results.get('index_id') or BAILIAN_INDEX_ID}")
        print(f"凭据可用: {results.get('credential_available')}")
        print(f"AccessKey ID: {results.get('access_key_id_preview', '未获取')}")
        print(f"使用 STS Token: {results.get('has_security_token')}")
        print(f"检索切片数: {results.get('chunk_count', 0)}")

    print(f"Workspace ID: {BAILIAN_WORKSPACE_ID or '未设置'}")
    print(f"连接测试: {results.get('connection_test')}")

    if results.get("error"):
        print(f"\n❌ 诊断结果：\n{results['error']}")
    else:
        print("\n✅ 诊断结果：配置正常，连接成功")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_diagnostics()
