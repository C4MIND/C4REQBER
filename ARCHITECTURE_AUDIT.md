# Architecture Audit — turbo-cdi (c4reqber)

**Scope:** whole project — ~222k LOC Python (`src/`, 83 top-level packages with code / 131 incl. nested), ~98k LOC tests, Go TUI v8/v9, deployment/infra, docs.
**Method:** 6 parallel evidence-grounded audits (module topology, core/pipeline, API/infra, LLM/agents/knowledge, contracts/packaging/worker-readiness, deps/tests/hygiene), each building a real AST import graph and grepping for evidence. Every claim is backed by a count or `file:line`.
**Date context:** stabilization phase; a long-term Agda-core + Python-workers rewrite is parked. Recovery tag `pre-reorg-baseline`.

> **Reference document. REFRESHED 2026-06-24** against `main @ 82c319b`, **after** the P0→P2 rework batch landed (subtraction, LLM gateway, pipeline registry, plugin registry). The previous revision described the *pre-subtraction* state. Findings are now tagged **[RESOLVED]** (the batch fixed it) · **[STILL-OPEN]** (untouched) · **[NEW]** (this refresh found it) · **[REGRESSED]** (got worse). The original §0 URGENT secrets item is tracked in `REWORK_PLAN.md` P0 + the project memory; it is **not re-closed here** (file deleted from tree, but secrets remain in pushed git history — rotation + `git filter-repo` still pending).

---

## 1. Executive summary (refresh)

The P0→P2 batch **closed exactly what it claimed** — the dual-step abstraction, C4State fragmentation, the 3 plugin registries, the LLM-routing entrypoint sprawl (facade only), and 155 files of dead code. But it **did not move the dependency graph by a single edge**: both pre-existing import cycles persist, all three hub-clusters are unchanged, and `core→c4` is still half-merged. The codebase's dominant failure mode — **fragmentation / no single source of truth** — survives one level deeper than the consolidations reached.

This refresh also **corrected two quantitative errors** in the prior audit and surfaced **several findings it missed**:
- The prior "contract poverty: 26 BaseModel" was wrong — there are **148**, but **124 are HTTP DTOs in `src/api/`**; the internal worker seams still have near-zero serializable contracts, so the *thesis* stands and the *number* was misleading.
- The "4 orchestrator modes are genuinely different, skip unification" verdict (REWORK_PLAN P2-C) missed that **two of the underlying A→G phase families are the same pipeline implemented twice** (`hil_phases/*` for turbo vs `discovery_phases/*` for the API).
- `pyproject.toml` has **no `[build-system]` table at all** → `pip install -e .` cannot run; the packaging hack is now a hard blocker, not just a smell.
- Several LLM model IDs across the routing tables are **non-existent / hallucinated** (dotted `claude-sonnet-4.6`, `gemini-3.1-pro`, `grok-4.20`), and `cost_tracker` silently mis-prices all Claude-4.x as gpt-4o.

**Posture (unchanged):** "Python is a tidy dead-end." Bias to subtraction + no-regret consolidation; don't build the full 16-module contract scaffold on code you intend to discard. The highest-leverage remaining moves are the cheap bug fixes, the two A→G phase families, finishing `core→c4`, one `Settings` object, and proving a **single** serialized worker contract on `embeddings`.

---

## 2. ✅ RESOLVED by the P0→P2 batch

| Finding (prior severity) | Evidence on current `main` |
|---|---|
| **Dual step abstraction, one dead** (CRITICAL) | P2-B: `pipeline/step_definition.py` gone; `executor.py` has 0 `importlib`/`STEP_MODULES`/`_get_step_fn`/free-fn shims; single `PipelineStep(ABC)` at `steps/base.py:26`, instantiated via `STEP_PLAN[*]["make"]` (`executor.py:602`) and called `.execute(context)` (`:604`). |
| **C4State fragmentation** | `c4/state.py:120` canonical (39 importers); `archetypes/data.py:10` renamed `C4Archetype`; `contracts/c4_types.py:31 C4State` correctly left as the foundation T/S/A scaffold. |
| **3 plugin registries** | P2-E: `unified_registry.py` is the only registry; `registry.py`/`v2_registry.py` deleted; WASM stubs stripped from `plugin_stage_router` PHASE_PLUGINS. |
| **LLM entrypoint sprawl (facade)** | P2-A A1: `llm/gateway.py` (`LLMGateway` + `DefaultGateway` + `get_gateway()`) is the sanctioned entry; dead clients (`UnifiedLLMClient`, `provider_router.py`, `routing/`, `model_per_stage.py`) removed; 14 consumers migrated. |
| **Unfinished subtraction (155 files)** | `api/database.py`, `fast_metrics.py`, middleware `{audit,policy,rate_limit}.py` gone; repo-wide grep for their imports = 0; dead leaf packages reduced to `.pyc` husks. |
| **`SQLiteDatabase.disconnect` AttributeError** | P0-2: explicit no-op `connect`/`disconnect` at `db_manager.py:103-112`. |
| **`.gitignore` ignore-conflicts** | `git ls-files \| git check-ignore --stdin` = empty; P1-7 exceptions for `models/`/`migrations/`/`k8s/`. |
| **patterns↔simulations "import cycle"** | Re-measured: **not** an import cycle — lazy method-body imports + one import-time edge `simulations/runner_v2.py:18`. (Prior audit overstated; REWORK_PLAN P2-D was right.) |

