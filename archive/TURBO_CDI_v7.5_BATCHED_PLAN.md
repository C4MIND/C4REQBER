# TURBO-CDI v7.5 — Batched Integration & Completion Plan

**Date:** 2026-05-01
**Status:** Phase 1 Complete (1195 tests), Phase 2 Batched Execution Ready
**Mission:** Integrate all engines into unified system via agent conveyor belt
**Execution Model:** Batch-based agent orchestration — each batch = 1 agent, max 3 files, explicit deliverables

---

## Completed Work (Pre-Batch)

| Step | Status | Result |
|------|--------|--------|
| A: Frontend Audit | ✅ | `docs/UI_AUDIT_REPORT.md` — 30 pages mapped, 14 real, 7 mock, 9 missing |
| B: Simulations | ✅ | 101 patterns load + run (was 99, fixed continuum_mechanics + n_body) |
| C: API /v7/ | ✅ | All 19+ endpoints implemented, all call real engines |
| D: Pipeline | ✅ | 8 REAL / 2 HYBRID / 0 MOCK (was 5/3/2). Steps 01 + 09 fixed. |

---

## Remaining Work: Batched Execution

### PRINCIPLE: Agent Conveyor Belt
- **1 batch = 1 agent = max 3 files to modify/create**
- **Agent gets exact spec**: file path, function signature, API contract, expected output
- **No analysis paralysis**: agent executes, not researches
- **Verification gate**: tests must pass before next batch starts
- **Russian in spec is OK** (for И.Г. Селютин), **English in code only**

---

## BATCH GROUP 1: API Contract Hardening (Backend-First)

**Goal:** Ensure all /v7/ endpoints return predictable, typed, documented responses before any frontend work.

### Batch 1.1: API Response Normalization
**Agent:** AGENT-API-NORMALIZE
**Files:** `src/api/v7_routers/*.py` (10 routers)
**Spec:**
- Every endpoint must return a Pydantic response model (no raw dicts)
- Every POST endpoint must have request validation schema
- Error responses must follow `{error: string, detail?: string}` format
- Add `tests/api/test_v7_contracts.py` — test all 20+ endpoints return 200 with valid JSON
**Deliverable:** All v7 routers use strict schemas, new contract test passes

### Batch 1.2: API Integration Tests
**Agent:** AGENT-API-TEST
**Files:** `tests/api/test_v7.py`, `tests/api/test_v7_integration.py`
**Spec:**
- Test each /v7/ endpoint with real engine calls (not mocked)
- Test error cases: 404 for unknown pattern, 422 for invalid input
- Test C4 navigation: from (0,0,0) to (2,2,2) returns path ≤6 steps
- Test TRIZ matrix: 39×39 returns 1521 entries
**Deliverable:** 30+ API integration tests, all pass

---

## BATCH GROUP 2: Fix Mock Pages (Frontend)

**Goal:** Convert 7 mock/stub pages to real API integration.

### Batch 2.1: TRIZ Page — Real 40 Principles + Matrix
**Agent:** AGENT-TRIZ-WIRE
**Files:** `web-v2/src/pages/Triz.tsx`, `web-v2/src/services/api.ts`
**Spec:**
- Replace `GET /bridge/principles` → `GET /api/v7/triz/principles` (40 principles)
- Replace `POST /bridge/contradiction` → `POST /api/v7/triz/solve` (39×39 matrix)
- Remove `MOCK_PRINCIPLES` fallback — always call API
- Display all 40 principles in scrollable list with descriptions
- Contradiction solver: dropdowns for 39 params → show recommended principles
**Deliverable:** TRIZ page shows real 40 principles, matrix solver works

### Batch 2.2: IsomorphismGraph — Wire to API
**Agent:** AGENT-ISO-WIRE
**Files:** `web-v2/src/pages/IsomorphismGraph.tsx`, `web-v2/src/services/api.ts`
**Spec:**
- Replace hardcoded `MOCK_ISOMORPHISMS` → `POST /api/v7/c4/transform` or structural memory search
- Add search input: user enters domain → API returns isomorphisms
- Display results as cards with similarity scores
- Keep ReactFlow graph visualization for structural mappings
**Deliverable:** IsomorphismGraph shows real API results

### Batch 2.3: Analogy Page — Remove Mock Fallback
**Agent:** AGENT-ANALOGY-WIRE
**Files:** `web-v2/src/pages/Analogy.tsx`
**Spec:**
- Remove `EXAMPLE_ANALOGIES` hardcoded fallback
- Call `POST /api/v6/isomorphism/search` (already exists)
- On error: show error message, NOT mock data
- Display structural mappings (entity→entity, relation→relation)
**Deliverable:** Analogy page calls real API, no mock fallback

