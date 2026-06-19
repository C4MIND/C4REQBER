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
- ✅ **P0 (security/correctness code parts), P1 (subtraction, 155 files), P2-F, P2-E** — landed (`fix/tui-v9-audit-batch1`).
- ✅ **P2-A track A1 (LLM gateway, equivalence-preserving)** — done; facade + 13 characterization tests + all ad-hoc callers migrated + dead routing/model-table deleted. A2 owner-gated, not started. See mini-plan.
- ✅ **P2-B (step model → PipelineStep registry)** — done; killed importlib/STEP_MODULES/step_definition dispatch + 14 free-fn shims, drives typed classes directly. Fast dispatch net + real-step e2e green. See mini-plan.
- ⚠️ **P2-C (orchestrator spine)** — REVISED: the "one spine for 4 modes" premise fails the safety gate (the 4 modes are genuinely different, not N copies). Recommend **skipping** the grand unification; remaining items are cosmetic/optional. See revised P2-C.
- ⏳ **Next** — owner's call: P2-D (pattern ABC + serializable result → worker-POC), A2 (LLM cross-cutting, owner-gated), or stop. P0 owner-actions (rotate secrets, scrub history, `pre-commit install`) still pending.

---

## The core problem (verified): "one thing, implemented N times in parallel"

Each cluster below was **verified directly against the code** (import counts, instantiation checks), correcting a few imprecise audit claims. The fix recipe is identical for all: **define one protocol → make the rest strategies behind it → migrate N call-sites → delete the dead ones.** These are also the exact contract seams the Agda rewrite would need.

### ⚠️ Consolidation safety gate (mandatory — lesson from the plan-audit)
"N implementations of the same thing" **silently assumes they are behaviorally equivalent.** Often they are NOT — they are divergent implementations that evolved separately, and the differences encode intent, fixes, or coverage. Collapsing them naively *loses* those differences. So **before** any consolidation:
1. **Behavioral diff** the N implementations — actually run them (compare registered sets / outputs / method sources; for routers, enumerate which features each has), don't eyeball.
2. **Classify each difference**: `cosmetic` (drop freely) · `intentional divergence` (preserve in the union) · `bug-fix-in-one-only` (canonical must adopt the fixed behavior).
3. **Preserve the union** of intentional behaviors — OR explicitly justify dropping one *in the commit message*.
4. **Lock it** with a regression test capturing the preserved behavior.

Audit status of consolidations done so far: **P2-E verified equivalent post-hoc** (plugin IDs 28≡28; `select_plugins_for_problem` identical 20/20 across problems×modes; `WebSearchPlugin` differs only by a removed docstring/comment — same stub body). **P2-F** is a pure rename (no behavior). Both safe — but P2-E was *asserted* a "superset" before being *proven* one; that ordering is the gap this gate closes.

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
- **P2-F** **C4State finish** *(F)* — ✅ done (`fix/tui-v9-audit-batch1`). **Careful-analysis correction:** `contracts.c4_types.C4State` is NOT a deletable duplicate — it's used by `C4Space.navigate()` and `C4Path.states` in the same foundation module (a self-consistent T/S/A contract scaffold, only its own test imports it), so it was **left as-is**, not deleted (the audit overstated it). The genuine collision was `archetypes.data.C4State` — actually archetype *metadata* (code/time/scale/agency strings, name_en/name_ru, metaphor, strengths, color; the 27 named archetypes), not the canonical computational state. **Renamed → `C4Archetype`** across 4 files (`archetypes/{data,engine,__init__}.py`, `api/agents_router.py`; engine.py done carefully since it imports the canonical as `CanonicalC4State`). `c4.state.C4State` stays canonical (30 importers, untouched). 13 targeted tests + import-guard green.
- **P2-E** **One plugin registry** *(E)* — ✅ done (`fix/tui-v9-audit-batch1`). **Careful-analysis finding:** the consolidation was already half-built — `unified_registry.py` is a complete drop-in **superset** (module-level `PLUGIN_REGISTRY` singleton with full dict API `get/items/values/keys/__getitem__/__contains__/...`, plus every symbol consumers used: `WebSearchPlugin/ToolMetadata/PluginInfo/select_plugins_for_problem/execute_plugin/...`), but the migration to it was never finished. So it was **pure import repointing**, no API adaptation. Decisions (owner): canonical = `unified_registry`; WASM stubs = delete.
  - Repointed all 12 import sites (CLI/pipeline/HIL/MCP/dag/steps) from `registry`/`v2_registry` → `unified_registry`; deleted `src/plugins/{registry,v2_registry}.py`.
  - WASM: removed the 4 dead `@wasm` stub registrations (they never actually registered — Python registration was disabled-by-design, registry stays at 28 plugins) + stripped the phantom WASM ids (monte_carlo_pi/matrix_mult/text_distance/hash_fingerprint) from `plugin_stage_router` PHASE_PLUGINS/ALL_COMPUTE_PLUGINS. Kept the `.wasm` artifacts + `wasm/runtime.py` (revivable). Replaced the now-stale `test_wasm_plugins_present_in_source` with a regression test `test_wasm_stubs_not_registered` locking the removal.
  - Verified: plugin tests 49 passed, import-guard green, full logic suite green.