---

## 3. 🆕 NEW findings (missed by the prior audit)

**N1 — Two A→G phase families are the same pipeline, twice** *(high value).* `pipeline/hil_phases/*` (7 files, 991 LOC, drives `turbo` via `HILDiscoveryPipeline`) and `pipeline/discovery_phases/*` (6 files, 762 LOC, drives the **API** via `api/v8_routers/discovery/pipeline.py`, which labels phases "A: Framing … G: Quality" at `:191-241` while importing the *other* package). The matching pair `phase_b_knowledge`↔`phase_2_knowledge` is the same stage with **divergent contracts and fixes** (phase_2 disables citation-chasing for the S2 rate limit `:42-55`; phase_b does `WebSearchPlugin` augmentation `:31-45`). Each family has exactly one consumer → two pipelines maintained in lockstep. This is the genuine "shared spine duplicated" that P2-C's top-level "4 modes" framing hid.

**N2 — `pyproject.toml` has no `[build-system]` table** *(REGRESSED / blocker).* `pip install -e .` fails before starting. Plus a live contradiction: `[project.scripts] c4reqber = "src.cli.blast_app:app"` (`:58`) assumes `src.` top-level, while `pytest.ini:2 pythonpath=src` strips it (`runner.py:182` does `from patterns.core import ...` with no `src.`). Blocks any worker carve.

**N3 — Hallucinated/non-existent model IDs across the 4 routing tables.** `router.py:35` `claude-3.5-sonnet`; `depth_router.py:29` dated `claude-sonnet-4-20250514`; `model_assignment.py:43` + `model_catalog.py:50` dotted `claude-sonnet-4.6`/`claude-opus-4.6` (and `gemini-3.1-pro`, `grok-4.20`, `deepseek-v4-pro`, `kimi-k2.6`). Real IDs are hyphenated `claude-opus-4-8`/`claude-sonnet-4-6`/`claude-haiku-4-5`. A2 must **fix values**, not just unify tables.

**N4 — `cost_tracker` mis-prices all Claude-4.x** *(bug).* `_normalize_model` (`cost_tracker.py:24-35`) knows only `claude-3.5`; everything else falls through to the `gpt-4o` default ($2.50/$10), under-pricing Opus 4.8 (~$5/$25) by ~2×. ~10-line fix, independent of A2.

**N5 — k8s config cannot boot** *(bug).* `CSRFProtectionMiddleware.__init__` raises `RuntimeError` without `CSRF_SECRET` (`csrf.py:42-44`); `k8s/deployment.yaml` env omits it → crash-loop. Also `replicas:3`/HPA `3-20` (`hpa.yaml:11`) on one RWO PVC (`deployment.yaml:67`) sharing a SQLite file; Redis URL injected with no Redis manifest.

**N6 — A JSON-over-subprocess worker contract already exists** *(opportunity).* `simulations/newton_bridge.py:265-281` (+ `vina/nvidia/slim/mirrorfish_bridge.py`) already do `json.dumps(config) → subprocess.run → json.loads`, with declared `PatternProtocol` (`:63`) and `NewtonResult` (`:52`). This is the CLAUDE.md "Python in a separate barrel" pattern — present for external engines, not yet generalized. (`buf.yaml`/`buf.gen.yaml` exist; **zero `.proto` files**.)

**N7 — 6 ad-hoc `SentenceTransformer` loaders**, not just NoveltyScorer: `knowledge/novelty_scorer.py:31`, `c4/invariant_engine.py:58`, `verification/claim_matcher.py:84`, `discovery/novelty_validator.py:25`, `analogy/operations.py:41`, `analogy/structural.py:468`. The "unify before carving embeddings" prerequisite is bigger than the prior single-caveat.

