# Honesty Contract — c4reqber (anti green-fake)

**Status:** active · **Date:** 2026-07-18
**Audience:** agents, reviewers, contributors
**Canonical remote:** GitLab `cognitive-functors/c4reqber`

This document is the SSOT for what “success / verified / available” means.
If code paints green while this contract says it must not — the code is wrong.

---

## Vocabulary

| Status / flag | Meaning | May look green? |
|---------------|---------|-----------------|
| `success` / `completed` / `ok` | Real work finished for the claimed engine/backend | Yes |
| `partial` | Something ran, but fallback / incomplete / weak gates | **No** (amber) |
| `unavailable` / `skipped` | Engine/backend missing or budget skip | **No** |
| `failed` / `error` | Hard failure | **No** |
| `stub: true` | Placeholder path | **No** |
| `heuristic: true` | Keyword / length / prior ranking — not evidence | **No** |
| `engine_truth: not_*` | Named engine was **not** the one that ran | **No** |
| `COMPILED` | Formal artifact typechecks; claim not aligned | **No** as VERIFIED |
| `FORMALLY VERIFIED` | Reserved for claim-aligned proof (alignment gate) | Yes only then |
| `satisfiable` (Z3 sat) | Model exists — **not** theorem proved | **No** as verified |

---

## Hard rules

1. **No invented success.** Empty search, missing corpus, transport errors, `sorry`, or conceptual stubs must not yield `passed=True` / `verified=True` / novelty `1.0`.
2. **Fallback ≠ primary engine.** NumPy/Jaynes–Cummings/Rebound stand-ins must set `engine_truth`, `accelerated: false`, and non-success status when they are not the claimed GPU/physics engine.
3. **OpenAlex citation match** requires normalized title similarity ≥ **0.82** (not “first search hit”). CrossRef DOI + unmatched OpenAlex → `PARTIAL`, never `VERIFIED`.
4. **Novelty unchecked** → `novelty_score: null` and pipeline abort / soft-fail — never `0.5` that slips under `< 0.5` gates.
5. **Z3 `sat` ≠ verified.** API exposes `satisfiable`; `verified` stays false without proof-goal semantics.
6. **MCP / plugin outer status** requires **positive provenance** for `success`:
   - Sims: `engine_truth` (not `not_*`) or named real engine + `executed` — fallbacks stay `partial` with payload retained
   - Plugins: `llm_backed=True` (gateway LLM ran) or compute evidence / `executed` — bare `status:success` refused; LLM-miss keeps structured fields as `partial` (not stub-empty)
   - BMA: `weighted_prediction` + model posteriors; prior-only ranking stays `partial`
   - Causal: do-calculus completed (`identifiable` true **or** false is success)
   Helpers: `src/utils/honesty_status.py` (re-exported as `src/mcp_server/honesty.py`).
7. **TUI:** `sim_finished` paints green only for `engine_status` in `{ok, success, completed}`. `partial` / `failed` jobs use `toast.partial` / `toast.failed` — never celebration burst for failure.
8. **Capabilities probe:** instantiable without `available` / `is_available` → **unavailable** (`no_availability_api`), not default-true.
9. **HF token:** optional `HF_TOKEN` env or `~/.cache/huggingface/token`. `~/.kimi/.env` → symlink to `~/.kilo/.env` (LLM keys); HF is usually **not** there.

---

## Dempster / MNLI

Preference order: **MNLI** (`facebook/bart-large-mnli`) → LLM stance → keyword overlap.

| Method | `heuristic` |
|--------|-------------|
| `nli_dempster` | `false` |
| `keyword_overlap_dempster` | `true` |
| no papers | `true` (explicit fallback) |

To force the keyword Dempster path in CI, set env ``C4_DEMPSTER_NLI`` to ``0``.
Local model cache: ``C4REQBER/.cache/huggingface`` (set ``HF_HOME``).

---

## Simulation honesty (selected)

| Path | Honest behavior |
|------|-----------------|
| Newton NumPy fallback | `partial`, `engine_truth: not_newton_physics` |
| Schr NumPy fallback | `partial`, `engine_truth: not_schr`, `accelerated_by: none` |
| Ensemble noise | off by default; if on → `heuristic: true` |
| Vast empty SSH | not `deployed` success |
| Schr “legacy speedup” | refused (`speedup: null`) — no `time.sleep` theater |

---

## TUI debug (Ctrl+Shift+D)

Must show last SSE type + timestamp when events arrived. Must not invent “phase (legacy)” as the only signal when typed events exist.

---

## Regression tests (honesty)

Run with project `.venv` (3.11+), not system 3.14 for physics/MNLI:

```bash
HF_HOME="$(pwd)/.cache/huggingface" \
.venv/bin/python -m pytest \
  tests/test_mcp_honesty_status.py \
  tests/test_citation_openalex_honesty.py \
  tests/test_mnli_real.py \
  tests/test_w*.py \
  tests/test_full_physics_integration.py \
  tests/test_post_audit_honesty.py \
  tests/test_honesty_sim_verify.py \
  -q
```

TUI:

```bash
cd src/tui/v9 && go test ./... -count=1
```

---

## Docs that must stay aligned

When honesty rules change, update:

- this file (`docs/HONESTY_CONTRACT.md`)
- `CHANGELOG.md` (honesty section)
- `AGENTS.md` (Honest Implementation Status)
- `docs/VERIFICATION_BACKENDS.md`
- `src/tui/v9/README.md` (status mapping)
- `docs/mcp_registry.md` (status fields)

Do **not** claim “0 mypy errors” or “ensemble = physics evidence” without re-verification against current code.
