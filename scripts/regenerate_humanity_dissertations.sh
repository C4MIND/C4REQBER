#!/usr/bin/env bash
# Regenerate humanity-saving turbo dissertations (hard-gated Phase F).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT_DIR="$ROOT/reports/2026-07-09/humanity_saving/discoveries"
mkdir -p "$OUT_DIR"

run_one() {
  local id="$1"
  local topic="$2"
  local out="$OUT_DIR/${id}.md"
  local log="$OUT_DIR/${id}.log"
  echo "=== [$id] turbo: $topic ==="
  if ./scripts/run_humanity_mission.sh turbo "$topic" \
      --output "$out" --no-functors --no-iterative \
      2>&1 | tee "$log"; then
    words=$(wc -w < "$out" | tr -d ' ')
    if grep -q '\[LLM unavailable' "$out" 2>/dev/null; then
      echo "FAIL [$id]: LLM placeholder in $out"
      return 1
    fi
    if [[ "$words" -lt 600 ]]; then
      echo "FAIL [$id]: only ${words} words in $out"
      return 1
    fi
    echo "OK [$id]: ${words} words -> $out"
    return 0
  fi
  echo "FAIL [$id]: pipeline exit non-zero"
  return 1
}

FAIL=0
run_one "01_marine_cloud_brightening" \
  "marine cloud brightening geoengineering to prevent 2C warming" || FAIL=$((FAIL + 1))
run_one "04_epigenetic_aging" \
  "epigenetic reversal of cellular aging through metabolic reprogramming" || FAIL=$((FAIL + 1))
run_one "06_soil_carbon" \
  "soil carbon sequestration: regenerative agriculture to reverse desertification" || FAIL=$((FAIL + 1))
run_one "02_compact_fusion" \
  "compact fusion reactors for distributed clean energy: breakthrough physics pathway to decarbonize grid by 2040" || FAIL=$((FAIL + 1))
run_one "05_amr_phage_crispr" \
  "antimicrobial resistance: phage-CRISPR cocktail to restore antibiotic efficacy" || FAIL=$((FAIL + 1))

echo "=== Done. Failures: $FAIL ==="
exit "$FAIL"
