# Architecture Audit — turbo-cdi (c4reqber)

**Scope:** whole project — ~228k LOC Python (`src/`, 91 packages), ~98k LOC tests, Go TUI v9, deployment/infra, docs.
**Method:** 6 parallel evidence-grounded audits (module topology, core/pipeline, patterns/simulations, API/infra, LLM/agents/knowledge, deps/tests/rewrite-readiness), each building real import graphs and grepping for evidence.
**Date context:** stabilization phase; a long-term Agda-core + Python-workers rewrite is parked. Recovery tag `pre-reorg-baseline`.

> This is a **reference document**. It records findings; it does not change code (except its own existence). Fixes are tracked separately. The TUI-v9 line-level audit (batch 1) is already landed on this branch; this document is the *project-wide architectural* layer.

---

## 0. 🔴 URGENT — committed live secrets (act before anything else)

`archive/harness/value-keys.tex` is **tracked in git** (since commit `bcf299d`, v5.6.0) and **not** gitignored. It contains real, correctly-formatted credentials: an OpenRouter key, a **PyPI publish token** (`pypi-…`), a **Telegram bot token**, NOWPayments/NVIDIA/XAI/Brave/Exa/Tavily-style keys (~16 secret lines), and crypto wallet addresses. Several are self-labelled "PERSONAL TESTING".

