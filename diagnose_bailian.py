#!/usr/bin/env python3
"""百炼 RAG 快速诊断脚本 - 支持 Retrieve（默认）与 App completion（备用）。"""

from app.config import BAILIAN_CALL_MODE, RAG_PROVIDER
from app.rag.diagnostics import check_bailian_config, print_diagnostics


def main() -> None:
    if RAG_PROVIDER != "bailian":
        print(f"\n⚠️  当前 RAG_PROVIDER={RAG_PROVIDER}，不是 'bailian'")
        print("   如需使用百炼，请在 .env 中设置：RAG_PROVIDER=bailian\n")
        return

    print_diagnostics()
    results = check_bailian_config()
    if results.get("error"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
