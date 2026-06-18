# Rework Plan — turbo-cdi (c4reqber)

**Companion to [`ARCHITECTURE_AUDIT.md`](./ARCHITECTURE_AUDIT.md).** The audit records *what* is wrong; this is the *living plan* for fixing it.

## How to use this document
- This is the **skeleton** (full scope, phase-level). Each consolidation gets a detailed **mini-plan** (target interface, call-site map, migration steps, test strategy) written **just before it is executed**, appended under its item below.
- Stable item IDs (e.g. `P2-A`) are referenced from commits and discussion.
- Every code change is **test-gated**: the Go TUI suite + the Python logic suite (`-m "not slow"`, excl patterns/simulations) stay green; consolidations add a regression test that locks the single-source invariant.
- Tags: **[no-regret]** = valuable whether or not the Agda rewrite ever happens · **[conditional]** = only worth it if we keep investing in the Python.
- Guiding owner constraint: "Python is a tidy dead-end." Bias toward subtraction and no-regret consolidation; avoid building scaffold on code we may discard. (Appetite for this round: **full plan**, per decision 2026-06-18.)

## Status snapshot
- ✅ **TUI v9 line-level audit + fixes (batch 1)** — landed (`f7424a1`): SSE leak, palette, keymap g/G, persistence, golden-fixtures gitignore. Green on clean checkout.
- ✅ **Project-wide architectural audit** — landed (`be4f752`, `ARCHITECTURE_AUDIT.md`).
- ✅ **Duplication clusters verified against code** — see below.
- ⏳ **This plan** — skeleton committed; execution not started.

---

## The core problem (verified): "one thing, implemented N times in parallel"

Each cluster below was **verified directly against the code** (import counts, instantiation checks), correcting a few imprecise audit claims. The fix recipe is identical for all: **define one protocol → make the rest strategies behind it → migrate N call-sites → delete the dead ones.** These are also the exact contract seams the Agda rewrite would need.

| ID | Cluster | Verified reality | Canonical target | Dead (delete) | Migration scope | Risk |
|---|---|---|---|---|---|---|
| **A** | LLM routing | 3 live entrypoints: `ProviderRouter` (13 importers), `AsyncLLMClient` (7), `LLMProviderRouter` (5); name-collision dups (`ProviderRouter`×2, `LocalLLMClient`×2); **21 raw `/chat/completions` sites** bypassing all routing/cost/retry/safety | one `LLMGateway` protocol; keep the 6 `BaseLLMClient` provider subclasses as the provider layer; routers → strategies | `UnifiedLLMClient` (0 importers) | ~28 importer-files + 21 raw sites | medium |
| **B** | Pipeline step model | each of 15 steps defines `class XxxStep(PipelineStep).execute()` (**real impl**) **+** a free `step_xx()` wrapper; executor's `STEP_PLAN` calls the wrappers by string via `importlib`. **NOT dead code — a redundant indirection layer.** | executor instantiates `PipelineStep` classes via a registry directly; drop the free-fn wrappers + `importlib` + string `STEP_PLAN` | — | 15 steps + `executor.py` | medium (live solve engine) |
| **C** | Pipeline orchestrators | 4 modes / 3 phase families: solve=`UniversalSolvePipeline`, turbo=`HILDiscoveryPipeline` (A–G), API=`discovery_phases` (1–6), **flash + turbofactory inline in `cli/blast_core.py`** (raw `asyncio.Semaphore`, ignores `SmartScheduler`) | one `Pipeline`/`Phase` contract; all 4 modes compose over it; move flash/factory out of `cli/` | — | all 4 modes | high (user-facing) |
| **D** | Pattern base class | 3 groups: `SimulationPattern` (async) 56 subclasses, `BasePattern` (sync) 7, base-less 44; `runner.py` bridges via `inspect.signature` reflection; result `data: dict[str,Any]` leaks raw numpy (only ~59/107 `.tolist()`) | one ABC `run(hypothesis, config)->SimulationResult` + **serializable-by-construction** result | `loader.py`, `_registry.py` | 107 patterns (mechanical) + runner | medium, high volume |
| **E** | Plugin registry | 3 live: `registry` (5 ext importers), `v2_registry` (5), `unified_registry` (1); pipeline uses registry+v2, CLI uses all three, MCP uses registry+unified | one registry (subsume v2+legacy) | — | ~11 call-sites | low-medium |
| **F** | C4State | `c4.state.C4State` (30 ext importers) = canonical; `contracts.c4_types.C4State` (**0 importers — dead in the foundation layer**); `archetypes.data.C4State` (1 importer, a *different* concept) | `c4.state` canonical (optionally promote into `contracts`); rename archetype variant | `contracts.c4_types.C4State` | delete 1 + rename 1 + add deprecation on shims | low |
| **G** | Manifests / docs | 5 dependency files disagree (`pyproject` not a superset); 3 ARCHITECTURE docs claim 4 versions | `pyproject.toml` = single dep source (core + extras); one canonical ARCHITECTURE doc | 4 redundant manifests, stale docs | config + docs | low |