### Batch 2.4: Canvas Widgets — Wire to Real Stores
**Agent:** AGENT-CANVAS-WIRE
**Files:** `web-v2/src/pages/CanvasPage.tsx`, `web-v2/src/components/canvas/Widget*.tsx`
**Spec:**
- WidgetSolve: call `GET /api/v7/simulations` → show recent runs
- WidgetGraph: call `GET /graph/stats` → show real node/edge counts
- WidgetC4: call `GET /api/v7/c4/states` → show current state
- WidgetHyperCube: call `GET /api/v7/c4/states` → show active states
- Remove all `DEMO_DATA`, `FAKE_PROGRESS`, `MOCK_*`
**Deliverable:** All 4 canvas widgets show real data

### Batch 2.5: DecompositionTree — IMPACT Integration
**Agent:** AGENT-DECOMPOSE-WIRE
**Files:** `web-v2/src/pages/DecompositionTree.tsx`
**Spec:**
- Add input field: "Enter problem to decompose"
- Call `POST /api/v7/c4/fingerprint` → get C4 state
- Call `POST /api/v7/impact/analyze` (new endpoint or use existing) → get entities
- Auto-build tree from API response
- Allow manual editing as fallback
**Deliverable:** DecompositionTree auto-builds from problem text

### Batch 2.6: Agents Page — Remove Mock
**Agent:** AGENT-AGENTS-WIRE
**Files:** `web-v2/src/pages/Agents.tsx`
**Spec:**
- Remove `MOCK_AGENTS` fallback
- Call `GET /api/agents/` — if 404, show "No agents configured" (not mock data)
- Display real agent cards with status
**Deliverable:** Agents page shows real data or empty state

### Batch 2.7: Settings — Fix Duplicate Notifications
**Agent:** AGENT-SETTINGS-FIX
**Files:** `web-v2/src/pages/Settings.tsx`
**Spec:**
- Remove duplicate Notifications card
- Verify all other settings sections are unique
**Deliverable:** Settings page has no duplicate sections

---

## BATCH GROUP 3: New Module Pages (Frontend)

**Goal:** Create pages for 8 new Phase 2 modules.

### Batch 3.1: Causal Engine Page
**Agent:** AGENT-CAUSAL-PAGE
**Files:** `web-v2/src/pages/Causal.tsx`, `web-v2/src/services/api.ts`
**Spec:**
- Route: `/causal`
- Sections: SCM Builder (DAG editor), Do-Calculus (intervention input), Counterfactual (what-if)
- API: `POST /api/v7/causal/scm`, `POST /api/v7/causal/do`, `POST /api/v7/causal/counterfactual`
- Use `@xyflow/react` for DAG visualization
**Deliverable:** `/causal` page with SCM builder, do-calculus, counterfactual

### Batch 3.2: Discovery Engine Page
**Agent:** AGENT-DISCOVERY-PAGE
**Files:** `web-v2/src/pages/DiscoveryV7.tsx`
**Spec:**
- Route: `/discovery-v7` (or upgrade existing `/discover`)
- Sections: Abduction (observations → hypotheses), Strong Inference (competing hypotheses), Falsification (severity scoring)
- API: `POST /api/v7/discovery/abduce`, `POST /api/v7/discovery/infer`, `POST /api/v7/discovery/falsify`
- Display hypotheses as cards with confidence scores
**Deliverable:** Discovery page with abduction/inference/falsification

### Batch 3.3: LitIntel Page
**Agent:** AGENT-LITINTEL-PAGE
**Files:** `web-v2/src/pages/LitIntel.tsx`
**Spec:**
- Route: `/litintel`
- Sections: Paradigm Shift Detection, Contradiction Mining, Temporal KG
- API: `POST /api/v7/litintel/paradigm`, `POST /api/v7/litintel/contradict`
- Text input for papers/claims → anomaly scores, contradictions list
**Deliverable:** `/litintel` page with paradigm/contradiction analysis

### Batch 3.4: Bayesian Page
**Agent:** AGENT-BAYESIAN-PAGE
**Files:** `web-v2/src/pages/Bayesian.tsx`
**Spec:**
- Route: `/bayesian`
- Sections: MCMC Sampling, BMA, Prior/Posterior visualization
- API: `POST /api/v7/bayesian/mcmc`, `POST /api/v7/bayesian/bma`
- Use Recharts or D3 for distribution plots
**Deliverable:** `/bayesian` page with MCMC/BMA visualizations

### Batch 3.5: System Dynamics Page
**Agent:** AGENT-SD-PAGE
**Files:** `web-v2/src/pages/SystemDynamics.tsx`
**Spec:**
- Route: `/dynamics`
- Sections: Stock-Flow Builder, Feedback Loop Analysis, Simulation Runner
- API: `POST /api/v7/sd/model`, `POST /api/v7/sd/simulate`
- Use `@xyflow/react` for stock-flow diagrams
**Deliverable:** `/dynamics` page with stock-flow builder

