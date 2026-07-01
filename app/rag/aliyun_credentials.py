"""阿里云 Credentials 默认凭据链封装。

Retrieve API 通过 CredentialClient() 获取 RAM 凭证，不在业务代码中传递 access_key_secret。
凭据来源顺序见官方默认凭据链：环境变量 → 配置文件 → ECS/ACK 角色等。

参考：https://help.aliyun.com/en/sdk/developer-reference/v2-manage-python-access-credentials
"""

from __future__ import annotations

import re
from typing import Any

_RAM_ACCESS_KEY_ID_PATTERN = re.compile(r"^LTAI[A-Za-z0-9]+$")


def get_credential_client():
    """使用默认凭据链初始化 Credentials 客户端（无参）。"""
    from alibabacloud_credentials.client import Client as CredentialClient

    return CredentialClient()


def _reject_dashscope_api_key(name: str, value: str) -> None:
    if value.startswith("sk-") or value.startswith("sk_"):
        raise ValueError(
            f"{name} 看起来是百炼控制台 API Key（sk- 开头），不能用于 Retrieve API。"
            "请配置 RAM AccessKey（通常 AccessKey ID 以 LTAI 开头）。"
        )


def validate_ram_credential() -> None:
    """校验默认凭据链能否取得合法 RAM AccessKey。"""
    try:
        credential = get_credential_client().get_credential()
    except Exception as exc:
        raise ValueError(
            "无法从 Credentials 默认凭据链获取 RAM AccessKey。"
            "请设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET，"
            "或配置 ~/.alibabacloud/credentials 等凭据源。"
            f"详情：{exc}"
        ) from exc

    access_key_id = credential.get_access_key_id() or ""
    access_key_secret = credential.get_access_key_secret() or ""

    if not access_key_id or not access_key_secret:
        raise ValueError(
            "Credentials 默认凭据链未返回完整的 RAM AccessKey。"
            "请设置 ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET。"
        )

    _reject_dashscope_api_key("AccessKey ID", access_key_id)
    _reject_dashscope_api_key("AccessKey Secret", access_key_secret)

    if not _RAM_ACCESS_KEY_ID_PATTERN.match(access_key_id):
        raise ValueError(
            "AccessKey ID 格式异常（应以 LTAI 开头）。"
            "请确认使用的是 RAM AccessKey，而非百炼控制台 sk- API Key。"
        )


def get_credential_status() -> dict[str, Any]:
    """诊断用：检查默认凭据链状态（不暴露 Secret）。"""
    result: dict[str, Any] = {
        "auth_method": "credential_default_chain",
        "bailian_api_key_used": False,
        "credential_available": False,
        "access_key_id_preview": "未获取",
        "has_security_token": False,
        "error": None,
    }
    try:
        credential = get_credential_client().get_credential()
        access_key_id = credential.get_access_key_id() or ""
        access_key_secret = credential.get_access_key_secret() or ""
        result["credential_available"] = bool(access_key_id and access_key_secret)
        if access_key_id:
            result["access_key_id_preview"] = (
                f"{access_key_id[:8]}...{access_key_id[-4:]}" if len(access_key_id) > 12 else "已设置"
            )
        result["has_security_token"] = bool(credential.get_security_token())
        validate_ram_credential()
    except Exception as exc:
        result["error"] = str(exc)
    return result