### NOT duplication — explicitly do **not** merge
- `src/agent` (CLI agent-mode: `AgentCore`/`AgentConfig`) vs `src/agents` (solve engine: `FunctorOrchestrator`/multi-agent) — **distinct subsystems** sharing a confusing name → **rename** `agent`→`agent_mode`/`exoskeleton`, don't merge.
- `metamodels` (live) vs `meta_layer` / `metaprograms` (distinct, two orphaned) — not dups; evaluate orphans for deletion, don't merge.
- The 6 `BaseLLMClient` provider subclasses — legitimate provider layer, keep.
- `C4StateItem` (API schema), `C4StateFrame`/`C4StateJournal` (journal) — legitimately distinct types, keep.

---

## Phased plan (full scope)

Dependency summary: **B → C** (step protocol before orchestrator spine); **D** interleaves with Phase 4 (worker boundary); everything else is independent. Phase 1 (subtraction) goes first and simplifies Phase 2.

### Phase 0 — Security & correctness · *[no-regret]* · do now
- **P0-1** Rotate the leaked credentials in `archive/harness/value-keys.tex`; remove the file; scrub git history (`git filter-repo`); add a secret scanner (gitleaks pre-commit). *(Owner action for rotation + history rewrite; I can stage the removal + .gitignore + scanner config.)*
- **P0-2** Fix `SQLiteDatabase.disconnect` AttributeError on shutdown (add no-op `connect`/`disconnect`).

### Phase 1 — Subtraction (delete confirmed-dead) · *[no-regret]*
Each deletion re-grep-verified (fan-in 0 / no mounted router) immediately before removal.
- **P1-1** Top-level legacy trees: `v6/`, `v7/` (not imported by src; `tests/test_v6_patterns.py` may reference — check).
- **P1-2** `src/mcp` deprecated shim (shadows the `mcp` SDK; 0 importers).
- **P1-3** Dead leaf packages: `payments`, `radar`, `skills`, `tutorial`, `bots`.
- **P1-4** Dead API middleware: `policy.py`, `audit.py`, `rate_limit.py`; dead infra `observability/*`, `cache/*`, `infrastructure/logging`, `api/fast_metrics.py`, `api/database.py`, `v7_schemas`/`v8_schemas`.
- **P1-5** Dead numerics scaffolding: `patterns/library/loader.py`, `patterns/library/_registry.py`; stale `v6_legacy` refs in `pyproject.toml:84,114`.
- **P1-6** Dead LLM class `UnifiedLLMClient`; dead foundation type `contracts.c4_types.C4State`.
- **P1-7** `.gitignore` hygiene: narrow the over-ignores (`models/`, `migrations/`, `k8s/`, `*.txt`) that silently drop tracked source.
- **P1-8** Committed binary bloat (~8 MB): screenshots/PDFs/`coverage.out`/duplicated WASM binaries → gitignore + remove.