- **P2-A** **LLM `Gateway`** *(A)* — *[no-regret core]*. **⚠️ This is the consolidation-safety-gate's hardest case: the routers are NOT copies, they are genuinely divergent** (verified in the plan-audit):
  - **Guardian safety scan** is in `LLMProviderRouter` + `AsyncLLMClient` but **absent in `ProviderRouter`** (the most-used, 13 importers) and all 21 raw sites → inconsistent coverage.
  - **Retry/reliability**: THREE different strategies — `ProviderRetryManager` (11-provider backoff, only ProviderRouter) vs unified's 3-provider fallback chain vs async_client's own.
  - **Stage→model routing**: FOUR disagreeing tables (router presets, `model_per_stage`, `model_catalog`, `depth_router`) with different Claude versions per phase.
  - **Mandatory sub-step before code**: a *behavior inventory* of each router → reconcile into the gateway as the **union** (guardian for all; one explicit retry policy; **one** deliberate stage→model table). The stage→model reconciliation is a **product decision (owner): which model per phase** — not a mechanical merge. Then: `LLMGateway` protocol as sole entry; routers/raw-sites migrated behind it; centralize keys/cost/retry/guardian; fix Claude-4.x cost table. Native Anthropic backend = separate opt-in scope (feature, not consolidation).
- **P2-B** **Step model → protocol** *(B)* — *[conditional]*. Executor drives `PipelineStep` via a registry; remove free-fn wrappers + `importlib` + string `STEP_PLAN`. **Prereq for P2-C.**
- **P2-C** **Orchestrator spine** *(C)* — ⚠️ **REVISED 2026-06-19 — the "one spine" premise does NOT survive the safety gate; do NOT force it.** Characterization (`blast_core.py`): the 4 modes are *genuinely different things*, not N copies of one orchestrator —
  - `solve` → `UniversalSolvePipeline` (12-stage `PipelineStep` registry, just rebuilt in P2-B)
  - `turbo` → `HILDiscoveryPipeline` (`src/pipeline/hil_pipeline.py`, 254 LOC, a *different* CommandHandler/phase architecture — no `PipelineStage`/`STEP_PLAN` overlap)
  - `flash` → a quick LLM answer (~220 LOC inline; not a multi-phase pipeline at all)
  - `turbofactory` → a parallel *runner* that fans out N solve/turbo pipelines + aggregates (not itself a pipeline)
  Collapsing these into one `Pipeline`/`Phase` contract = inventing a false abstraction over genuinely different control-flows (the exact safety-gate failure the owner flagged). What the audit *actually* found here is shallow/optional, not a no-regret consolidation:
  - **`phase_d_agents` `importlib`** (`hil_phases/phase_d_agents.py:29`) is **intentional late-binding** — it keeps the generic pipeline engine free of an import-time dependency on the agents package (documented + try/except-guarded). Converting it to an injected `CognitiveAgentRunner` protocol is *design polish*, not subtraction; low value vs the dead-end-Python stance.
  - **CLI-command boilerplate** (banner + `asyncio.run(_run())` + `inject_mascot_status` repeated across the 4 `cmd_*`) is *cosmetic* dedup (~a dozen lines).
  **Recommendation: skip the grand unification.** P2-B already delivered the real structural win (the solve spine). Spend effort on higher-value tracks (P2-D worker boundary / A2) instead.
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

