# Honesty Contract — c4reqber (anti green-fake)

**Status:** active · **Date:** 2026-07-22
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
10. **Flash `--sources`:** `blast flash` / MCP `blast_flash` share `run_flash`. A source is **verified** only after `CitationVerifier` (CrossRef DOI and/or OpenAlex title similarity ≥ 0.82 → `VERIFIED`/`PARTIAL`). Presence of a DOI/URL alone is **checkable**, not verified. Footer / mascot / `sources` list = **verified only**. Unverified raw hits may appear under a separate “Unverified hits (not counted)” section. If verified sources exist, the answer must not claim “unable to find”. Strip `example.com` and `scholar.google.com/scholar?q=` URLs. `~/.c4reqber/secrets.env` is loaded for **all** CLI commands so Tavily can activate.
11. **Rate limits (HTTP 429):** OpenRouter / gateway chat must rotate free-tier and local providers (cap: `C4_LLM_MAX_ROTATIONS`, default 8). When all providers are exhausted → `status: partial` + `rate_limited` warning — **never** an empty success answer. Prefer LM Studio / Ollama / MLX when `C4_LOCAL_LLM_FIRST=1` or after the first 429.
12. **Query spray:** literature/materials flash queries use domain allowlists — do not hammer PubChem / ClinicalTrials / UCI ML / HF datasets / CERN OD / AFLOW / Materials Project with full English instructions.

---

## Flash surfaces (I1–I10)

Merge blockers from the Zero-Asymmetry Product Lock PRD. Every surface that shows Flash, sources, complete, verified, or novelty must obey these invariants.

| ID | Invariant | Surfaces |
|----|-----------|----------|
| **I1** | Exactly **one** Flash implementation: `run_flash` → shared `FlashResult` schema. CLI, MCP, API job, TUI all consume the **composed** job (answer + verified sources + optional C4/TRIZ/hypothesis). | `blast flash`, MCP `blast_flash`, `POST /v8/discover/flash`, TUI Flash mode |
| **I2** | No UI fires `toast.complete` or celebration **burst** unless terminal status ∈ `{success, complete}` **and** payload honesty allows it. Missing status → fail-closed (`partial`, no burst). | TUI `applyCelebrationPolicy`, Flash / Discover / Multi SSE + poll paths |
| **I3** | `sources` / mascot source count = **CitationVerifier-confirmed** (`VERIFIED`/`PARTIAL`) only. Raw hits → `unverified_hits` (labeled, not counted). | CLI footer, MCP payload, TUI cards, turbo/solve mascots, Phase B |
| **I4** | Empty / unchecked novelty → `novelty_score: null` — never placeholder `1.0` or `0.5`. Gates treat `null` as **unchecked** (warn/skip), not automatic fail. | NoveltyScorer, synthesis, agenda, discovery_utils, quality gates |
| **I5** | HTTP **429** → rotate free-tier/local providers (cap `C4_LLM_MAX_ROTATIONS`); all exhausted → `status: partial` + `rate_limited` warning — never empty success answer. | `AsyncLLMClient`, gateway, `run_flash` |
| **I6** | Fallback sim (`not_*`, `*_not_*`, e.g. `rebound_not_amuse`) → outer **`partial`**, never SUCCESS. | MCP `c4_simulate`, TUI `sim_finished`, honesty_status helpers |
| **I7** | Stub tools forbidden on production paths (`agent_search` string placeholders, fake dissertation sections, `WebSearchPlugin` example.com). Wire real search or honest `unavailable`. | Agent daemon, plugins, live_feed |
| **I8** | `~/.c4reqber/secrets.env` loaded on every product entry: `blast *`, API lifespan, MCP serve, Win desktop launcher. | `apply_config_to_env` in paths / lifespan / MCP / launcher.bat |
| **I9** | Query shaping (`_shape_search_query`) on **all** search entrypoints including `search_single` and MCP `c4_search`. | orchestrator, MCP search tools |
| **I10** | Live Windows AISI 440C acceptance (TUI Flash **or** CLI after TUI path proven) before calling the PRD done. Log or explicit waiver required. | `docs/WINDOWS_FLASH_ACCEPTANCE.md` |

### FlashResult (SSOT)

Defined in `src/knowledge/flash_contract.py`:

```text
status: success | partial | error
answer: str
sources: list[CitationCard]          # verified only
unverified_hits: list[CitationCard]  # not counted
verified_count, found_count, warnings, search_meta
c4_path?, triz_principles?, hypothesis?  # composer framing (§4.1)
```

### JobTerminalEvent (SSE)

`JobStore` derives terminal event from `result.status` via `derive_terminal()` — **must not** emit `type=complete` when `result.status` ∈ `{partial, aborted, failed, error}`.

### TUI celebration policy

| Incoming status | Toast | Burst | Card status |
|-----------------|-------|-------|-------------|
| `success` / `complete` | `toast.complete` | yes | done |
| `partial` / `aborted` | `toast.partial` | **no** | partial |
| `failed` / `error` | `toast.failed` | **no** | error |
| missing | `toast.partial` (fail-closed) | **no** | partial |

Applies to Flash, Multi, Discover SSE `handleCompleteEvent`, and poll paths.

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
  tests/test_flash_sources.py \
  tests/test_flash_grounding_honesty.py \
  tests/test_wave0_sources_honesty.py \
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
