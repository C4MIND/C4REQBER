# TURBO-CDI v7.5 — Integration & Completion Plan

**Date:** 2026-04-30
**Status:** Phase 1 Complete (1195 tests), Phase 2 Ready
**Mission:** Integrate all engines into unified system + complete remaining simulations + connect to UI

---

## Phase 1 Summary (COMPLETED)

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| C4 Engine (Z₃³) | 37 | — | ✅ Real implementation |
| MP Profiler (~70) | 69 | 99% | ✅ C4 mapping |
| QZRF/FRA (14 ops) | 127 | 92% | ✅ Real routing |
| L5 Discovery | 136 | 95% | ✅ Abduction/Inference/Falsification |
| L1 Causal | 88 | 78% | ✅ do-calculus/SCM |
| L6 LitIntel | 51 | 91% | ✅ Paradigm/Contradiction |
| Simulations (10 real) | 356 | — | ✅ MC, FEM, CFD, MD, SEIR, Ising, etc. |
| TRIZ | 46 | — | ✅ 40 principles + 39×39 matrix |
| L2 Bayesian | 190 | 84% | ✅ MCMC/BMA/GP |
| L3 System Dynamics | — | — | ✅ Stock-Flow/CLD |
| Security | 111 | — | ✅ JWT/RateLimit/HSM |
| **TOTAL** | **1195** | — | **✅ ALL PASS** |

**What's Missing:** Integration into pipeline, API, frontend, remaining 85+ simulations

---

## Phase 2: Integration & Completion Architecture

```
PHASE 2 FLOW:
│
├─ STEP A: Frontend Audit (2 days)
│   └─ Audit existing React app → identify gaps → redesign plan
│
├─ STEP B: Complete Simulations (5 days)  
│   └─ 85+ remaining simulations → real implementations
│
├─ STEP C: API Router /v7/ (3 days)
│   └─ Endpoints for all new modules → OpenAPI specs
│
├─ STEP D: Pipeline Integration (4 days)
│   └─ 10-step pipeline calls real engines → no mocks
│
├─ STEP E: Frontend Wiring (5 days)
│   └─ React components → C4 viz, TRIZ solver, simulation runner, etc.
│
└─ STEP F: E2E Tests (2 days)
    └─ Full flow: UI → API → Engine → Result

Total: 21 days (3 weeks)
```

---

## STEP A: Frontend Audit

**Goal:** Understand what UI exists, what's broken, what's missing

**Agent:** AGENT-UI-AUDIT

**Tasks:**
1. Read all React components in `web-v2/src/`
2. Map existing pages to features
3. Identify: working / broken / mock / missing
4. Create UI gap analysis report
5. Propose redesign for new modules integration

**Deliverables:**
- `docs/UI_AUDIT_REPORT.md` — full audit
- `docs/UI_REDESIGN_PLAN.md` — redesign proposal
- List of components to fix/create

---

## STEP B: Complete Simulations

**Goal:** 95+ real simulations (currently 10 done, 85+ remaining)

**Agent:** AGENT-SIM-COMPLETE

**Priority batches:**

| Batch | Simulations | Complexity |
|-------|-------------|------------|
| B1 | Random Walk, Percolation, Poisson Solver, Optimization | Low |
| B2 | Quantum (QHO, QFT basics), Statistical (Ising variants), Network | Medium |
| B3 | Plasma PIC, GR basics, Cosmology, Climate | High |
| B4 | Agent-based, Game Theory, Economics, Social | Medium |
| B5 | Biophysics, Neuroscience, Materials | High |

**Deliverables:**
- `src/patterns/library/` — 85+ new real implementations
- Tests for each with correctness verification

---

## STEP C: API Router /v7/

**Goal:** REST API for all new modules

**Agent:** AGENT-API-V7

**Endpoints to create:**