**These must be treated as compromised.** Required actions, in order:
1. **Rotate every credential** in that file now (the PyPI token especially — it can publish packages under the maintainer's account).
2. Remove the file and add `archive/harness/value-keys.*` (and a broader secrets glob) to `.gitignore`.
3. **Scrub git history** (`git filter-repo --path archive/harness/value-keys.tex --invert-paths`) and force-push — a normal delete leaves the secrets in history.
4. Add a pre-commit secret scanner (gitleaks/trufflehog); the `.tex` extension slipped past the existing `*.txt`/key rules.

This is the single highest-priority item in the audit and is independent of all architectural work.

---

## 1. Executive summary

The codebase is large, feature-rich, and **healthier structurally than its own docs claim** — but it is dominated by one recurring failure mode: **fragmentation without a single source of truth**. The same concept is implemented 3–6 times in parallel at almost every layer (LLM routing ×6, pipeline/step models ×3, pattern base classes ×3, plugin registries ×3, dependency manifests ×5, ARCHITECTURE docs ×3 with 4 version numbers, API client contracts ×3 across 5 clients). Layered on top is a thick stratum of **dead/aspirational code** (the Phase-1 "subtraction" is real but unfinished) and a **packaging hack** (`from src.X` + `PYTHONPATH=src`, never installable) that blocks clean module boundaries.

The genuinely good news, which the rewrite plan can build on:
- The residual **8-package orchestration core is now an acyclic DAG** (`{agents,api,auth,discovery,litintel,pipeline,solver,validation}`) — better than the documented "24→8 still-cyclic".
- `C4State` is ~90% consolidated onto a single canonical `src/c4/state.py`.
- A `contracts/` foundation layer exists and the `SolvePipeline` protocol injection (in `validation/empirical_layer.py`) is the *right* pattern — it just isn't applied consistently.
- The **embeddings engine is clean and ~95% worker-boundary-ready**; `patterns/` is a near-clean leaf with one narrow async call site.
- Security *primitives* are sound and the dev-mode auth bypass is safe-by-default.

**Posture recommendation** (consistent with the owner's "Python is a tidy dead-end" stance): do not build the full 16-module contract scaffold on Python you intend to discard. Do the high-value, no-regret subset: rotate secrets, finish the subtraction, pick one import style, collapse the worst duplications to a single source of truth, and prove the worker boundary on `embeddings` + `patterns/simulations` only.

---

## 2. Cross-cutting themes (the patterns that repeat across dimensions)

### T1 — No single source of truth (fragmentation) · **the dominant theme**
| Concern | Parallel implementations | Evidence |
|---|---|---|
| LLM routing | 6+ routers (`ProviderRouter`, `LLMProviderRouter`, `DepthBasedRouter`, `ProviderAwareCoordinator`, `model_per_stage`, `model_catalog`) **+ 21 files calling `/chat/completions` raw** | `src/llm/*` |
| Pipeline "step" | 3 models: `PipelineStep(ABC)` (dead), `STEP_PLAN` function-table (live), free `step_xxx()` fns | `agents/pipeline/{steps/base.py,executor.py}` |
| Pipeline orchestrator | 4 modes / 3 phase families: `PipelineExecutor` (s1–s9), `HILDiscoveryPipeline` (A–G), `discovery_phases` (1–6), inline flash/factory in `cli/` | `agents/`, `pipeline/`, `cli/blast_core.py` |
| Pattern base class | 3: `SimulationPattern` (async), `BasePattern` (sync), base-less; bridged by reflection runner | `patterns/{core.py,library/base.py,runner.py}` |
| Plugin registry | 3: `unified_registry`, `v2_registry` (live), `registry` (legacy) | `src/plugins/*` |
| `C4State` type | 3 classes + 4 variants (Pydantic/API/journal) | `c4/state.py`, `contracts/c4_types.py`, `archetypes/data.py` |
| API wire contract | 5 clients, 3 styles (in-process import / hand JSON / hand Go structs); no OpenAPI codegen | §5 |
| Dependency manifest | 5: `pyproject.toml`, `requirements.txt`, `requirements-simple.txt`, `requirements.lock`, `uv.lock` | §7 |
| Architecture docs | 3 files, 4 version numbers claimed simultaneously | §7 |

The fix is always the same shape: **define one protocol/contract, make the rest strategies behind it.** This is also exactly what the Agda rewrite needs.

### T2 — Unfinished subtraction (dead/orphaned code)
Confirmed dead (fan-in 0 / no importers / no mounted router): top-level `v6/` (~62–118 files) and `v7/` (~17–22 files); `src/mcp` (deprecated shim shadowing the 3rd-party `mcp` SDK); `src/payments`, `src/radar`, `src/skills`, `src/tutorial`, `src/bots`; API middleware `policy.py`/`audit.py`/`rate_limit.py`; `src/observability/*`, `src/cache/*`, `src/infrastructure/logging` (zero live importers); `src/api/fast_metrics.py`, `v7_schemas`/`v8_schemas`; `patterns/library/loader.py` (points at deleted `v6.engine.*`) + `_registry.py`; `src/api/database.py`. Plus stale `v6_legacy` refs in `pyproject.toml:84,114`.

### T3 — Aspirational infra wired-but-inert
`/metrics` is mounted but its Prometheus counters are never incremented (exports zeros); OTel is never initialized; the 4-tier cache has no importers (only `api/cache.py` is live); WASM plugins are registered behind an explicit early-`return` (disabled by design) yet `plugin_stage_router` still references them; `PostgresDatabase` is a connect/ping stub with no CRUD and silently falls back to SQLite.

### T4 — Worker-boundary readiness (for the parked rewrite)
- **Embeddings: ~95% ready.** Single `EmbeddingEngine` singleton, all heavy deps (sentence-transformers/sklearn/chromadb) lazy-imported. Lowest-risk first carve. Blocker: `NoveltyScorer` loads a *second* model — unify first.
- **patterns + simulations: structurally ready, contractually not.** `patterns/` is a near-clean leaf (only `di.container`, `utils.safe_eval`, lazy `simulations.newton_bridge`); the pipeline touches it through one async chokepoint `get_runner().run_pattern(...)`. But there is **no serializable result contract** — `SimulationResult.data: dict[str,Any]` leaks raw numpy arrays (only ~59/107 patterns `.tolist()`), and the runner dispatches via `inspect.signature` reflection that cannot cross a process boundary. There is a real `patterns↔simulations` cycle to break first.
- **Blockers (project-wide):** no process/RPC boundary exists at all; only 26 `BaseModel` classes across 228k LOC (contract poverty); the `from src.X` packaging hack means you cannot cleanly `pip install` a carved-out worker.

### T5 — Packaging is a `PYTHONPATH` hack (structural blocker)
`from src.X` (415 files / 679 stmts) coexists with relative imports (501) and 6 bare imports, working *only* because `src/__init__.py` exists **and** `pytest.ini` sets `pythonpath = src`; 7 `conftest.py` files inject `sys.path` manually. The package is never installed (no egg-info in the venv); `[project.scripts] = src.cli.blast_app:app` would break under a real `pip install`. This is the prerequisite for any clean boundary or worker carve.

---

## 3. Module topology & dependency health

- **8-package core = clean DAG, no cycles** (Tarjan over the core). Layering is correct: `api` at top, `validation` is the universal sink. Essential coupling, not accidental.
- **Remaining whole-graph cycles:** (1) `{agent,cli,codegen,mcp_server}` — a *genuine* entrypoint cycle, already papered over with function-local imports (the shared `cmd_solve/turbo/flash`, `auto_route`, `AgentCore`, `c4_codegen` handlers); fix by extracting them into a one-directional `commands` core. (2) `{patterns,simulations}` — small, essential, move-as-a-pair behind the worker boundary. (The `src/mcp` 5-node SCC was a false positive — name collision with the `mcp` SDK.)
- **Hubs:** fan-in leaders `di` (23), `c4` (17), `llm` (14) = de-facto shared kernel; fan-out leaders `api` (28), `mcp_server` (22), `agents` (20).
- **Naming duplication (quantified):** `core`(13)→`c4`(37) merge **incomplete** (core still imported by cli/pipeline/agents/api); `agent`(7, CLI exoskeleton) vs `agents`(55, solve engine) **distinct but confusingly named**; `mcp`(shim) vs `mcp_server`(live); `terminal_`(3, theme) fold into `tui`/`cli`; `metamodels`(live) vs `meta_layer`/`metaprograms` (orphaned).
- **`di` is the one seam that works** (2 files, fan-in 23) — but it's a global service-locator, disjoint from the API's `Depends()` (two parallel wiring mechanisms that never meet).
- **`contracts`/`infrastructure`/`adapters` are under-adopted** — the *intended* Agda contract boundaries exist but aren't load-bearing; only ~6 files use `contracts`.

**Highest-leverage moves:** delete the dead packages (pure subtraction, fan-in-0 verified); break the entrypoint cycle via a `commands` core; finish `core→c4`; carve `patterns+simulations` behind the worker boundary; make `contracts` types load-bearing on the core DAG's 15 edges.

---

## 4. Core domain & pipeline orchestration

- **Dual step abstraction, one dead** (CRITICAL): every step defines both a `XxxStep(PipelineStep)` ABC *and* a free `step_xxx()` fn; all 10 ABCs are **never instantiated** — the engine uses a string-keyed `importlib` table (`STEP_PLAN`). Pick one (the protocol is the right Agda target); delete the other.
- **`PipelineExecutor.execute()` is a 233-line god-function** with hardcoded `if step_id == "s8"/"s2d"/"s9"` branching over a mutable `state: dict` + callback channel. Split into `StepRunner` / `ObserverOrchestrator` / `ModePolicy` (declarative per-mode rules). This is where the historical phase-C hangs lived.
- **Four modes, no shared spine:** solve (`PipelineExecutor`), turbo (`HILDiscoveryPipeline`, phases A–G), flash+turbofactory (**inline `async def _run()` inside `cli/blast_core.py`**, untestable without the CLI; turbofactory uses a raw `Semaphore`, ignoring the existing `SmartScheduler`), API discovery (`discovery_phases` 1–6). Define one `Phase`/`Pipeline` contract in `contracts`; move flash/factory out of `cli/`.
- **pipeline→agents still crosses via `importlib.import_module("src.agents.functor_orchestrator")`** in `hil_phases/phase_d_agents.py` — an untyped runtime boundary. Replace with a `CognitiveAgentRunner` protocol injected from the composition root (copy the `SolvePipeline` pattern that's already done right).
- **`BasePipeline` is an infra grab-bag** (quality gates + event bus + EventStore + Saga + CQRS + observer) lazy-imported to dodge cycles. Demote to data+events; push transactional infra behind opt-in ports.
- **C4State ~90% consolidated** but `contracts/c4_types.py:C4State` is *dead in the foundation layer* (only a test imports it) — the opposite of intended; promote `c4/state.py` into `contracts` or delete the contracts variant; rename `archetypes.data.C4State`→`C4Archetype`.
- **Error/timeout/cancel is per-call, not policy-driven** — every phase hand-picks `asyncio.wait_for(timeout=N)`; turbofactory has no per-pipeline timeout. Introduce one injected `ExecutionPolicy`.
- God-modules to split: `discovery/pipeline_logic.py` (1011 LOC, 28 fns, mixes LLM/causal/Bayes/LaTeX), `discovery/falsifier.py` (833), `pipeline/redundant_gates.py` (738, 12 gates repeat parse+retry).

---

## 5. API / service layer, infra & the polyglot boundary

- **No single wire contract; the Go SSE decoder has drifted from the backend by 13 event types.** `tui/v9/api/sse_typed.go` knows 16 event types; the backend (`v8_routers/discovery_v8.py`) emits only `phase`/`complete`/`error`, **without** the `type` field the Go decoder dispatches on (a `status`-inference fallback masks it). The two Go TUIs target *different* prefixes (`/api/v1`+`/v8` vs `/api/v8`). **Fix:** OpenAPI → `oapi-codegen` for Go; a versioned typed SSE event schema emitted by Python and decoded by Go.
- **Versioning sprawl:** ~104 routes across `/api/v1/*` (15 legacy routers) + `/v8/*` (12 sub-routers), inconsistent prefixes; duplicate v8 verification routers. Collapse to one scheme.
- **Two parallel JWT paths** that disagree: a global middleware doing raw `jwt.decode` (no issuer/revocation check) vs `AuthManager.decode_token` (full checks) used by `Depends`. Route all verification through `AuthManager`. CORS is mounted **twice**. The dev-mode bypass *is* safe-by-default (needs `DEV_MODE=true` + configured token + HMAC-compared header) — keep it as the model.
- **Persistence reality vs scaffolding:** the app is single-process SQLite; `k8s/` declares 3–20 replicas sharing one RWO PVC with a SQLite file (unsafe), references a Redis with no manifest, and omits `JWT_SECRET`/`CSRF_SECRET` (the app can't even construct without `CSRF_SECRET`). `PostgresDatabase` is a stub; `init.sql` (Postgres DDL) has drifted from the inlined SQLite schema; `alembic.ini` exists with no `alembic/` dir. `SQLiteDatabase.disconnect` doesn't exist → AttributeError every shutdown. **Own SQLite (drop the k8s/Postgres scaffolding) or implement Postgres — don't straddle; fail loud on misconfig.**
- **Config is fragmented:** ~134 files read `os.getenv` directly; no `pydantic-settings` Settings object despite the dep being present.

---

## 6. LLM / agents / knowledge / RAG / MCP / plugins

- **No native provider SDK anywhere.** Every cloud model — including Claude — is reached as an OpenAI-compatible `/chat/completions` POST, mostly hard-pointed at OpenRouter. Providers wired: OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Ollama, LM Studio (byte-identical clients differing only by enum). **No `api.anthropic.com` path**, so no Anthropic-native features (prompt caching, `anthropic-version`) and OpenRouter routing cost on the heavy synthesis/dissertation phases.
- **6+ routers + 21 raw call sites** (CRITICAL, see T1): cost-tracking, retries, the guardian safety scan, and caching apply only on whichever path is used. **Fix:** one `LLMGateway` protocol as the sole entry-point; routers become strategies; add a native Anthropic backend behind it.
- **Claude/model IDs are inconsistent across the 5 routing tables** (`claude-3.5-sonnet` vs `sonnet-4.5` vs `4.6` vs dated `-4-20250514`), so the same logical stage resolves to different versions by code path; `cost_tracker` only knows `claude-3.5` and mis-prices Claude-4.x. Centralize on `model_catalog.py`.
- **Embeddings/RAG is the clean subsystem** — single `EmbeddingEngine` singleton, lazy deps, all semantic ops (dedup/evidence/cluster/coverage) route through it; ChromaDB-backed knowledge cache. The worker-boundary winner. (Caveat: `NoveltyScorer` loads a *second* SentenceTransformer — unify.)
- **3 plugin registries** + WASM registration **disabled by an explicit early-`return`** while `plugin_stage_router` still lists the WASM tools (phases silently fail to find them). Collapse to one registry; finish or delete WASM.
- **MCP healthy:** `src/mcp_server` is live (21 tools, official SDK + JSON-RPC fallback); `src/mcp` is a dead shim. `FunctorOrchestrator` is a *real* composable abstraction (9 functors + 18 composed `outer∘inner`, parallel via `asyncio.gather`); but `MultiAgentSystem` is heuristic keyword rules, not LLM-driven — wire or rename. Duplicate `AgentRole` enums to consolidate.
- **Prompts** mostly centralized (`agents/functors/prompts.py`) but ~12 inline literals remain and there's no prompt versioning/eval binding.

---

## 7. Deps, tests, docs, maintainability

- **5 competing dependency manifests; `pyproject.toml` is not a valid superset** — it omits `networkx`, the whole `sqlalchemy/alembic/asyncpg/redis` DB stack, `scikit-learn`, `cryptography`, `sentence-transformers`, and pins almost nothing. `requirements.txt` is the de-facto source of truth (unpinned). Heavy optionals (torch/wasmtime/numba/jax) are correctly guarded in code, so a `core` + `[project.optional-dependencies]` extras split is achievable — `z3` and `gensim` are the two heavies that are **not** guarded despite being described as optional. **Make `pyproject` the single source; delete the other manifests; generate a lock.**
- **Test pyramid: sane but bottom-heavy.** Strong unit base mirroring `src/`; the `integration` marker is used by **0 tests**; `tests/e2e/` has 2 files (one opt-in, one assert-less); fast/full split is aspirational (`-m "not slow"` removes 2 tests). Biggest holes: `src/agents/` orchestration core (55 files, ~1 test), `src/api/routers/` (0 dedicated tests), error/timeout/circuit paths. `fail_under=60` is lenient.
- **Docs are a version graveyard:** `AGENTS.md` (v9.13.0), `docs/ARCHITECTURE.md` (v5.4.0/v5.3.9), `ARCHITECTURE_C4R.md` (v5.6.0) claimed at once; `AGENTS.md`'s "REMOVED" list names files that still exist; `ARCHITECTURE_C4R.md` points the TUI at non-existent `src/tui/v7/`. Pick one canonical doc, date the rest.
- **`.gitignore` over- and under-ignores:** `models/`, `migrations/`, `k8s/` are blanket-ignored yet contain **tracked** real source (future files silently dropped); the `*.txt` over-ignore was only just patched for the v9 goldens. ~8 MB of committed binary bloat (Russian-named PNG screenshots in `archive/harness/`, PDFs, `coverage.out`, duplicated WASM binaries in both `wasm/plugins/` and `wasm_plugins/`).
- Hardcoded dev paths `/Users/figuramax/...` in `tui/v9/i18n/pipeline/translate_hymt.py` and `quality_score.py`.

---

## 8. Agda-rewrite readiness verdict

**Not ready — and deliberately don't over-invest.** The intended end-state (pure Agda core + Python numeric workers behind a process + serializable contract) needs three seams the code lacks:
1. **No worker/process boundary exists** — the ~50 `simulations/*_bridge.py` engines are called in-process. The one template to generalize is `src/wasm/runtime.py` (clean Protocol + stub fallback), but it's an island.
2. **Contract poverty** — only 26 `BaseModel` classes, no protobuf/schema at module seams; boundaries are Python calls, not serializable messages.
3. **The pure-logic core isn't isolated** — `src/agents` (the would-be Agda core) is I/O-entangled, least-tested, and mostly `mypy: ignore_errors`.

**Cleanest carve candidates (already narrow, value-in/value-out, guarded deps):** `embeddings` (≈95% ready), `patterns+simulations`, `verification/hoare_verifier`, `wasm/runtime`. **Recommended minimal path:** Phase-1 subtraction → rotate leaked keys → one import style/installable package → one `Settings` object → prove a single serialized worker contract around `embeddings` (then `patterns`) as the POC seam. Then stop.

---

## 9. Prioritized recommendation backlog

**P0 — security/correctness, do now**
1. Rotate the leaked credentials + scrub `archive/harness/value-keys.tex` from history; add a secret scanner. (§0)
2. Fix `SQLiteDatabase.disconnect` AttributeError on shutdown. (§5)

**P1 — no-regret subtraction & single-source-of-truth (high value, low risk)**
3. Delete confirmed dead packages: `v6/`, `v7/`, `src/mcp`, `payments/radar/skills/tutorial/bots`, dead middleware, `observability/cache/infrastructure-logging`, `patterns/{loader,_registry}.py`, `fast_metrics`, `v7/v8_schemas`, stale `v6_legacy` config. (T2)
4. Make `pyproject.toml` the single dependency source (core + extras); delete the other 4 manifests; pin via one lock. (§7)
5. Designate one canonical ARCHITECTURE doc; date/retire the rest; fix the stale "removed"/`tui/v7` claims. (§7)
6. Narrow the `.gitignore` over-ignores (`models/`, `migrations/`, `k8s/`, `*.txt`). (§7)

**P2 — collapse the worst duplications behind one contract**
7. One `LLMGateway` protocol; migrate the 21 raw call sites; add a native Anthropic backend; centralize model IDs + cost table. (§6)
8. One pipeline `Step`/`Phase` contract; delete the dead ABC duplication; move flash/factory out of `cli/`; replace the `importlib` agent boundary with an injected protocol. (§4)
9. One plugin registry; finish or delete WASM. (§6)
10. One JWT path (`AuthManager`); mount CORS once. (§5)
11. One typed wire contract (OpenAPI/codegen) for the 5 API clients + a versioned SSE event schema. (§5)

**P3 — packaging & worker-boundary POC (enables the rewrite, but bounded)**
12. Pick one import style; make `src/` an installable package (`c4reqber/`, `pip install -e .`). (T5)
13. Introduce one `Settings(BaseSettings)` config seam. (§5/§7)
14. Prove the worker boundary on `embeddings` (unify `NoveltyScorer` first), then `patterns+simulations` (uniform base class + JSON-safe `SimulationResult`, break the cycle). (T4)

**P4 — finish the in-place reorg (per CLAUDE.md Phase 1)**
15. Finish `core→c4`; break the `agent↔cli↔codegen↔mcp_server` cycle via a `commands` core; make `contracts` load-bearing on the core DAG; split the named god-modules. (§3/§4)

---

*Generated from a 6-dimension parallel architectural audit. Every claim above is grounded in import-graph/grep evidence captured during the audit; see the per-dimension sections for file:line references.*
