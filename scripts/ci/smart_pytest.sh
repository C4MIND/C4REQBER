#!/usr/bin/env bash
# Smart full pytest — use local HF/MNLI cache, never re-download Hub weights.
# Fail LLM providers fast so the suite does not burn 120s per hanging call.
#
# Usage:
#   bash scripts/ci/smart_pytest.sh
#   bash scripts/ci/smart_pytest.sh tests/test_honesty_sim_verify.py -q
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

HF_CACHE="${HF_HOME:-$ROOT/.cache/huggingface}"
MNLI_HUB="$HF_CACHE/hub/models--facebook--bart-large-mnli"

export HF_HOME="$HF_CACHE"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_CACHE}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
# Prefer local MNLI when snapshot exists; keyword Dempster otherwise
if [[ -d "$MNLI_HUB" ]]; then
  export C4_DEMPSTER_NLI="${C4_DEMPSTER_NLI:-1}"
  echo "smart_pytest: MNLI cache found → C4_DEMPSTER_NLI=$C4_DEMPSTER_NLI (local_files_only)"
else
  export C4_DEMPSTER_NLI=0
  echo "smart_pytest: no MNLI cache → C4_DEMPSTER_NLI=0 (keyword path)"
fi
# Do not wait minutes on OpenRouter/local LLM for unit suite.
# 8 providers × 8s ≈ blows pytest --timeout=60; keep one fast attempt.
export C4_LLM_HTTP_TIMEOUT="${C4_LLM_HTTP_TIMEOUT:-3}"
export C4_LLM_MAX_ROTATIONS="${C4_LLM_MAX_ROTATIONS:-1}"
# SystemAnalyzer graph deepen is optional; unit suite stays deterministic
export C4_LLM_DEEPEN="${C4_LLM_DEEPEN:-0}"

PY="${PYTHON:-}"
if [[ -z "$PY" && -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif [[ -z "$PY" ]]; then
  PY="python3"
fi

LOG="${SMART_PYTEST_LOG:-$ROOT/.cache/smart-pytest.log}"
mkdir -p "$(dirname "$LOG")"

ARGS=("$@")
if [[ ${#ARGS[@]} -eq 0 ]]; then
  # signal method actually interrupts hung tests; thread (pytest.ini) can leave
  # the whole suite stuck / silently dead on native code.
  ARGS=(-q --tb=line --timeout=60 --timeout-method=signal)
fi

echo "smart_pytest: HF_HOME=$HF_HOME HF_HUB_OFFLINE=1"
echo "smart_pytest: C4_LLM_HTTP_TIMEOUT=$C4_LLM_HTTP_TIMEOUT C4_LLM_MAX_ROTATIONS=$C4_LLM_MAX_ROTATIONS C4_LLM_DEEPEN=$C4_LLM_DEEPEN"
echo "smart_pytest: log → $LOG"
echo "smart_pytest: $PY -m pytest ${ARGS[*]}"
# Avoid `| tail`/awk eating the final summary; tee keeps a full log.
set +e
"$PY" -m pytest "${ARGS[@]}" 2>&1 | tee "$LOG"
code=${PIPESTATUS[0]}
set -e
echo "----- smart_pytest summary (tail) -----"
tail -n 40 "$LOG" | sed -n '/failed\|passed\|error\|===/Ip'
exit "$code"
