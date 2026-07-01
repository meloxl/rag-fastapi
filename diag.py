#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

output = []

output.append("=" * 80)
output.append("DIAGNOSTIC REPORT")
output.append("=" * 80)

try:
    from app.config import (
        RAG_PROVIDER,
        BAILIAN_CALL_MODE,
        BAILIAN_WORKSPACE_ID,
        BAILIAN_INDEX_ID,
        ALIBABA_CLOUD_ACCESS_KEY_ID,
        ALIBABA_CLOUD_ACCESS_KEY_SECRET,
    )

    output.append("\n1. CONFIGURATION")
    output.append("-" * 80)
    output.append(f"RAG_PROVIDER: {RAG_PROVIDER}")
    output.append(f"BAILIAN_CALL_MODE: {BAILIAN_CALL_MODE}")
    output.append(f"BAILIAN_WORKSPACE_ID: {BAILIAN_WORKSPACE_ID}")
    output.append(f"BAILIAN_INDEX_ID: {BAILIAN_INDEX_ID}")
    output.append(f"ALIBABA_CLOUD_ACCESS_KEY_ID: {'SET' if ALIBABA_CLOUD_ACCESS_KEY_ID else 'NOT SET'}")
    output.append(f"ALIBABA_CLOUD_ACCESS_KEY_SECRET: {'SET' if ALIBABA_CLOUD_ACCESS_KEY_SECRET else 'NOT SET'}")

    if ALIBABA_CLOUD_ACCESS_KEY_ID:
        output.append(f"AccessKey ID preview: {ALIBABA_CLOUD_ACCESS_KEY_ID[:10]}...")

    output.append("\n2. CREDENTIAL STATUS")
    output.append("-" * 80)
    from app.rag.aliyun_credentials import get_credential_status
    status = get_credential_status()
    output.append(f"Auth method: {status.get('auth_method')}")
    output.append(f"Credential available: {status.get('credential_available')}")
    output.append(f"AccessKey ID: {status.get('access_key_id_preview')}")
    output.append(f"Has security token: {status.get('has_security_token')}")
    if status.get('error'):
        output.append(f"ERROR: {status.get('error')}")

    output.append("\n3. FULL DIAGNOSTIC")
    output.append("-" * 80)
    from app.rag.diagnostics import check_bailian_config
    results = check_bailian_config()
    output.append(f"Connection test: {results.get('connection_test')}")
    if results.get('error'):
        output.append(f"ERROR: {results.get('error')}")

except Exception as e:
    output.append(f"\nFATAL ERROR: {e}")
    import traceback
    output.append(traceback.format_exc())

output.append("\n" + "=" * 80)
result_text = "\n".join(output)

# Write to file
with open('diagnostic_output.txt', 'w', encoding='utf-8') as f:
    f.write(result_text)

# Also print
print(result_text)
