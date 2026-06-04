#!/bin/bash
set -e

echo "Building TURBO-CDI WASM modules..."

# Build spectral embedding module
echo "  → spectral"
cd "$(dirname "$0")/spectral"
wasm-pack build --target web --out-dir ../../web-v2/src/wasm/spectral

# Build graph algorithms module
echo "  → graph"
cd "$(dirname "$0")/graph"
wasm-pack build --target web --out-dir ../../web-v2/src/wasm/graph

echo "WASM build complete. Output: web-v2/src/wasm/"
