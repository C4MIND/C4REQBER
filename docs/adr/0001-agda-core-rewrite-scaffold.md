# ADR 0001: Agda-core rewrite scaffold (module boundaries only)

**Status:** Accepted (scaffold)
**Date:** 2026-07-22
**Deciders:** c4reqber maintainers

## Context

c4reqber ships multiple formal verification backends (Lean4, Coq, Dafny, Agda, Z3, …) behind
`HybridVerifier` and `LLMProver`. Agda is optional at install time; painting `verified` when
`agda` is missing is a honesty regression (R18 in the deep-honesty PRD).

A future **Agda-core rewrite** of pipeline logic has been discussed as a long-horizon option.
That rewrite must not block honesty fixes or product delivery.

## Decision

1. **Keep** `src/verification/agda_bridge.py` and the Agda path in `HybridVerifier` / `LLMProver`.
2. **Honesty:** `not_installed` → outer `unavailable` (never `verified` / green success).
3. **Scaffold only:** define target module boundaries aligned with Phase 1 reorg (~16 modules)
   without migrating runtime code:
   - `c4/` — state space + operators (Z₃³)
   - `pipeline/` — orchestration phases A–G
   - `verification/` — backend bridges + contracts
   - `knowledge/` — sources + citation honesty
   - Worker boundary — heavy numerics behind serializable IPC (future)
4. **Non-goal:** full Agda-core rewrite of the pipeline in a single merge.

## Consequences

- Windows / macOS users without Agda see honest `unavailable`, not fake proofs.
- CI may include an optional, skippable Agda scaffold test (`tests/test_agda_scaffold_stub.py`).
- When an Agda-core experiment starts, it targets the scaffold boundaries above, not ad-hoc files.

## References

- `docs/HONESTY_CONTRACT.md`
- `docs/superpowers/plans/2026-07-22-deep-honesty-asymmetry-fix.md` (W9)
- `CLAUDE.md` Phase 1 reordering notes