**N8 — Smaller new items:** orphan `v8_routers/verification.py` (imported nowhere; duplicate of wired `verification_v8.py`); synthesized fallback `news_router` stub (`v8_routers/__init__.py:22`); `agents_router.py:296` constructs `AsyncLLMClient()` directly (an A1 migration miss); `figuramax` hardcoded dev paths in **48 `.go` files** + 2 Python i18n scripts; `llm/embeddings.py` purity **[REGRESSED]** — now also hosts `fast_*`/`_call_llm` OpenRouter HTTP calls (`:286-393`), mixing the clean numeric engine with network code.

---

## 4. 🔧 Corrections to the prior audit's numbers

- **"26 BaseModel across 228k LOC" → actually 148.** But 124 are FastAPI request/response DTOs in `src/api/`; the worker seams (`patterns`↔`simulations`, `embeddings`) have near-zero contracts (`SimulationResult` is a bare `@dataclass` with `data: dict[str,Any]`, `patterns/core.py:68`). Thesis ("boundaries are in-process calls, not serializable messages") **stands**; the count was inflated downward.
- **"21 raw `/chat/completions` sites" → 35 grep hits**, splitting into the legitimate provider layer (`llm/providers/*`, `client.py`, `async_client.py`) and **~16 true bypass sites** (the A2 targets, listed in §6).
- **"Two Go TUIs target different prefixes" → both straddle the same** `/api/v1` + `/v8`. The real issue is two schemes, not divergence.
- **NoveltyScorer "second model" → six** ad-hoc embedders (N7).

---

## 5. 🧭 Module topology & dependency health  *(graph unchanged by the batch)*

- **[STILL-OPEN] Two SCCs persist** (Tarjan over the AST graph): `{agent, cli, codegen, mcp_server}` (genuine entrypoint cycle → extract a one-directional `commands` core) and `{patterns, simulations}` (essential pair → move behind the worker boundary). No new cycles; the 8-package orchestration core (`{agents,api,auth,discovery,litintel,pipeline,solver,validation}`) is still a clean DAG.
- **[STILL-OPEN] Hubs unchanged:** fan-in `di(21)` / `c4(17)` / `llm(15)`; fan-out `api(29)` / `mcp_server(22)` / `agents(20)`. `tui`→`cli` keeps the TUI in the cycle's blast radius.
- **[STILL-OPEN] `core→c4` incomplete:** `src/core/` still has 13 tracked files, 11 external importers, and **a duplicate `core/c4_state.py` alongside `c4/state.py`**. Most-imported survivors: `core.profile_manager` (10), `core.complexity_adapter` (8).
- **[STILL-OPEN] Dead islands:** `meta_layer` (5 files, only self-imports) and `metaprograms` (5 files, only self-imports) have **zero external fan-in** → pure subtraction. `terminal_` (3 files) still imported by 6 `cli`/`agents` files.
- **[NEW] `.pyc` husk dirs shadow imports:** 8+ husks (`payments/radar/skills/tutorial/bots/observability/cache/mcp` + `llm/routing`, `tui/v8/splash`) have 0 tracked files but live `__pycache__`; the AST graph mis-resolved `from mcp.server` onto `src/mcp/` because the dir physically exists on `sys.path`. `git clean -fdx src/` them.
- **[STILL-OPEN] `contracts`/`infrastructure`/`adapters` not load-bearing:** 4/7/3 importers respectively. The `SolvePipeline`-protocol injection in `validation/empirical_layer.py` is the lone good citizen.
- **Package count vs ~16-module target:** 83 code-packages ≈ 5× over; natural bucketing into ~13 candidate modules exists (kernel / llm / pipeline / agents / discovery / knowledge / reasoning / patterns→worker / graph / domain-extras / api / cli-tui / delete-orphans).

---

## 6. Core, pipeline, LLM, API — STILL-OPEN detail

**Core & pipeline**
- **[STILL-OPEN] `PipelineExecutor.execute()` is still a 236-line god-function** (`executor.py:262-498`) with hardcoded `if step_id=="s9"/"s8"/"s2d"` branching over a mutable `state` dict (`:298,302,320,332,349`). P2-B *relocated* the cleverness into an in-module `STEP_PLAN` lambda table + 8 `_on_sN` free fns (file grew 233→628 LOC) but did not split it. The `StepRunner`/`ObserverOrchestrator`/`ModePolicy` split is now *cheaper* (dispatch is already a clean table).
- **[STILL-OPEN] flash + turbofactory inline in `cli/blast_core.py`** (`cmd_flash._run:222`, `cmd_turbofactory:455-687`), untestable without the CLI; turbofactory uses a raw `asyncio.Semaphore` (`:565`), ignoring `SmartScheduler`.
- **[STILL-OPEN] `pipeline→agents` via `importlib.import_module("src.agents.functor_orchestrator")`** (`hil_phases/phase_d_agents.py:29`); no `CognitiveAgentRunner` protocol (grep 0). (P2-C reframed as low-value design polish — stands.)
- **[STILL-OPEN] No `ExecutionPolicy`:** 10 hand-picked `asyncio.wait_for` timeouts; turbofactory has none.
- **[STILL-OPEN] God-modules, none split:** `triz/matrix_core.py` 1761, `triz/standard_solutions.py` 1289, `triz/standard_solutions_data.py` 1210, `triz/principles.py` 1136, `operators/matrix_dream.py` 1120, `discovery/pipeline_logic.py` 1011, `operators/autoresearch.py` 962, `triz/ariz.py` 884, `discovery/falsifier.py` 833. `triz/` is the densest cluster.

