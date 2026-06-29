"""百炼应用诊断工具 - 帮助快速排查 403 权限问题"""

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


def check_bailian_config() -> dict[str, Any]:
    """检查百炼应用配置和连接状态"""
    results = {
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

    # 测试连接
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
        
        if status_code == 403:
            results["error"] = (
                "【HTTP 403 - 访问被拒绝】\n"
                "可能的原因：\n"
                "1. API Key 已失效、过期或被撤销\n"
                "2. API Key 与 App ID 不匹配\n"
                "3. 子业务空间应用缺少或填错 Workspace ID\n"
                "4. 应用在百炼平台被禁用\n"
                "5. 账户配额已用尽或余额不足\n"
                "6. API Key 权限不足\n\n"
                f"错误详情：{detail}"
            )
        elif status_code == 401:
            results["error"] = (
                "【HTTP 401 - 认证失败】\n"
                "API Key 可能无效。请检查：\n"
                "1. BAILIAN_API_KEY 值是否正确\n"
                "2. 是否正确地使用了 DASHSCOPE_API_KEY 别名\n\n"
                f"错误详情：{detail}"
            )
        else:
            results["error"] = f"HTTP {status_code} 错误：{detail}"
    except urllib.error.URLError as exc:
        results["error"] = f"无法连接：{exc.reason}"
    except Exception as exc:
        results["error"] = f"未知错误：{exc}"

    return results


def print_diagnostics() -> None:
    """打印诊断信息到控制台"""
    results = check_bailian_config()
    
    print("\n" + "="*60)
    print("百炼应用诊断信息")
    print("="*60)
    print(f"API Base URL: {results['api_base']}")
    print(f"Expected Base: {results['expected_api_base']}")
    print(f"API Key: {results['api_key_preview']}")
    print(f"App ID: {results['app_id']}")
    print(f"Workspace ID: {results['workspace_id']}")
    print(f"超时设置: {results['timeout']}s")
    print(f"连接测试: {results['connection_test']}")
    
    if results["error"]:
        print(f"\n❌ 诊断结果：\n{results['error']}")
    else:
        print("\n✅ 诊断结果：配置正常，连接成功")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_diagnostics()
