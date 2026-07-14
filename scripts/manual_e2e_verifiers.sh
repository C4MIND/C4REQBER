#!/bin/bash
# Manual E2E verifier test — same paths TUI + pipeline use.
set -euo pipefail
export PATH="/opt/homebrew/bin:/opt/homebrew/opt/openjdk/bin:$PATH"
export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk}"
export TLA_TOOLS_JAR="${TLA_TOOLS_JAR:-$HOME/.tlaplus/tla2tools.jar}"
BASE="${1:-http://127.0.0.1:8000}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

# TUI path: GET /health harvests csrf_token cookie, then POST sends X-CSRF-Token.
COOKIE_JAR="/tmp/c4_e2e_cookies.txt"
rm -f "$COOKIE_JAR"
curl -sf -c "$COOKIE_JAR" "$BASE/api/v1/health" -o /dev/null
CSRF_TOKEN=$(awk '$6=="csrf_token"{print $7}' "$COOKIE_JAR" | tail -1)
AUTH_HDR=$(/opt/homebrew/bin/python3 - <<'PY'
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(".env.dontredact"))
    load_dotenv(Path(".env"))
except ImportError:
    pass
secret = os.getenv("JWT_SECRET", "")
if not secret:
    print("")
else:
    import jwt
    print("Authorization: Bearer " + jwt.encode({"sub": "e2e-test"}, secret, algorithm="HS256"))
PY
)
CURL_AUTH=()
if [[ -n "$AUTH_HDR" ]]; then
  CURL_AUTH=(-H "$AUTH_HDR")
fi
CURL_CSRF=()
if [[ -n "$CSRF_TOKEN" ]]; then
  CURL_CSRF=(-H "X-CSRF-Token: $CSRF_TOKEN")
fi

pass=0
fail=0
check() {
  local name="$1" code="$2"
  if [[ "$code" == "0" ]]; then
    echo "PASS $name"
    pass=$((pass + 1))
  else
    echo "FAIL $name"
    fail=$((fail + 1))
  fi
}

echo "=== E2E Verifier Manual Test (base=$BASE) ==="

# 1. TUI capabilities overlay endpoint
code=$(curl -sf -o /tmp/cap.json -w "%{http_code}" "$BASE/v8/simulations/capabilities" || echo 000)
check "GET /v8/simulations/capabilities HTTP" "$([[ "$code" == "200" ]] && echo 0 || echo 1)"
/opt/homebrew/bin/python3 - <<'PY'
import json, sys
d=json.load(open("/tmp/cap.json"))
v={x["id"]:x["available"] for x in d.get("verifiers",[])}
for k in ("cvc5","tla","alloy"):
    if not v.get(k):
        print(f"FAIL verifier {k} not available in capabilities"); sys.exit(1)
print(f"OK capabilities: cvc5={v['cvc5']} tla={v['tla']} alloy={v['alloy']} engines={len(d.get('engines',[]))}")
PY
check "capabilities JSON cvc5/tla/alloy" $?

# 2. Verification methods
code=$(curl -sf -o /tmp/methods.json -w "%{http_code}" "$BASE/v8/verification/methods" || echo 000)
check "GET /v8/verification/methods HTTP" "$([[ "$code" == "200" ]] && echo 0 || echo 1)"
/opt/homebrew/bin/python3 - <<'PY'
import json, sys
d=json.load(open("/tmp/methods.json"))
st=d.get("status",{})
for k in ("cvc5","tla","alloy"):
    if not st.get(k):
        print(f"FAIL methods missing {k}"); sys.exit(1)
print("OK methods:", {k:st[k] for k in ("cvc5","tla","alloy")})
PY
check "methods status cvc5/tla/alloy" $?

# 3. Legacy POST /verify per backend
CVC5='(set-logic QF_LIA)(declare-const x Int)(assert (> x 0))(check-sat)'
curl -sf -b "$COOKIE_JAR" -X POST "$BASE/v8/verification/verify" -H 'Content-Type: application/json' \
  "${CURL_AUTH[@]}" "${CURL_CSRF[@]}" \
  -d "{\"code\":\"$CVC5\",\"formal_method\":\"cvc5\"}" -o /tmp/v_cvc5.json
