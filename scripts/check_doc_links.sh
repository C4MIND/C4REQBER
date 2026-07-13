#!/usr/bin/env bash
# Wave A doc invariants — verify canonical guides exist and are linked.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0

required=(
  docs/API_KEYS.md
  docs/SOCIAL_PUBLISHING.md
  docs/INSTALL.md
  packaging/desktop/README.md
)

for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f"
    fail=1
  fi
done

for f in README.md docs/INSTALL.md .env.example; do
  if ! rg -q 'docs/API_KEYS.md' "$f" 2>/dev/null; then
    echo "NO LINK to docs/API_KEYS.md in $f"
    fail=1
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "Doc link check failed."
  exit 1
fi
echo "Doc link check OK (${#required[@]} required files, API_KEYS links verified)."
