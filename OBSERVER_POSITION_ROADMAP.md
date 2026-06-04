# Observer Position Shifts — Implementation Roadmap

## Context
`ObserverController` (O₀/O₁/O₂) exists in `src/c4/observer.py` and is **actively integrated** into `PipelineExecutor` (`src/agents/pipeline/executor.py`) as of v5.6.0. `shift_up()` and `shift_down()` are now called during pipeline execution — O₀→O₁ after synthesis, O₁→O₂ on stagnation detection. Alternative C4 states are derived from O₂ insights.

This document tracks what is **implemented** (v5.6.0) and what remains **future work**.

---

## Goal
Enable automatic observer position shifts during pipeline execution:
- **O₀ → O₁**: Self-diagnostic pass after hypothesis generation
- **O₁ → O₂**: Meta-reflection when stagnation is detected

Expected outcome: early detection of stale hypotheses, automatic switching between shallow/deep search, reduced wasted LLM calls.

---

## Phase 1: O₀ → O₁ Self-Diagnostic Pass

### What
After each hypothesis generation step, run a lightweight O₁ observer frame:
1. Collect visible states from O₁ perspective (all states within Hamming distance ≤ 2)
2. Generate blind_spots list ("own observational bias", "second-order effects")
3. Check if current C4 path passes through any of these blind_spots
4. If yes → flag for deeper analysis

### Where inserted
`src/agents/pipeline/executor.py` — `_run_observer_diagnostic()` called after step s8 (synthesis), not as a separate pipeline step.

### Files modified
- ✅ `src/agents/pipeline/executor.py` — `_run_observer_diagnostic()`, `_observer_controller` integration
- ✅ `src/agents/pipeline/steps/step_08_synthesis.py` — `observer_insights` injected into synthesis prompt, quality scoring applies `observer_penalty` (−0.03 blind spots / +0.02 clean)
- ✅ `src/agents/pipeline.py` — `SolvePipelineResult.observer_insights` field

### Overhead estimate
~10–15% additional LLM calls (only when blind_spots detected) — **not yet measured**

---

## Phase 2: O₁ → O₂ Meta-Reflection on Stagnation

### What
When `PipelineObserver.should_halt()` returns stagnation signal:
1. Trigger O₂ observer frame (all 27 states visible)
2. Generate meta-insights: "System-level view: current approach too narrow"
3. Compare current path against 24 scientist paths — find alternative route
4. Switch pipeline mode: autopilot → deep-work or turbo

### Where inserted
`src/agents/pipeline/executor.py` — `_run_meta_reflection()` triggered when `PipelineObserver.should_halt()` returns stagnation signal. Also re-runs post-pipeline if `confidence < 0.72`.

### Files modified
- ✅ `src/agents/pipeline/executor.py` — `_run_meta_reflection()`, `_derive_alternative_c4()`
- ✅ `src/c4/observer.py` — no changes needed (already implemented)

### Overhead estimate
~20% additional compute only during stagnation (rare event) — **not yet measured**

---

## Phase 3: Automatic Mode Switching

### What
Map observer level to pipeline mode:
| Observer | Mode | Behavior |
|---|---|---|
| O₀ | autopilot | Fast, shallow, few LLM calls |
| O₁ | turbo | Standard depth + self-diagnostic |
| O₂ | deep-work | Full scientist paths, domain transformer, MP rotation |

### Status
⚠️ **Partially implemented**. `_derive_alternative_c4()` shifts C4 axes based on O₂ insights (keyword-driven: "future"→T+1, "meta"→S+1, "system"→A+1), but explicit pipeline mode switching (autopilot→turbo→deep-work) is **not yet wired**.

### Where to insert
`src/agents/pipeline/executor.py` — mode config selection

### Files to modify
- `src/agents/pipeline/executor.py` — dynamic mode switching
- `src/agents/pipeline/config.py` — observer-aware presets

---

## Phase 4: Metrics & Validation

### Metrics to track
- Stagnation detection rate (before vs after observer shifts)
- Average pipeline depth (number of iterations)
- Hypothesis novelty_score improvement
- Cost per pipeline (LLM tokens)

### Validation
Re-run benchmark suite on 50 test problems, compare with/without observer shifts.

---

## Acceptance Criteria
- [x] O₀→O₁ shift triggers automatically after hypothesis generation — **IMPLEMENTED** in `PipelineExecutor`, step s8
- [x] O₁→O₂ shift triggers on stagnation detection — **IMPLEMENTED** via `PipelineObserver.should_halt()` + `_run_meta_reflection()`
- [ ] Pipeline mode switches dynamically (autopilot/turbo/deep-work) — **NOT YET** (partial: `_derive_alternative_c4()` shifts axes, mode config untouched)
- [x] No regression in existing test suite (9908 tests) — **VERIFIED** (v5.6.0)
- [ ] Benchmark shows ≥15% reduction in stagnation rate — **NOT YET** (needs 50-problem benchmark)
- [x] Documentation updated (theory page + API docs) — **DONE** (`ARCHITECTURE_C4R.md`, `CHANGELOG.md`, `AGENTS.md`)

---

## Related Files
- `src/c4/observer.py` — core observer logic (`ObserverController`, `ObserverPosition`, `ObservationalFrame`)
- `src/agents/pipeline.py` — pipeline orchestration, `SolvePipelineResult.observer_insights`
- `src/pipeline/observer.py` — stagnation detection (`PipelineObserver.should_halt()`)
- `src/agents/pipeline/executor.py` — **active integration** (`_run_observer_diagnostic`, `_run_meta_reflection`, `_derive_alternative_c4`)
- `src/agents/pipeline/steps/step_08_synthesis.py` — synthesis prompt injects observer insights
- `src/c4/cognitive_router.py` — scientist path matching (future: use O₂ for re-matching)

## Priority
**P1-completed** (shipped in v5.6.0). Remaining work: dynamic mode switching + benchmark validation.
