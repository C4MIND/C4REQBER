#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/pkg"

echo "Building c4reqber WASM modules → $OUT"

echo "  → spectral"
cd "$ROOT/spectral"
wasm-pack build --target web --out-dir "$OUT/spectral"

echo "  → graph"
cd "$ROOT/graph"
wasm-pack build --target web --out-dir "$OUT/graph"

echo "WASM build complete. Output: $OUT/"
