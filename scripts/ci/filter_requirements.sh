#!/bin/sh
# Filter requirements.txt for CI/Docker images (API runtime, no heavy optional sim/ML).
# Keeps parity with scripts/ci/setup_python.sh exclusions.
set -eu

INPUT="${1:-requirements.txt}"
OUTPUT="${2:-requirements.docker.txt}"

grep -Ev '^(matplotlib|newton-physics|pymc|arviz|numba|sentence-transformers|gensim|dowhy)' "$INPUT" \
  | grep -Ev '^(pytest|pytest-asyncio|pytest-cov|pytest-timeout|mypy)' \
  | grep -Ev '^\s*#' \
  | grep -v '^[[:space:]]*$' \
  | sed 's/[[:space:]]*#.*$//' \
  | grep -v '^[[:space:]]*$' \
  | awk '!seen[$0]++' > "$OUTPUT"

echo "Wrote ${OUTPUT} ($(wc -l < "$OUTPUT" | tr -d ' ') lines)"
