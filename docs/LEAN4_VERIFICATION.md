# Lean 4 + lean4lean Verification

## Overview
lean4lean is a self-hosted Lean 4 kernel written entirely in Lean 4, available at [github.com/digama0/lean4lean](https://github.com/digama0/lean4lean). It is distributed under a BSD-style license, aligning with TURBO-CDI's compliance requirements.

## Setup
### Prerequisites
- [Lake](https://lake.readthedocs.io/) (Lean 4 package manager)
- Lean 4 toolchain installed

### Installation
1. Clone the lean4lean repository:
   ```bash
   git clone https://github.com/digama0/lean4lean.git /Users/figuramax/LocalProjects/lean4lean
   ```
2. Build the kernel:
   ```bash
   cd /Users/figuramax/LocalProjects/lean4lean && lake build Lean4Lean
   ```

## Benefits
- **Self-verification**: The Lean 4 kernel formally verifies its own correctness using lean4lean, reducing trust assumptions.
- **Stronger guarantees**: Formal validation of kernel operations ensures adherence to specification.
- **TURBO-CDI integration**: Enables future formal verification of TURBO-CDI's kernel operations once they are formalized in Lean 4.

## Verification Module Architecture (v8)

The verification system has been refactored into a 6-layer defense pipeline:

1. **Statistical Fast Path** (`stats_validator.py`) — SciPy t-test, chi², KS, correlation. Bypasses LLM for numerical claims.
2. **Auto-Theorem Formulator** (`auto_theorem.py`) — Z3 constraint extraction for numerical bounds.
3. **LLM Prover** (`llm_prover.py`) — Few-shot proof generation across 6 languages with RAG retrieval (251 examples).
4. **Consensus Engine** (`consensus_engine.py`) — Parallel Lean4 + Coq + Dafny, requires 2/3 agreement.
5. **Semantic Alignment** (`semantic_alignment.py`) — Checks proof-theorem correspondence.
6. **Unified Scoring** (`unified_score.py`) — 0–100 score with confidence and recommendations.

### Few-Shot Example Library
| Language | Examples | Coverage |
|----------|----------|----------|
| Lean4 | 56 | Arithmetic, induction, lists, logic |
| Coq | 48 | Nat proofs, booleans, lists, divisibility |
| Dafny | 52 | Methods, loops, invariants, data structures |
| Z3 | 50 | Integer/real constraints, parity, divisibility |
| Agda | 45 | Dependent types, equality, list proofs |

### RAG Retriever
TF-IDF + cosine similarity retriever (`rag_retriever.py`) selects top-k similar examples for few-shot prompting. Zero GPU required.

### Integration Status
The `Lean4LeanClient` (located at `src/verification/lean4lean_client.py`) provides a Python interface to interact with lean4lean. Full verification is pending formalization of TURBO-CDI operations in Lean 4.