### Batch 3.6: Decision Engine Page
**Agent:** AGENT-DECISION-PAGE
**Files:** `web-v2/src/pages/Decisions.tsx`
**Spec:**
- Route: `/decisions`
- Sections: AHP (pairwise comparison), TOPSIS (ranking), Game Theory (payoff matrix)
- API: Use existing decision endpoints or create wrapper
- Interactive matrices for input
**Deliverable:** `/decisions` page with AHP/TOPSIS/game theory

### Batch 3.7: Simulation Runner Page
**Agent:** AGENT-SIM-PAGE
**Files:** `web-v2/src/pages/SimulationRunner.tsx`
**Spec:**
- Route: `/simulations`
- Sections: Pattern List (101 patterns), Run Config, Results Visualization
- API: `GET /api/v7/simulations`, `POST /api/v7/simulations/{id}/run`
- Filter by domain, search by name
- Show execution time, status, result summary
**Deliverable:** `/simulations` page to browse and run all 101 patterns

---

## BATCH GROUP 4: Orphaned Components + Routing

**Goal:** Connect 6 orphaned advanced/lite components to routes.

### Batch 4.1: Route Orphaned Components
**Agent:** AGENT-ROUTE-ORPHANS
**Files:** `web-v2/src/App.tsx`
**Spec:**
- Add routes:
  - `/advanced/c4` → `Advanced/C4Explorer.tsx`
  - `/advanced/triz` → `Advanced/TRIZMatrix.tsx`
  - `/advanced/agents` → `Advanced/AgentPanel.tsx`
  - `/advanced/pipeline` → `Advanced/PipelineViewer.tsx`
  - `/lite/solve` → `Lite/SolveLite.tsx`
- Add navigation links in AppShell sidebar
- Verify each page loads without errors
**Deliverable:** All 5 orphaned components accessible via routes

---

## BATCH GROUP 5: E2E Tests + Final Verification

### Batch 5.1: E2E Critical Flows
**Agent:** AGENT-E2E-FLOWS
**Files:** `tests/e2e/test_v7_flow.py`
**Spec:**
- Flow 1: Problem → C4 fingerprint → MP profile → QZRF → hypothesis
- Flow 2: TRIZ solver → principles → apply
- Flow 3: Run simulation → results → visualize
- Flow 4: Causal model → do-calculus → effect
- Flow 5: Full pipeline: problem → discovery → validation → simulation
**Deliverable:** 5 E2E tests, all pass

### Batch 5.2: Final Audit
**Agent:** AGENT-FINAL-AUDIT
**Files:** `docs/V7_5_COMPLETION_REPORT.md`
**Spec:**
- Verify: 0 mock pages, 0 orphaned components, all /v7/ endpoints wired
- Count: total tests, coverage, pages, components
- Grade: 10/10 checklist
**Deliverable:** Completion report with grade

---

## Execution Order (Conveyor Belt)

```
GROUP 1 (API) → GROUP 2 (Fix Mocks) → GROUP 3 (New Pages) → GROUP 4 (Orphans) → GROUP 5 (E2E)
     │                │                      │                    │                │
     ▼                ▼                      ▼                    ▼                ▼
  1.1, 1.2        2.1-2.7               3.1-3.7              4.1            5.1, 5.2
```

**Rule:** Next batch starts only after previous group passes verification.

---

## Agent Spec Template (for each batch)

```
BATCH: X.Y
AGENT: AGENT-NAME
FILES: file1, file2, file3
API CONTRACT:
  - Endpoint: METHOD /api/vX/...
  - Request: {field: type}
  - Response: {field: type}
TASK:
  1. Specific change 1
  2. Specific change 2
VERIFICATION:
  - Test command: pytest tests/... -v
  - Expected: X passed
```

---

## Success Criteria (Phase 2 Final)

- [ ] 101 simulations all real, all tested
- [ ] /v7/ API with 20+ endpoints, strict schemas, all documented
- [ ] Pipeline uses real engines, 0 mocks
- [ ] 0 mock pages (TRIZ, Analogy, IsomorphismGraph, Canvas, DecompositionTree, Agents)
- [ ] 8 new module pages (Causal, Discovery, LitIntel, Bayesian, SystemDynamics, Decision, SimulationRunner, + existing)
- [ ] 0 orphaned components
- [ ] E2E tests pass for all 5 critical flows
- [ ] Total tests: 2000+
- [ ] Grade: 10/10

---

## References

- Phase 1 Plan: `TURBO_CDI_v7_ORCHESTRATION_PLAN.md`
- Frontend Audit: `docs/UI_AUDIT_REPORT.md`
- Existing API: `src/api/v6_router.py`, `src/api/v7_router.py`
- Existing Pipeline: `src/agents/pipeline.py`
