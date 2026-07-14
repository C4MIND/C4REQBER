#!/usr/bin/env bash
# Test LLM provider chain (keys from ~/.kilo; no secrets printed).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$(dirname "$0")/load_kilo_env.sh"
export PYTHONPATH=src
python3 - <<'PY'
from src.llm.sync_provider_chain import generate_with_fallback
r = generate_with_fallback("Reply with exactly: PROVIDER_OK", max_tokens=20, temperature=0)
print("RESULT:", r[:200])
PY
