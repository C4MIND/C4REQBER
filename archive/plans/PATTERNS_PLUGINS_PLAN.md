# TURBO-CDI: Scientific Patterns & Plugin Integration Plan

## Executive Summary

Система имеет **103 legacy паттерна** в `archive/legacy-patterns-v6/v6_legacy/` — полноценные научные симуляции (SEIR, CFD, FEM, DFT, quantum, etc.) на numpy/scipy. Они архивированы и не используются. Также есть **4 метамодель-плагина** (SWOT, 5 Whys, Morphological, Lateral Thinking) в `src/plugins/` — реализованы, но не интегрированы в pipeline.

## Цель

1. **Активировать 100+ научных паттернов** — перенести из archive в активный код
2. **Дополнить метамодель-плагины** — добавить недостающие (SCAMPER, Delphi, Delphi Method, TRIZ Bridge, etc.)
3. **Интегрировать всё в pipeline** — умный выбор паттернов/плагинов по домену задачи
4. **API + Frontend** — endpoints для запуска и UI для выбора

---

## Architecture Design

### Layer 1: Pattern Engine (Scientific Simulations)

```
┌─────────────────────────────────────────────────────────────┐
│  Pattern Engine                                              │
│  ─────────────────────────────────────────────────────────   │
│  • 100+ scientific simulation patterns                      │
│  • Domain-specific: physics, biology, economics, CS...      │
│  • Each pattern: run(hypothesis) → SimulationResult         │
│  • Resource estimation, GPU support, async execution        │
└─────────────────────────────────────────────────────────────┘
```

**Pattern Categories (103 total):**

| Category | Count | Examples |
|----------|-------|----------|
| Physics & Engineering | 18 | CFD, FEM, DFT, Thermal, Elasticity, Seismic, Acoustic |
| Biology & Medicine | 15 | SEIR, Enzyme Kinetics, Protein Folding, Neural Mass, Synaptic Plasticity |
| Economics & Finance | 12 | DSGE, GARCH, Credit Risk, Portfolio, Game Theory, Search Matching |
| Computer Science | 10 | Neural Network, Agent-Based, SLAM, Path Planning, Collaborative Filtering |
| Ecology & Environment | 12 | Spatial Ecology, Fisheries, Forest Gap, Wildfire, Air Quality, Sea Ice |
| Materials & Chemistry | 8 | Crystal Growth, Biogeochemistry, Cloud Microphysics, Phase Field |
| Social & Networks | 10 | Social Network, Opinion Dynamics, Herding, Rumor Spreading, Conflict |
| Control & Systems | 8 | PID Tuning, State Space, System Dynamics, Queueing Networks, Supply Chain |
| Geoscience | 5 | Groundwater, Geomagnetic, Surface Water, Urban Growth, Traffic Flow |
| Quantum & Advanced | 5 | Quantum, QFT Lattice, Plasma PIC, Wave Optics, Spectral Estimation |

### Layer 2: Metamodel Plugins (Cognitive Tools)

```
┌─────────────────────────────────────────────────────────────┐
│  Metamodel Plugin System                                     │
│  ─────────────────────────────────────────────────────────   │
│  • 20+ cognitive/methodological tools                       │
│  • Each plugin: execute(input) → structured output          │
│  • Auto-selection based on problem type                     │
│  • Composable: plugins can chain together                   │
└─────────────────────────────────────────────────────────────┘
```

**Required Plugins (20 total):**

| # | Plugin | Status | Description |
|---|--------|--------|-------------|
| 1 | SWOT Analysis | ✅ Done | Strengths/Weaknesses/Opportunities/Threats |
| 2 | 5 Whys | ✅ Done | Root cause analysis |
| 3 | Morphological Analysis | ✅ Done | Systematic solution exploration |
| 4 | Lateral Thinking | ✅ Done | De Bono's creative techniques |
| 5 | SCAMPER | 🆕 New | Substitute/Combine/Adapt/Modify/Put to other uses/Eliminate/Reverse |
| 6 | Delphi Method | 🆕 New | Expert consensus forecasting |
| 7 | TRIZ Bridge | 🆕 New | 40 principles + contradiction matrix |
| 8 | Six Thinking Hats | 🆕 New | Parallel thinking |
| 9 | Ishikawa Diagram | 🆕 New | Fishbone cause-effect |
| 10 | Pareto Analysis | 🆕 New | 80/20 rule prioritization |
| 11 | Design Thinking | 🆕 New | Empathize/Define/Ideate/Prototype/Test |
| 12 | First Principles | 🆕 New | Physics-style decomposition |
| 13 | Inversion | 🆕 New | Solve backwards from failure |
| 14 | Second-Order Thinking | 🆕 New | Consequences of consequences |
| 15 | OODA Loop | 🆕 New | Observe/Orient/Decide/Act |
| 16 | Red Team Analysis | 🆕 New | Adversarial critique |
| 17 | Pre-Mortem | 🆕 New | Post-project failure analysis |
| 18 | Constraint Relaxation | 🆕 New | Remove constraints temporarily |
| 19 | Analogical Reasoning | 🆕 New | Cross-domain transfer |
| 20 | Bayesian Update | 🆕 New | Probabilistic belief updating |