### P2-A — LLM Gateway · mini-plan · **A1 ✅ done** (`fix/tui-v9-audit-batch1`)
**Decisions (owner, 2026-06-18):** scope = **consolidation only, keep OpenRouter** as the transport (no native Anthropic backend for now); goal = **behavioral equivalence to the existing system** (owner is still learning the code).

**Why equivalence reframes this:** the audit's "make the gateway apply guardian+retry+cost+cache to ALL paths" is a *behavior change* (paths that lack a feature would gain it — e.g. `ProviderRouter` calls would newly get guardian-scanned and could be blocked). That violates "equivalent to existing." So P2-A splits into two clearly separated tracks:

- **A1 — equivalence-preserving consolidation (this round, no-regret):** one `LLMGateway` *facade* that is the single entry, but each caller's path keeps its **current** model selection, retry strategy, and guardian-or-not — byte-for-byte behavior. The win here is structural: one entry point, dead/duplicate clients removed (`UnifiedLLMClient`, the `ProviderRouter`/`LocalLLMClient` name-collision dups), one model-ID source that **reproduces what each live path resolves to today** (not a new policy). The 21 raw `/chat/completions` sites are migrated to gateway calls that **reproduce their current direct-httpx behavior** (same model/params, no added cross-cutting).
- **A2 — cross-cutting unification (separate, opt-in, owner-gated):** apply guardian/cost/cache/one-retry-policy uniformly to every call. This is the audit's real prize but it **changes behavior** → defer; do it deliberately, per-concern, with the owner aware (e.g. "now every LLM call is guardian-scanned").

**The stage→model tables (4, disagreeing):** do NOT invent a canonical policy. For A1, first **determine which table each live path actually resolves through at runtime** and preserve exactly that. Centralizing model IDs = collapsing to one table whose values reproduce today's resolved models per path, not a redesign. (Owner deferred the policy decision: keep existing behavior.)