| Endpoint | Module | Methods |
|----------|--------|---------|
| `/v7/c4/states` | C4 Engine | GET all 27 states |
| `/v7/c4/navigate` | C4 Navigation | POST: from→to state |
| `/v7/c4/fingerprint` | FRA | POST: problem text → C4 state |
| `/v7/discovery/abduce` | Abduction | POST: observations → hypotheses |
| `/v7/discovery/infer` | Strong Inference | POST: hypotheses → experiment |
| `/v7/discovery/falsify` | Falsification | POST: hypothesis → severity |
| `/v7/causal/scm` | SCM | POST: build model |
| `/v7/causal/do` | Do-calculus | POST: identify causal effect |
| `/v7/causal/counterfactual` | Counterfactual | POST: what-if analysis |
| `/v7/litintel/paradigm` | Paradigm Shift | POST: text → anomaly score |
| `/v7/litintel/contradict` | Contradiction | POST: claims → contradictions |
| `/v7/triz/solve` | TRIZ Solver | POST: problem → principles |
| `/v7/triz/matrix` | TRIZ Matrix | GET: full 39×39 |
| `/v7/sim/run` | Simulations | POST: run simulation |
| `/v7/bayesian/mcmc` | MCMC | POST: sample posterior |
| `/v7/bayesian/bma` | BMA | POST: model averaging |
| `/v7/sd/model` | System Dynamics | POST: build stock-flow |
| `/v7/sd/simulate` | SD Simulation | POST: run simulation |
| `/v7/mp/profile` | MP Profiler | POST: text → profile |
| `/v7/mp/shift` | MP Suggester | POST: profile → shift suggestions |

**Deliverables:**
- `src/api/v7_router.py` — all endpoints
- `tests/api/test_v7.py` — API tests
- OpenAPI 3.1 spec

---

## STEP D: Pipeline Integration

**Goal:** 10-step pipeline uses REAL engines

**Agent:** AGENT-PIPELINE-REAL

**Current pipeline (mock → real):**

| Step | Current | Target |
|------|---------|--------|
| 1. IMPACT Identify | LLM call | LLM + C4 fingerprint |
| 2. Prior Art Search | arXiv/PubMed | + LitIntel contradiction mining |
| 3. C4 Fingerprinting | LLM classifier | **Real C4 engine** |
| 4. MP Rotation | 153 MPs | **Real ~70 MPs** |
| 5. QZRF Selection | 14 operators | **Real QZRF + FRA routing** |
| 6. Isomorphism Search | spectral | Real + C4 navigation |
| 7. Plugin Execution | 20 plugins | Real engines |
| 8. LLM Synthesis | 7 providers | + Bayesian aggregation |
| 9. TOTE Validation | self-correction | + Falsification engine |
| 10. Pattern Simulation | stubs | **Real simulations** |

**Deliverables:**
- `src/agents/pipeline_v7.py` — integrated pipeline
- `tests/agents/test_pipeline_v7.py` — integration tests

---

## STEP E: Frontend Wiring

**Goal:** React components for all new features

**Agent:** AGENT-FRONTEND-WIRE

**Components to create/fix:**

| Component | Feature | Status |
|-----------|---------|--------|
| `C4HyperCube` | 3D C4 visualization | Check existing |
| `C4Navigator` | State navigation UI | NEW |
| `TRIZSolver` | Contradiction solver | NEW |
| `SimulationRunner` | Run simulations | NEW |
| `DiscoveryPanel` | Abduction/Inference | NEW |
| `CausalGraph` | DAG visualization | NEW |
| `ParadigmMonitor` | Shift detection | NEW |
| `MPProfiler` | User profile | NEW |
| `BayesianDashboard` | MCMC results | NEW |
| `SDModeler` | Stock-flow builder | NEW |

**Deliverables:**
- React components in `web-v2/src/components/v7/`
- API client updates in `web-v2/src/services/`
- Page updates in `web-v2/src/pages/`

---

## STEP F: E2E Tests

**Goal:** Full flow verification

**Agent:** AGENT-E2E-FINAL

**Test flows:**
1. User enters problem → C4 fingerprint → MP profile → QZRF operators → hypothesis
2. User runs TRIZ solver → gets principles → applies to problem
3. User runs simulation → gets real results → visualizes
4. User builds causal model → runs do-calculus → gets causal effect
5. Full pipeline: problem → discovery → validation → simulation → result

**Deliverables:**
- `tests/e2e/test_v7_flow.py` — Playwright/Cypress tests
- Performance benchmarks
- Final report: all claims verified

---

## Success Criteria (Phase 2)

- [ ] 95+ simulations all real, all tested
- [ ] /v7/ API with 20+ endpoints, all documented
- [ ] Pipeline uses real engines, no mocks
- [ ] Frontend has components for all major features
- [ ] E2E tests pass for all critical flows
- [ ] Total tests: 2000+

---

## References

- Phase 1 Plan: `TURBO_CDI_v7_ORCHESTRATION_PLAN.md`
- Existing UI: `web-v2/src/`
- Existing API: `src/api/v6_router.py`
- Existing Pipeline: `src/agents/pipeline.py`