### Layer 3: Smart Integration Engine

```
┌─────────────────────────────────────────────────────────────┐
│  Integration Engine                                          │
│  ─────────────────────────────────────────────────────────   │
│  • Problem classifier → domain + complexity                 │
│  • Pattern selector → best simulation pattern               │
│  • Plugin composer → chain cognitive tools                  │
│  • Pipeline injector → insert into solve/discover flow      │
└─────────────────────────────────────────────────────────────┘
```

**Decision Logic:**

```python
def select_tools(problem: str, domain_hint: str | None) -> ToolSelection:
    # Step 1: Classify problem
    domain = classify_domain(problem)  # physics/biology/economics/etc.
    complexity = assess_complexity(problem)  # simple/moderate/complex
    
    # Step 2: Select simulation pattern (if applicable)
    pattern = None
    if domain in SIMULATION_DOMAINS:
        pattern = find_best_pattern(domain, problem)
    
    # Step 3: Select cognitive plugins
    plugins = []
    if complexity == "complex":
        plugins.extend(["first_principles", "system_dynamics"])
    if "trade-off" in problem or "contradiction" in problem:
        plugins.append("triz_bridge")
    if "forecast" in problem or "predict" in problem:
        plugins.extend(["delphi_method", "bayesian_update"])
    if "creative" in problem or "novel" in problem:
        plugins.extend(["lateral_thinking", "scamper", "analogical_reasoning"])
    if "risk" in problem or "failure" in problem:
        plugins.extend(["swot", "pre_mortem", "red_team"])
    
    # Step 4: Compose execution plan
    return ToolSelection(pattern=pattern, plugins=plugins, order=determine_order(plugins))
```

---

## Implementation Plan

### Phase A: Pattern Engine Revival (Week 1)

**A1. Migrate 103 patterns from archive**
- Copy `archive/legacy-patterns-v6/v6_legacy/*.py` → `src/patterns/library/`
- Update imports (archive → active)
- Fix Python 3.9+ compatibility (`datetime.UTC` issue)
- Create `src/patterns/library/__init__.py` with lazy loading

**A2. Pattern Registry v2**
- Extend `src/patterns/core.py` with domain tags
- Add `PatternRegistry.list_by_domain(domain)`
- Add `PatternRegistry.find_for_problem(problem_text)` — semantic matching
- Resource estimation for all patterns

**A3. Pattern API Endpoints**
```
GET  /v6/patterns              → list all patterns
GET  /v6/patterns/{id}         → pattern metadata
POST /v6/patterns/{id}/run     → execute pattern
POST /v6/patterns/select       → auto-select pattern for problem
GET  /v6/patterns/domains      → list domains
```

### Phase B: Complete Plugin Suite (Week 1-2)

**B1. Implement 16 new plugins**
- `src/plugins/scamper.py`
- `src/plugins/delphi.py`
- `src/plugins/six_hats.py`
- `src/plugins/ishikawa.py`
- `src/plugins/pareto.py`
- `src/plugins/design_thinking.py`
- `src/plugins/first_principles.py`
- `src/plugins/inversion.py`
- `src/plugins/second_order.py`
- `src/plugins/ooda.py`
- `src/plugins/red_team.py`
- `src/plugins/pre_mortem.py`
- `src/plugins/constraint_relaxation.py`
- `src/plugins/analogical_reasoning.py`
- `src/plugins/bayesian_update.py`
- `src/plugins/triz_bridge.py`