/opt/homebrew/bin/python3 -c "import json; d=json.load(open('/tmp/v_cvc5.json')); assert d.get('verified'), d; print('OK cvc5 verify')"
check "POST /verify cvc5" $?

TLA='---- MODULE Counter ----\nEXTENDS Naturals\nVARIABLE x\nInit == x = 0\nNext == /\\ x < 5 /\\ x'"'"' = x + 1\n===='
curl -sf -b "$COOKIE_JAR" -X POST "$BASE/v8/verification/verify" -H 'Content-Type: application/json' \
  "${CURL_AUTH[@]}" "${CURL_CSRF[@]}" \
  -d "$(/opt/homebrew/bin/python3 -c "import json; print(json.dumps({'code': '''$TLA''', 'formal_method': 'tla'}))")" -o /tmp/v_tla.json
/opt/homebrew/bin/python3 -c "import json; d=json.load(open('/tmp/v_tla.json')); assert d.get('verified'), d; print('OK tla verify')"
check "POST /verify tla" $?

curl -sf -b "$COOKIE_JAR" -X POST "$BASE/v8/verification/verify" -H 'Content-Type: application/json' \
  "${CURL_AUTH[@]}" "${CURL_CSRF[@]}" \
  -d '{"code":"sig Node {}\nrun {} for 3\n","formal_method":"alloy"}' -o /tmp/v_alloy.json
/opt/homebrew/bin/python3 -c "import json; d=json.load(open('/tmp/v_alloy.json')); assert d.get('verified'), d; print('OK alloy verify')"
check "POST /verify alloy" $?

# 4. Pipeline hybrid verifier (phase E path)
/opt/homebrew/bin/python3 - <<'PY'
import asyncio
from src.config.paths import load_verifiers_env
load_verifiers_env()
from src.verification.hybrid_verifier import HybridVerifier

async def main():
    hv = HybridVerifier()
    for backend, hyp in [
        ("cvc5", {"title": "SMT", "description": "(declare-const x Int)(assert (> x 0))(check-sat)"}),
        ("tla", {"title": "TLA", "description": "---- MODULE E2E ----\nEXTENDS Naturals\nVARIABLE x\nInit == x = 0\nNext == /\\ x < 5 /\\ x' = x + 1\n===="}),
        ("alloy", {"title": "Alloy", "description": "sig Node {}\nrun {} for 3\n"}),
    ]:
        claim = f"{hyp['title']}. {hyp['description']}"
        sel = hv._select_backend(claim)
        assert sel == backend, f"expected {backend} got {sel}"
        r = await hv.verify(hyp)
        print(f"pipeline {r.backend} status={r.status}")
        assert r.backend == backend, r.backend
        assert r.status == "verified", r

asyncio.run(main())
print("OK pipeline hybrid verify")
PY
check "pipeline HybridVerifier phase E" $?

# 5. Smoke script
/opt/homebrew/bin/python3 scripts/verify_backends_smoke.py
check "verify_backends_smoke.py" $?

# 6. TUI capsim client path (same HTTP call as Ctrl+Shift+C)
/opt/homebrew/bin/python3 - <<'PY'
import json, urllib.request
url = "http://127.0.0.1:8000/v8/simulations/capabilities"
with urllib.request.urlopen(url, timeout=15) as resp:
    data = json.load(resp)
ids = [v["id"] for v in data.get("verifiers", []) if v.get("available")]
for k in ("cvc5", "tla", "alloy"):
    assert k in ids, f"TUI overlay would miss {k}: {ids}"
print("OK TUI capsim fetch:", [k for k in ("cvc5","tla","alloy") if k in ids])
PY
check "TUI capsim HTTP fetch" $?

echo ""
echo "=== RESULT: $pass passed, $fail failed ==="
[[ "$fail" -eq 0 ]]