**Method = characterization-test-first refactor** (right tool when the owner doesn't fully know the code):
1. **Characterize**: for each live entrypoint + a sample of the 21 raw sites, capture what model/params/headers it resolves to today (via the fake-LLM harness from stab/12, asserting the outgoing request shape). These tests encode "current behavior."
2. **Introduce `LLMGateway` facade** that delegates to the existing strategies unchanged; characterization tests stay green.
3. **Migrate callers** to the facade one file at a time; each migration must keep its characterization test green (proves equivalence).
4. **Delete** the now-unused dead clients/dups + collapse the model-ID tables to one (values unchanged per path).
5. Regression test locking the single-entry invariant: no `/chat/completions` httpx call outside the gateway/provider layer.

**Risk:** medium — the 21 raw sites are the exposure. Mitigation: characterization test per site, migrate one at a time. **A2 not started until A1 ships and the owner okays each behavior change.**

#### A1 — outcome (owner closed A1, 2026-06-19)

**Shipped (all equivalence-preserving; full suite 5146 passed / 0 failed at every step):**
1. **Facade + safety net** — `src/llm/gateway.py` (`LLMGateway` Protocol + `DefaultGateway` + `get_gateway()`), 13 characterization tests (`tests/llm/test_gateway_characterization.py`) locking the wire behavior of all 3 entrypoints (ProviderRouter stage-routing, AsyncLLMClient default-model+cache, LLMProviderRouter guardian+fallback) plus DefaultGateway-equivalence assertions.
2. **Dead-routing deletion** (step 2) — removed `src/llm/local/client_unified.py` (`UnifiedLLMClient`), `src/llm/routing/`, `src/llm/provider_router.py` + their tests; trimmed re-exports in `local_client.py`/`local/__init__.py`.
3. **Caller migration** — every **ad-hoc direct** caller now routes through the gateway:
   - group 1 (`discovery/{gap_miner,pipeline_logic}`, `api/v8_routers/discovery*`): `LLMProviderRouter.chat/chat_json` → `get_gateway().chat/chat_json`.
   - group 2 (`mcp_server/{server,blast_tools}`, `cli/blast_core`): `AsyncLLMClient()` → `get_gateway()` (6 sites).
   - group 3a-direct (`social/telegram_bot`, `verification/{semantic_alignment,formalization_engine,llm_prover}`, `discovery/closed_loop/refiner`, `exploration/{question_generator,formal_extender}`): `ProviderRouter()` → `DefaultGateway().generate_for_stage`; 5 test files repointed `_router.generate`→`generate_for_stage` (`e51a43d`).
4. **Dead model-table deletion** — `src/llm/model_per_stage.py` (84 LOC, parallel stage→model dup, 0 importers) removed (`0540d29`).

**Deliberately NOT done (owner decision):**
- **group 3a-injection** (functor system: `functor_orchestrator` + `functors/{base,composite}` DI-default + 9 sub-agents calling `.generate(stage,…)`/`.generate_batch(stage,…)` + the e2e `FakeProviderRouter`) — **skipped as zero-value/high-churn.** These are *not* a parallel reimplementation: they already use clean dependency-injection on the **canonical** `ProviderRouter` (which the gateway merely wraps). Migrating would force a `.generate`→`.generate_for_stage` rename across 9 agents, a new `generate_batch_for_stage` on the gateway, and an e2e-harness rewrite — for no behavioral or structural gain. The 3 remaining `ProviderRouter()` literals in `src/` are exactly these injection defaults; leaving them is correct.

**Boundary to A2 (still owner-gated, NOT started):**
- The remaining **live** stage→model tables (`model_catalog`, `router.py` PRESETS, `model_assignment`, `depth_router`) serve **different** live consumers (cli / embeddings / tui-budget). Collapsing them is a **behavior change**, not equivalence → A2. Step 5's "single-entry httpx regression test" and the 21 raw `/chat/completions` sites are likewise A2 (they currently bypass the gateway by design = their current behavior). Do per-concern, behavioral-diff each, with owner aware.

---

### P2-D — Pattern base + serializable result · mini-plan (analyzed 2026-06-19; scoping decision pending)

**Careful-analysis finding — THREE parallel "pattern" conventions (the real "one thing, N times"):**
- **`SimulationPattern`** (`patterns/core.py`, ABC) — `async run(Hypothesis) -> SimulationResult` (typed), `@simulation_pattern` decorator + `PatternRegistry` (register/get/list). **~56 patterns.** The canonical/modern path; a typed `SimulationResult` and a registry *already exist here*.
- **`BasePattern`** (`patterns/library/base.py`, ABC) — `def run(dict) -> dict` (sync), `GPUMixin`, `BaseConfig`. **7 patterns.** Legacy dict-based.
- **Bare classes** — no base, no decorator (e.g. `adaptive_filter.AdaptiveFilterPattern`). **~46 files.** Work only via the reflection runner's duck-typing.

The reflection **`PatternRunner`** (`patterns/runner.py`, 306 LOC: `importlib` + `inspect.getmembers` + `inspect.signature` adaptive dispatch) exists *because* categories 2–3 aren't on the registry. Single execution chokepoint: `PatternRunner.run_pattern` (~5 callers: step_10_simulation, cli/commands, hil phase_e, solver/strategies, api/routers/patterns).

The `patterns↔simulations` cycle is **lazy** (the 35 `NewtonBridge` imports are *inside method bodies*, not import-time) → not an import cycle; lower urgency than the plan implied.

**Scoping reality (revises the plan's "easy ABC win"):** the "one ABC + registry + delete reflection runner" win requires migrating ~53 patterns (7 `BasePattern` + 46 bare) onto `SimulationPattern`+decorator — large churn for a dead-end-Python codebase. And `SimulationResult` is typed but **not guaranteed JSON-safe** (`data: dict[Any]`, `datetime`, enum fields) → genuine worker-boundary gap, but serializing at the chokepoint now has **no consumer** until the worker POC exists (speculative). So P2-D splits:
- **D-core:** fold the 7 `BasePattern` patterns onto `SimulationPattern`, delete `BasePattern`. **NOT the clean fold it first looked:** all 7 are **sync** `run()->dict`; 3 (`n_body`, `acoustic_waves`, `rigid_body`) depend on `GPUMixin` (heavy numerics — the literal "Python in a separate barrel" worker candidates). Folding = semantic migration (sync→async, dict→typed `SimulationResult`, preserve GPU) of working numeric code, with behavior-preservation risk. The reflection `PatternRunner` already tolerates both conventions via duck-typing, so these 7 work as-is today.
- **D-bulk (large, optional):** migrate the 46 bare patterns onto the registry + delete the reflection `PatternRunner`. Big churn; internal tidiness only.
- **D-worker (deferred):** JSON-safe `SimulationResult` + serialize at the `run_pattern` chokepoint — only when P4 worker boundary is actually pursued (else speculative dead code with no consumer).

**Revised recommendation: defer all of P2-D until the worker boundary (P4) is greenlit, then do it *as part of* building that POC.** Every slice is semantic migration of working numeric code, and the reflection runner already provides a working unification seam at the single `run_pattern` chokepoint. Speculative consolidation now = churn without a consumer, against the dead-end-Python stance. The one thing P4 genuinely needs (a serializable result across the process boundary) is cheapest to add *at the chokepoint when the worker exists*, not by migrating 53 patterns up front.

---

### P2-B — Step model → protocol · mini-plan · **✅ done 2026-06-19** (`fix/tui-v9-audit-batch1`)

**Outcome (all under the fast dispatch net + real-step e2e, both green; full suite 5153/0):**
- **Step 0** — built `tests/agents/test_executor_dispatch.py` (7 tests, ~1.7s, always-on): pins the exact event/stage sequence, turbo-skip, early-exit, plugin interleave, pattern simulation, deep-work extras, on_complete side-effects. Negative-control verified. (`f64c7cf`)
- **Core** (`37dddef`) — executor now constructs typed `PipelineStep` subclasses via `make(pipeline)` + `build_context(pipeline,state,result)` and calls `.execute(context)` directly. Deleted: `_get_step_fn`+globals-cache+per-call `importlib`, `src/pipeline/step_definition.py` (STEP_MODULES/StepDefinition), the `unwrap_tuple` mechanism (prior_art's max_confidence already in output_data → via include_output), and the `build_args` pos/kwargs lambdas. Inline plugin/sim branches call the classes directly.
- **Cleanup** (`02494dd`) — deleted the 14 now-dead `step_*` free-fn shims (AST-precise; kept class-only helper `_enhance_perspectives_with_llm`), their re-exports, the stale "for test mocking" imports, dead `step_11_verify.py`, and 3 pre-existing unused imports.

The net's assertions never changed across the refactor — only its injection seam moved from `_get_step_fn` to `make` — which is the equivalence proof. **Next: P2-C** (orchestrator spine), the payoff this unblocks.

---

### P2-B — (original analysis, kept for reference)

**Careful-analysis finding (safety-gate "is it really a dup?"): YES, but the dup is *dispatch machinery*, not step logic.** Each `step_NN_*.py` already contains the canonical typed form — a `PipelineStep` ABC subclass (`ImpactIdentifyStep.execute(context)` etc., 14 of them). The step **logic lives exactly once**, in those classes. Layered *on top* are two redundant indirections the executor actually drives through:
- **14 free-fn shims** (`step_impact_identify(...)`) — each a 3-line "legacy function-based API" that just `Cls(deps).execute({...})`. Re-exported from `steps/__init__.py` and imported (unused?) by `solve_pipeline.py`.
- **String/importlib dispatch** — `STEP_PLAN` (executor.py) entries carry `"fn": "step_…"` strings + `build_args` lambdas; `_get_step_fn()` resolves them via `importlib.import_module(STEP_MODULES[name])` + a `globals()` cache hack; `STEP_MODULES`/`StepDefinition` live in `pipeline/step_definition.py`. Net: a **triple bounce** (string → importlib → free-fn → instantiate class → `.execute`) to call a method the executor could call directly.

Single live orchestrator confirmed: `solve_pipeline.py` (233 LOC) **delegates** to `PipelineExecutor` (no own step loop) → P2-B is self-contained to `executor.py` + `steps/` + `step_definition.py`.

**Target:** executor holds a registry of constructed `PipelineStep` instances (stage→step), loops calling `.execute(context)` against the shared `state` dict directly. Delete: the 14 free-fn shims, `STEP_MODULES`, `step_definition.py`, `_get_step_fn` + globals cache, the `"fn"` strings and `build_args` lambdas (the class reads inputs from `context`; constructor deps come from `pipeline`). Pure subtraction + de-cleverness; **prereq for P2-C** (orchestrator spine).

**Risk: medium-high, and the net is thin.** The executor tangles step dispatch with the observer O₀→O₂ loops, deep-work branches, early-exit, and interleaved plugin/pattern steps — all keyed off STEP_PLAN `id`s. The ONLY end-to-end characterization (`tests/e2e/test_pipeline_fake_llm.py`) is **double-gated off** by default (`skipif RUN_PIPELINE_E2E` + `@mark.slow`, ~49s). **Mandatory step 0: build a fast, always-on executor-level characterization test** (fake pipeline, assert the exact event/stage sequence + key outputs of a full STEP_PLAN run) before touching dispatch. Then migrate per-step under green, verifying each `Cls.execute(context)` reproduces the free-fn path's positional-arg behavior (the `build_args` lambdas are the spec to preserve).

**Owner note:** value is internal tidiness + unblocking P2-C, not a user-facing fix; weigh against the dead-end-Python stance. Cleanest as **P2-B+C as one track** (P2-B alone just tidies plumbing; the payoff lands when P2-C reshapes the spine).

---


### P0 — Security & correctness · ✅ code parts done (`fix/tui-v9-audit-batch1`)
**P0-1 (secrets):**
- Done by me: `git rm archive/harness/value-keys.tex`; `.gitignore` rule (`*value-keys*`, `archive/harness/value-keys.*`); generated `.secrets.baseline` so the (previously broken — referenced a missing baseline) detect-secrets hook is functional. Root cause of the leak: `.git/hooks/pre-commit` was **never installed**, so the already-configured gitleaks/detect-secrets hooks never ran. Spot-checked the 6 highest-risk detect-secrets hits (knowledge/config, auth/web3, p6_adapters, vastai_delegate, reasoner_client, llm_classifier) — no hardcoded live secrets; the 95 baseline entries are false positives (env refs, doc examples, hashes). Confirms value-keys.tex was the only live exposure.
- **REMAINING — owner actions (not done by me, by design):**
  1. **Rotate** every credential that was in the file: OpenRouter, Moonshot, DeepSeek, GroQ, Kilo Gateway, NVIDIA, XAI, Brave, Exa, Tavily (LLM/search); Telegram bot (С4 Science Bot / @c4cditurbot); `my-api-key (c4-turbo-cdi)` (NOWPayments/license); X/Twitter, Mastodon (social); and the **PyPI publish token**.
  2. **Scrub history** (the secrets are still in main's history since `bcf299d`): `git filter-repo --path archive/harness/value-keys.tex --invert-paths` then force-push. Destructive + rewrites origin/main → owner's call.
  3. `pre-commit install` (and `detect-secrets audit .secrets.baseline` to triage the 95 entries) so the scanners actually run going forward.

**P0-2 (disconnect):** ✅ added no-op `connect`/`disconnect` to `SQLiteDatabase` (`src/api/db_manager.py`) mirroring `PostgresDatabase`; verified `await db.disconnect()` no longer raises AttributeError. Fixes the shutdown error swallowed by lifespan's broad except.

### P1 — Subtraction · ✅ done (`fix/tui-v9-audit-batch1`)
Re-verified every target dead (0 src importers; not router-mounted) before removal. **155 files deleted.** Each "dead" package also carried a dedicated test suite — removed together (deleting dead code's tests is correct). Full Python logic suite after: **5134 passed / 0 failed** (was 5252; the −118 is the deleted dead-code tests). import-guard + collection both clean.
- **Stub packages** (owner confirmed dead, not feature-stubs): `src/{payments,radar,skills,tutorial,bots}` + their tests.
- **Dead infra**: `src/observability`, `src/cache`, `src/api/middleware/{policy,audit,rate_limit}.py`, `src/api/fast_metrics.py`, `src/api/database.py` (the unused Postgres module, not `db_manager`) + their tests.
- **Dead scaffolding**: `src/patterns/library/{loader.py,_registry.py}` (+ `test_loader.py`); `loader.py` pointed at deleted `v6.engine.*` paths.
- **Dead shims/legacy**: `src/mcp` deprecation shim (+`tests/mcp`); top-level `v6/` (+`test_v6_patterns.py`) and `v7/`.
- **P1-7** `.gitignore`: added exceptions so the blanket `models/`/`migrations/`/`k8s/` ignores no longer silently drop tracked source (`!models/**/*.json`, `!migrations/*.sql`, `!k8s/*.yaml`, `!k8s/*.sh`).
- **P1-8** removed `src/tui/v8/coverage.out` (Go coverage artifact) + ignore rule. *(Deferred, need decisions: duplicated WASM binaries `wasm/plugins` ↔ `wasm_plugins` → tangled with P2-E plugin/WASM resolution; docs/archive PDFs/CSVs/screenshots → not clearly junk; `src/tui/v8` legacy Go TUI → separate call.)*
- **Deferred out of P1** (need design, not blind subtraction): `UnifiedLLMClient` is re-exported via `llm/local` → handle in **P2-A**; `contracts/c4_types.py` is the foundation module (T/S/A axes + C4Space protocol, only its own test imports it) → its dead `C4State` handled in **P2-F** (promote-vs-delete decision).
- **Belt-and-braces audit (under the consolidation-safety-gate lens — "did we delete a *better/different* version of a live thing?"):** No live behavior lost. Deleted dead-infra compared to live counterparts:
  - `rate_limit.py` (31-LOC stub, 0 importers) — live `RateLimitMiddleware` in `security.py` (mounted, 429s, headers) + `api/rate_limiter.py` are far richer. Kept the better one.
  - middleware `policy.py` (`pev_loops` referenced nowhere live) — live `agents/policy.py` is the richer, used PolicyEngine (immutable audit trail). Kept the better one.
  - middleware `audit.py` (103 LOC) — live `security/audit_log.py` is richer (hash-chain integrity, verify, backend). Kept the better one.
  - **`observability/` (1225 LOC OTel impl) and `cache/` (4-tier CacheOrchestrator)** — these were the only deletions where the *deleted* code was arguably more elaborate than what we kept (live = a Prometheus stub that exports zeros / a 2-tier `api/cache.py` CacheManager that IS used). BUT both deleted impls were **completely unwired (0 importers, 0 telemetry/0 cache-hits)**, so no running behavior was lost — just unused alternative implementations. Recoverable from git (`87bded6^`) if the OTel/4-tier direction is ever wanted; leaving deleted is consistent with the subtraction goal + dead-end Python stance.