**B2. Plugin Integration API**
```
GET  /v6/plugins               → list all plugins
POST /v6/plugins/{id}/run      → execute plugin
POST /v6/plugins/compose       → chain multiple plugins
POST /v6/plugins/select        → auto-select plugins for problem
```

### Phase C: Pipeline Integration (Week 2)

**C1. Smart Tool Selection**
- Integrate into `UniversalSolvePipeline`
- After IMPACT Identify → classify problem → select pattern/plugins
- Before Synthesis → run selected tools → feed results into LLM prompt

**C2. Pipeline Extension**
```
Step 2.5: Pattern Simulation (optional)
  - If problem matches simulation domain
  - Run pattern with hypothesis parameters
  - Include simulation results in context

Step 4.5: Plugin Execution (optional)
  - Run selected cognitive plugins
  - Collect structured outputs
  - Feed into MP rotation as additional perspectives
```

**C3. Frontend Integration**
- Plugin selector in Solve/Discover pages
- Pattern visualization (if simulation runs)
- Results display with structured outputs

### Phase D: Frontend UI (Week 2-3)

**D1. Plugin Manager Page**
- Grid of all 20 plugins with icons
- Toggle on/off for pipeline inclusion
- Preview each plugin's output format

**D2. Pattern Browser**
- Filter by domain
- Pattern metadata cards
- "Run Simulation" button
- Results visualization

**D3. Pipeline Configurator**
- Drag-and-drop tool ordering
- Enable/disable steps
- Preview pipeline flow

---

## API Design

### Pattern Execution
```json
POST /v6/patterns/epidemic_seir/run
{
  "hypothesis": {
    "text": "Vaccination reduces R0 below 1",
    "parameters": {"beta": 0.3, "gamma": 0.1}
  },
  "config": {
    "N": 100000,
    "t_max": 365
  }
}

Response:
{
  "pattern_id": "epidemic_seir",
  "status": "completed",
  "result": {
    "R0": 3.0,
    "peak_infections": 45000,
    "herd_immunity_threshold": 0.67,
    "final_size": 85000
  },
  "execution_time_seconds": 2.4,
  "charts": [...]
}
```

### Plugin Execution
```json
POST /v6/plugins/triz_bridge/run
{
  "problem": "How to increase battery capacity without increasing weight?",
  "parameters": {"max_principles": 5}
}

Response:
{
  "plugin_id": "triz_bridge",
  "result": {
    "contradiction": {"improve": 7, "worsen": 1},
    "principles": [1, 15, 29, 4, 28],
    "principle_names": ["Segmentation", "Dynamics", "Pneumatics", ...],
    "suggestions": [...]
  }
}
```

### Smart Selection
```json
POST /v6/tools/select
{
  "problem": "Predict stock market volatility during recession",
  "domain_hint": "economics"
}

Response:
{
  "pattern": {
    "id": "garch",
    "confidence": 0.92,
    "reason": "Time-series volatility modeling"
  },
  "plugins": [
    {"id": "delphi_method", "confidence": 0.85},
    {"id": "bayesian_update", "confidence": 0.78},
    {"id": "red_team", "confidence": 0.65}
  ],
  "execution_plan": [...]
}
```

---

## Files to Create/Modify

### New Files:
- `src/patterns/library/` — 103 pattern files (migrated)
- `src/patterns/selector.py` — Smart pattern selection
- `src/patterns/api.py` — Pattern API endpoints
- `src/plugins/scamper.py` through `bayesian_update.py` — 16 new plugins
- `src/plugins/selector.py` — Smart plugin selection
- `src/plugins/composer.py` — Plugin chaining
- `src/integrations/tool_engine.py` — Unified tool execution

### Modified Files:
- `src/agents/pipeline.py` — Add pattern/plugin steps
- `src/api/v6_router.py` — Add pattern/plugin endpoints
- `src/patterns/core.py` — Extend with domain tags
- `src/patterns/runner.py` — Integrate with new library
- `src/pipeline/config.py` — Add pattern/plugin to templates
- `web-v2/src/pages/Discover.tsx` — Add tool selection UI
- `web-v2/src/pages/Solve.tsx` — Add pattern visualization

---

## Success Metrics

- [ ] 103 patterns migrated and loadable
- [ ] 20 plugins implemented with real logic
- [ ] Smart selection works for 10+ problem types
- [ ] Pipeline integration: pattern/plugins feed into LLM context
- [ ] Frontend: plugin manager + pattern browser
- [ ] All endpoints tested and documented