**LLM / agents**
- **[STILL-OPEN] ~16 true raw-httpx bypass sites** skip the gateway (cost/retry/guardian/cache): `social/grok_client.py:31`, `publishing/dissertation.py:37,50`, `memory/llm_isomorphisms.py:221`, `llm/reasoner_client.py:41+`, `plugins/_llm_base.py:23` (→ all 12 cognitive plugins), `llm/council.py:54`, `integrations/{nvidia,liquid_ai,openfang}.py`, `codegen/mcp_tool.py:88`, `discovery/{falsifier:776,novelty_validator:242}.py`, `utils/translation.py:84`, `llm/embeddings.py:393`, `llm/local_fallback.py:24`. Plus the `agents_router.py:296` `AsyncLLMClient()` miss (N8). These are the A2 targets.
- **[STILL-OPEN] No native Anthropic SDK:** zero `api.anthropic.com` / `import anthropic` / `anthropic-version`. Every model incl. Claude is OpenAI-compat `/chat/completions`. Forecloses prompt caching — the single biggest cost lever on synthesis/dissertation phases.
- **[STILL-OPEN] `MultiAgentSystem` is keyword-heuristic**, not LLM-driven (`multi_agent.py:137-234`); 3 duplicate `AgentRole` enums (`orchestrator.py:22`, `multi_agent.py:22`, `multi/core.py:12`).
- **[RESOLVED] Embeddings engine** is a clean lazy singleton (`embeddings.py:71,141`) with `embed(list[str])->ndarray` already the target signature — but see N7 (6 ad-hoc loaders) and N8 (module purity regressed).

**API / infra**
- **[STILL-OPEN] SSE drift: 16 decoded vs 3 emitted.** Go decoder (`tui/v9/api/sse_typed.go:16-34`) knows 16 event types; backend (`api/v8_routers/discovery_v8.py:154-189`, the only SSE emitter) emits `phase`/`complete`/`error` with **no `type` field**; 13 typed Go events are never produced; only string-inference (`DecodeTypedEvent`) masks it.
- **[STILL-OPEN] Versioning sprawl:** 27 routers / 23 prefixes / 105 routes across two schemes (`/api/v1/*` + `/v8/*`).
- **[STILL-OPEN] Two disagreeing JWT paths:** global middleware `JWTAuthMiddleware.dispatch` does raw `jwt.decode` with no issuer/`require`/revocation (`middleware/auth.py:88`) vs `AuthManager.decode_token` full checks (`api/auth.py:182`). A token lacking `iss`/`jti` or a revoked token passes the middleware but fails AuthManager. **CORS mounted twice** (`server.py:79` inside `setup_security_middleware` + `:80` `setup_cors`). Dev-mode bypass is safe-by-default (keep as model).
- **[STILL-OPEN] Persistence straddle:** `PostgresDatabase` is a connect/ping stub with zero CRUD + silent SQLite fallback (`db_manager.py:252-298`); `init.sql` (Postgres DDL) drifted from inlined `SQLITE_SCHEMA`; `alembic.ini` with no `alembic/` dir.
- **[STILL-OPEN] Config fragmentation:** 273 `os.getenv`/`os.environ` across 123 files; `pydantic-settings` declared (`pyproject.toml:19`) but **zero** `BaseSettings` subclasses.

---

## 7. Worker-boundary readiness verdict

| Candidate | Readiness | Blockers |
|---|---|---|
| **embeddings** | ~85% (was ~95%) | Split `llm/embeddings.py` (numeric vs LLM/HTTP, N8); unify 6 ad-hoc `SentenceTransformer` (N7); add `[build-system]` (N2). Engine signature already *is* the contract. |
| **patterns + simulations** | ~45% | `SimulationResult` not serializable (bare dataclass, `data: dict[str,Any]`); only ~70/170 patterns `.tolist()`; `runner.py` `inspect.signature` reflective dispatch can't cross a process boundary; invert one edge (`runner_v2.py:18`). |

