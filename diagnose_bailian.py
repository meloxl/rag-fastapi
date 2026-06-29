#!/usr/bin/env python3
"""百炼应用快速诊断脚本 - 无需完整依赖"""

import json
import os
import urllib.error
import urllib.request
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BAILIAN_API_BASE = os.getenv("BAILIAN_API_BASE", "https://dashscope.aliyuncs.com/api/v1").rstrip("/")
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
BAILIAN_APP_ID = os.getenv("BAILIAN_APP_ID", "w6gsdtpq67")
BAILIAN_WORKSPACE_ID = os.getenv("BAILIAN_WORKSPACE_ID", os.getenv("DASHSCOPE_WORKSPACE_ID", "ws-kjehcatf1uzce0xp"))
BAILIAN_TIMEOUT = float(os.getenv("BAILIAN_TIMEOUT", "60"))
RAG_PROVIDER = os.getenv("RAG_PROVIDER", "local").strip().lower()


def normalize_bailian_api_base(api_base: str) -> str:
    base = api_base.rstrip("/")
    if ".maas.aliyuncs.com" in base:
        return "https://dashscope.aliyuncs.com/api/v1"
    return base


BAILIAN_API_BASE = normalize_bailian_api_base(BAILIAN_API_BASE)


def mask_secret(value: str) -> str:
    if not value:
        return "未设置"
    if len(value) <= 12:
        return "已设置（已隐藏）"
    return f"{value[:8]}...{value[-4:]}"


def diagnose() -> None:
    """执行诊断"""
    print("\n" + "="*70)
    print("🔍 百炼应用诊断工具")
    print("="*70)
    
    print(f"\n📋 配置信息：")
    print(f"  RAG_PROVIDER:     {RAG_PROVIDER}")
    print(f"  API Base:         {BAILIAN_API_BASE}")
    print(f"  App ID:           {BAILIAN_APP_ID}")
    print(f"  Workspace ID:     {BAILIAN_WORKSPACE_ID or '未设置'}")
    print(f"  API Key:          {mask_secret(BAILIAN_API_KEY)}")
    print(f"  Timeout:          {BAILIAN_TIMEOUT}s")
    
    if RAG_PROVIDER != "bailian":
        print(f"\n⚠️  注意：当前 RAG_PROVIDER={RAG_PROVIDER}，不是 'bailian'")
        print("   如需使用百炼，请在 .env 中设置：RAG_PROVIDER=bailian")
        print("="*70 + "\n")
        return
    
    if not BAILIAN_API_KEY:
        print("\n❌ 错误：BAILIAN_API_KEY 未设置")
        print("   请在 .env 中添加：BAILIAN_API_KEY=sk-xxxxx")
        print("="*70 + "\n")
        return
    
    if not BAILIAN_APP_ID:
        print("\n❌ 错误：BAILIAN_APP_ID 未设置")
        print("   请在 .env 中添加：BAILIAN_APP_ID=应用ID")
        print("="*70 + "\n")
        return
    
    # 测试连接
    print(f"\n🔗 连接测试...")
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
        print(f"  ✅ 连接成功！")
        print(f"\n✅ 诊断结果：所有检查通过，百炼应用配置正常")
        
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        detail = exc.read().decode("utf-8", errors="replace")
        
        print(f"  ❌ HTTP {status_code} 错误")
        
        if status_code == 403:
            print(f"\n❌ 诊断结果：HTTP 403 - 访问被拒绝")
            print(f"\n原因分析：")
            print(f"  1. ❓ API Key 是否已失效或过期？")
            print(f"     → 登录阿里云百炼平台检查 API Key 有效期")
            print(f"     → 必要时删除旧 Key 并生成新的")
            print(f"\n  2. ❓ API Key 与 App ID 是否对应？")
            print(f"     → 确保在同一阿里云账户下创建")
            print(f"     → 检查 App ID 是否正确：{BAILIAN_APP_ID}")
            print(f"\n  3. ❓ Workspace ID 是否正确？")
            print(f"     → 当前 Workspace ID：{BAILIAN_WORKSPACE_ID or '未设置'}")
            print(f"     → 子业务空间应用必须设置 X-DashScope-WorkSpace 请求头")
            print(f"\n  4. ❓ 应用在百炼平台是否被禁用？")
            print(f"     → 登录百炼平台验证应用状态")
            print(f"\n  4. ❓ 账户是否有足够的配额和余额？")
            print(f"     → 检查阿里云账户余额")
            print(f"     → 查看百炼应用调用配额是否已用尽")
            
        elif status_code == 401:
            print(f"\n❌ 诊断结果：HTTP 401 - 认证失败")
            print(f"原因：API Key 无效或格式错误")
            print(f"解决：检查 BAILIAN_API_KEY 是否正确，应以 'sk-' 开头")
            
        else:
            print(f"\n❌ 诊断结果：HTTP {status_code} 错误")
        
        print(f"\n📝 错误详情：")
        # 只显示前 500 字符避免过长
        error_preview = detail[:500] if len(detail) > 500 else detail
        print(f"  {error_preview}")
        
    except urllib.error.URLError as exc:
        print(f"  ❌ 连接失败")
        print(f"\n❌ 诊断结果：无法连接百炼服务")
        print(f"原因：{exc.reason}")
        print(f"\n检查项：")
        print(f"  - 网络连接是否正常？")
        print(f"  - API Base URL 是否正确？({BAILIAN_API_BASE})")
        print(f"  - 是否在防火墙或代理后面？")
        
    except Exception as exc:
        print(f"  ❌ 未知错误")
        print(f"\n❌ 诊断结果：发生异常")
        print(f"错误：{exc}")
    
    print("\n" + "="*70)
    print("💡 更多帮助请查看：documentation/百炼_403问题排查指南.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    diagnose()
