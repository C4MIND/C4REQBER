# UCOS Architecture

## Unified Cognitive Operating Stack (UCOS) for Reqber/C44TCDI

The UCOS stack organizes cognitive operations into four layers with clear separation of concerns. Each layer builds upon the one below it, from concrete process loops to dynamic state navigation.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: Application (Reqber CLI, API, MCP Server)             │
│  - User-facing discovery pipelines                              │
│  - 10-step scientific discovery workflow                        │
│  - Export, visualization, social publishing                     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: Dynamics (State Transitions)                          │
│  - QZRF 14 Operators (Quantum-Zonal Recursion)                  │
│  - FRARouter (Fingerprint-Route-Adapt)                          │
│  - Adaptive routing with feedback                               │
│  - BFS + heuristic pathfinding in C4 Z_3^3 space               │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Statics (Knowledge Templates)                         │
│  - 153 Metaprograms (structured cognitive patterns)             │
│  - 12 categories: Temporal, Scale, Agency, Process, ...         │
│  - Each MP: pattern name, applicability condition, logic        │
│  - C4 coordinates F<T,S,A> for every pattern                   │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: Process (Control Loops)                               │
│  - IMPACT: 6-phase problem-solving with convergence checks      │
│  - COMPASS: 7-level depth navigation with semantic abstraction  │
│  - TOTE: Test-Operate-Test-Exit with explicit exit criteria     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Process

### IMPACT (6-Phase Problem Solving)

```
Identify -> Map -> Predict -> Analyze -> Create -> Test
```

Each phase has:
- **Explicit input**: problem statement + accumulated context
- **Explicit output**: structured decomposition, entities, relations
- **Convergence check**: validation rule specific to the phase
- **Adaptive transition**: retry with relaxed parameters if convergence fails

**Phase Convergence Criteria:**
| Phase | Convergence Rule |
|-------|-----------------|
| Identify | At least 1 entity extracted |
| Map | Relations mapped (may be empty) |
| Predict | At least 2 scenarios generated |
| Analyze | Contradictions identified (may be empty) |
| Create | At least 1 solution proposed |
| Test | Confidence score >= 0.5 |

### COMPASS (7-Level Depth Navigation)

```
0. Fact        ->  raw data, observations
1. Phenomenon  ->  patterns in facts
2. Law         ->  regularities, equations
3. Principle   ->  underlying mechanisms
4. Meta        ->  frameworks, paradigms
5. Absolute    ->  universal truths
6. Transcendence -> beyond the system
```

- `ascend()`: semantic abstraction (LLM-based or template-based)
- `descend()`: concretization back to observable level
- `jump_to()`: direct navigation to any level

### TOTE (Test-Operate-Test-Exit)

```
Test 1: Is current state acceptable?
   |
   |-- YES -> Exit (success)
   |
   |-- NO -> Operate (transform state)
              |
              v
         Test 2: Is new state closer to target?
              |
              |-- YES -> Exit (success)
              |
              |-- NO -> Repeat loop
```

**Exit Criteria:**
- `target_reached`: boolean — test function returned True
- `max_iterations_exceeded`: loop hit safety limit
- `convergence_observed`: success within 3 iterations
- `error_occurred`: exception during test or operate

---

## Layer 2: Statics

### 153 Metaprograms

Organized into 17 categories:

| Category | Count | Example Patterns |
|----------|-------|-----------------|
| Temporal | 12 | Past Orientation, Future-Visionary |
| Scale | 10 | Concrete-Detail, Meta-Systemic, Analogical |
| Agency | 10 | Self-Agency, Distributed-Agency |
| Process | 8 | Iterative, Experimental |
| Result | 8 | Goal-Focused, Satisficing |
| Communication | 12 | Visual, Assertive |
| Meta-cognitive | 5 | Observer-O2, Cognitive-Flexibility |
| Problem-Solving | 12 | Divide and Conquer, Analogy Transfer, Constraint Relaxation |
| Scientific | 10 | Hypothesis Formation, Falsification, Bayesian Update |
| Creative | 9 | Divergent Thinking, Biomimicry, Forced Connection |
| Emotional | 7 | Emotional Awareness, Resilience, Gratitude |
| Social | 7 | Social Proof, Negotiation, Reputation Management |
| Strategic | 9 | Game Theory, Antifragility, Second-Order Thinking |
| Logical | 7 | Deductive Reasoning, Reductio ad Absurdum, Probabilistic Thinking |
| Learning | 7 | Spaced Repetition, Transfer Learning, Deliberate Practice |
| Decision | 8 | Expected Value, Optionality, Regret Minimization |
| Executive | 12 | Prioritization, Delegation, Feedback Loop |

Each metaprogram:
- Has a unique code (e.g., `PS01`, `SC03`)
- Maps to C4 coordinates `F<T,S,A>`
- Includes applicability keywords for text detection
- May have an opposite metaprogram

---

## Layer 3: Dynamics

### QZRF Operators (14)

Quantum-Zonal Recursion Framework:

| Phase | Operators |
|-------|-----------|
| Divergence | Branching, Annealing, Projection |
| Modulation | Gradient Step, Parametric Sweep, Resonance Tuning |
| Network | Graph Weave, Cross-Linking, Eigenmode Extraction |
| Integration | Synthesis, Harmonization, Crystallization |
| Topology | Space Folding, Dimensional Lift |

### FRARouter

**Fingerprint-Route-Adapt pattern:**
1. **Fingerprint**: Classify problem into C4 state via keyword analysis
2. **Route**: BFS with heuristic to find optimal operator sequence
3. **Adapt**: Re-rank operators based on historical feedback scores

**Theorem 9 Integration:**
- Path length = Hamming distance for undirected C4 space
- Any state reachable from any other in <= 6 steps (Theorem 11)
- BFS guarantees shortest path when heuristic is admissible

**Quality Presets:**
- `synthesis`: Favor connect, crystallize, expand operators
- `mp_rotation`: Favor shift, tune, cycle operators
- `validation`: Favor detect, track, focus operators

---

## Layer 4: Application

Reqber v4.2.1 uses UCOS through:
- **MCP Server** (9 tools): c4_solve, c4_search, c4_triz, etc.
- **CLI**: Cube-Mascot, Adaptive Layout, Timeline
- **API**: v8 routers for all discovery endpoints

---

## Separation of Concerns

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| L1 Process | Control loops, convergence, iteration | `metamodels/impact.py`, `metamodels/compass.py`, `metamodels/tote.py` |
| L2 Statics | Pattern library, matching, coordinates | `metaprograms/core.py` |
| L3 Dynamics | State transitions, routing, adaptation | `c4/routing.py`, `metaprograms/dynamics.py`, `metamodels/qzrf/operators.py` |
| L4 Application | User interface, pipelines, integrations | `cli/`, `api/`, `mcp_server/` |

---

## Theory-Implementation Alignment (Phase P5)

### Theorem 9 -> Implementation
- **Theory**: Shortest path length = Hamming distance in C4 Z_3^3
- **Implementation**: `FRARouter.find_route()` uses BFS with distance heuristic; `RoutePlan.is_optimal` checks equality

### Theorem 11 -> Implementation
- **Theory**: Any state reachable in <= 6 steps
- **Implementation**: BFS max_depth = 6; `C4Space.shortest_path_length()` enforces bound

### Metaprogram Theory -> Implementation
- **Theory**: 153 cognitive patterns with C4 coordinates
- **Implementation**: `ALL_METAPROGRAMS` list with 153 entries, each with `C4Coord`

### IMPACT Theory -> Implementation
- **Theory**: 6-phase problem-solving with validation gates
- **Implementation**: `ImpactEngine.solve()` with `_check_phase_convergence()` and `_adaptive_transition()`

---

*Generated: 2026-05-10*
*Version: P5 Theory-Implementation Alignment*