**Minimal no-regret path to prove ONE worker contract:** (1) add a `[build-system]` table; (2) split `llm/embeddings.py` to a pure-numeric engine; (3) unify NoveltyScorer (one import site, `step_08_synthesis.py`); (4) generalize the `newton_bridge.py` `json.dumps→subprocess→json.loads` idiom (N6) into an `embeddings_worker` speaking `{"texts":[...]}→{"vectors":[[...]]}`. Defer `patterns+simulations` to a second POC.

---

## 8. Deps / tests / docs / hygiene — STILL-OPEN

- **[STILL-OPEN] 5 dependency manifests** (`pyproject.toml`, `requirements{,-simple}.txt`, `requirements.lock`, `uv.lock`); `pyproject` still not a superset (missing networkx, sqlalchemy, asyncpg, redis, scikit-learn, cryptography, sentence-transformers) and still pinned at `5.6.0`. `z3` is now a declared dep but an **unguarded** top-level `import z3` (`verification/hoare_verifier.py:27`).
- **[STILL-OPEN] Test pyramid:** 377 `test_*.py` / ~9,500 test fns; `integration` marker used by **0** tests; `-m "not slow"` removes only **2** tests; `fail_under=60`. Holes: `src/agents/` (54 files / 24 test fns — improved from ~1), `src/api/routers/` (14 routers / **0** dedicated tests).
- **[STILL-OPEN] Docs version graveyard:** `AGENTS.md` (v9.13.0, names existing `async_client.py`/`fallback.py` as "REMOVED"), `docs/ARCHITECTURE.md` (v5.4.0), `ARCHITECTURE_C4R.md` (v5.6.0, points TUI at non-existent `src/tui/v7/`). **[NEW]** these now also contradict the accurate `ARCHITECTURE_AUDIT.md`/`REWORK_PLAN.md`.
- **[STILL-OPEN] Binary bloat:** `archive/harness/` ~3.2 MB PNGs, Cyrillic PDFs under `docs/upgrades/`, duplicated WASM in `wasm/plugins/` ↔ `wasm_plugins/`. (`coverage.out` un-tracked — [RESOLVED].)
- **[STILL-OPEN] `figuramax` hardcoded paths** across 48 `.go` + 2 `.py` i18n files; 8 `.pyc` husk dirs to `git clean`.

---

## 9. Prioritized backlog (current state)

**Cheap bugs — do now**
1. `cost_tracker`: add Claude-4.x to `_PROVIDER_PRICES`/`_normalize_model` (N4, ~10 lines).
2. Delete duplicate `setup_cors` (`server.py:80`), orphan `v8_routers/verification.py`, news fallback stub; `git clean -fdx src/` the 8 husk dirs.
3. k8s: add/fail-loud on `CSRF_SECRET`/`JWT_SECRET`; `replicas:1` if staying on SQLite (N5).

**No-regret consolidations**
4. **Reconcile the two A→G phase families** (N1) — safety-gate behavioral diff per pair → union → one contract; the genuine duplication P2-C missed.
5. Finish `core→c4` (duplicate `c4_state.py`); delete `meta_layer`/`metaprograms` islands.
6. One `Settings(BaseSettings)`, fail-loud on secrets (also fixes the k8s misconfig class).
7. `pyproject.toml` = single manifest (+`[build-system]` N2, +7 deps, extras, guard `import z3`); delete the other 4; one lock. Designate one canonical ARCHITECTURE doc; fix stale "REMOVED"/`tui/v7` claims.

**Worker-boundary POC (Agda-rewrite leverage)**
8. embeddings POC per §7; then patterns+simulations.

**A2 — LLM cross-cutting (owner-gated)**
9. Migrate the ~16 raw sites to the gateway; collapse the 4 model tables **and fix the hallucinated IDs** (N3); route cost/retry/guardian/cache uniformly; add a native Anthropic backend with prompt caching (separate opt-in feature).

**Finish the in-place reorg (CLAUDE.md Phase 1)**
10. Break `{agent,cli,codegen,mcp_server}` via a `commands` core; make `contracts` load-bearing on the core DAG; split the `triz/` and `discovery/` god-modules.

---

*Refreshed from a 6-dimension parallel architectural audit on `main @ 82c319b` (2026-06-24). Every claim is grounded in import-graph/grep evidence with file:line refs. The previous (pre-subtraction) revision is recoverable from git history (`git show be4f752:ARCHITECTURE_AUDIT.md`).*
