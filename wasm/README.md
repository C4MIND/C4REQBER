# WASM Spectral Embedding Module

Rust-based WASM module for high-performance spectral embedding computations.

## Structure

```
wasm/
├── Cargo.toml          # Rust workspace manifest
├── spectral/           # Spectral embedding crate
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs      # wasm-bindgen exports
├── graph/              # Graph algorithms crate
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs
└── build.sh            # Build script
```

## Prerequisites

- Rust + wasm-pack: `curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh`
- Node.js 18+

## Build

```bash
cd wasm
./build.sh
```

## Usage (Frontend)

```typescript
import init, { spectral_embedding } from '@/wasm/spectral'

await init()
const embedding = spectral_embedding(adjacencyMatrix, dimensions)
```

## Performance Targets

- Spectral embedding: < 50ms for 1000-node graphs (vs 500ms Python)
- Graph Laplacian: SIMD-optimized
- Memory: zero-copy via SharedArrayBuffer