### Phase 2 — Single-source consolidations · ascending risk
- **P2-F** **C4State finish** *(F)* — *[no-regret]*. Delete `contracts.c4_types.C4State`, rename `archetypes.data.C4State`→`C4Archetype`, deprecate the re-export shims. Quick win, low risk.
- **P2-E** **One plugin registry** *(E)* — *[no-regret]*. Make one registry canonical; repoint pipeline/HIL/CLI/MCP imports; resolve or delete the WASM path so `plugin_stage_router` stops referencing phantom tools.
- **P2-A** **LLM `Gateway`** *(A)* — *[no-regret]*. Define `LLMGateway` protocol (`generate(prompt, stage, ...) -> LLMResponse`) as the sole entry; routers become strategies; migrate the 21 raw sites; centralize keys/cost/retry/guardian; centralize model IDs on `model_catalog`; add a native Anthropic backend; fix Claude-4.x cost table.
- **P2-B** **Step model → protocol** *(B)* — *[conditional]*. Executor drives `PipelineStep` via a registry; remove free-fn wrappers + `importlib` + string `STEP_PLAN`. **Prereq for P2-C.**
- **P2-C** **Orchestrator spine** *(C)* — *[conditional]*. One `Pipeline`/`Phase` contract in `contracts`; express solve/turbo/flash/factory as compositions; move flash/factory out of `cli/`; one injected `ExecutionPolicy` (timeout/retry/cancel); replace the `phase_d_agents` `importlib` boundary with an injected `CognitiveAgentRunner` protocol.
- **P2-D** **Pattern base + serializable result** *(D)* — *[conditional; partially no-regret as worker-POC]*. One ABC + JSON-safe `SimulationResult`; migrate 107 patterns; delete the reflection runner; break the `patterns↔simulations` cycle.

### Phase 3 — Contracts for polyglot / rewrite · *[conditional]*
- **P3-1** One typed wire contract: FastAPI OpenAPI → `oapi-codegen` (Go) + Python client; versioned typed SSE event schema emitted by backend, decoded by TUI (fixes the 13-event Go drift). Collapse `/api/v1` vs `/v8` prefix sprawl.
- **P3-2** One auth path (`AuthManager`); mount CORS once.
- **P3-3** Persistence decision: own SQLite (drop k8s replicas/HPA/Postgres/alembic scaffolding) **or** implement Postgres CRUD + real Alembic; fail loud on misconfig.
- **P3-4** Packaging: one import style; make `src/` an installable package (`c4reqber/`, `pip install -e .`); one `Settings(BaseSettings)` config seam.
- **P3-5** **G** — `pyproject.toml` single dep source (core + `[project.optional-dependencies]`); delete the other 4 manifests; one lock. Designate one canonical ARCHITECTURE doc; fix stale claims.

### Phase 4 — Worker-boundary POC (the Agda-rewrite payoff) · *[no-regret as proof]*
- **P4-1** `embeddings` worker (~95% ready): first unify `NoveltyScorer` onto the single `EmbeddingEngine`; then move `embed(list[str])->ndarray` behind a process + serializable contract.
- **P4-2** `patterns + simulations` worker: depends on **P2-D** (serializable result) + breaking the cycle; swap the one `get_runner().run_pattern(...)` chokepoint for `submit_to_worker(...)`. Also fixes the un-interruptible Jansen-Rit/connectome C-loops (killable as a separate OS process).

---

## Sequencing recommendation
1. **P0** (security) — immediately, in parallel with everything.
2. **P1** (subtraction) — first code work; low risk, shrinks the surface for P2.
3. **P2-F, P2-E** (quick no-regret consolidations) → **P2-A** (LLM gateway, biggest value).
4. **P2-B → P2-C** (step protocol → orchestrator spine).
5. **P3** (contracts/packaging) and **P2-D + P4** (pattern contract → worker POC) as the final, rewrite-facing tracks.

Each item ships as its own branch/commit, test-gated, with its mini-plan appended here at execution time.

---

## Mini-plans (filled in at execution time)
*(none yet — to be appended per item as work starts)*
