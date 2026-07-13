# C4REQBER Architecture (C4R)

> ⚠️ **HISTORICAL (v5.6.0, 2026-06-03).** Superseded for the current architectural
> picture by [`ARCHITECTURE_AUDIT.md`](./ARCHITECTURE_AUDIT.md) (refreshed 2026-06-24).
> Kept for the C4/QZRF/UCOS design rationale; treat structural/path claims as dated.

> **Version:** 5.6.0
> **Date:** 2026-06-03
> **Systems:** C4 · QZRF · UCOS · CDI · TOTE · MatrixDream

---

## 1. Philosophy

C4REQBER is a **cognitive-scientific discovery platform** that treats hypothesis generation as a formal, verifiable process. It combines:

- **Cognitive models** (C4 Z₃³ space, QZRF operators, MP rotation) for structured thinking
- **Knowledge integration** (33 sources) for comprehensive literature awareness
- **Simulation validation** (36 engines, 32 adapters) for empirical grounding
- **Formal verification** (Lean4, Dafny, Hoare, Z3) for mathematical rigor
- **Multi-agent debate** (Analyst, Scientist, Critic, Synthesizer) for idea refinement

The architecture follows three principles:
1. **Graceful degradation** — every component works standalone; failures cascade to safe defaults
2. **Lazy loading** — heavy dependencies (GPU engines, Web3, telemetry) load on demand
3. **Developer-first** — dummy secrets with warnings; production config via env vars

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  TUI v9  │  │ Typer CLI│  │ FastAPI  │  │  MCP Server        │  │
│  │(BubbleTea)│ │ (Rich)   │  │(SSE/WS)  │  │  (blast serve)     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────────┬──────────┘  │
│       │             │             │                  │              │
│       └─────────────┴─────────────┴──────────────────┘              │
│                         │                                           │
│              ┌──────────▼──────────┐                                │
│              │   API Gateway       │                                │
│              │  (Auth / Metrics)   │                                │
│              └──────────┬──────────┘                                │
└─────────────────────────┼──────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Cognitive   │ │  Knowledge   │ │  Simulation  │
│   Engine     │ │  Orchestrator│ │   Engine     │
│              │ │              │ │   Map        │
│ • C4 Space   │ │ • 33 Sources │ │ • 36 Engines │
│ • QZRF       │ │ • MegaDB     │ │ • 32 Adapters│
│ • MP Library │ │ • Search All │ │ • Runner v2  │
│ • CDI Engine │ │ • ArXiv      │ │ • VirtualBio │
│ • TOTE Loop  │ │ • PubMed     │ │ • PatternEng │
│ • MatrixDream│ │ • ORCID      │ │              │
│ • IMPACT     │ │ • ...        │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┴────────────────┘
                          │
              ┌───────────▼───────────┐
              │   Agent Pipeline      │
              │  UniversalSolve v2    │
              │  HILDiscovery v4      │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │   Quality & Verify    │
              │  Quality Gates        │
              │  Formal Verification  │
              │  Reality Check        │
              └───────────────────────┘
```

---

## 3. Cognitive Layer

### 3.1 C4 Space — Z₃³ Cognitive Coordinates

The **C4 model** classifies every problem into a 3×3×3 grid:

| Axis | Values | Meaning |
|------|--------|---------|
| Time (Z₀) | 0=Past, 1=Present, 2=Future | Temporal perspective |
| Scale (Z₁) | 0=Concrete, 1=Abstract, 2=Meta | Abstraction level |
| Agency (Z₂) | 0=Self, 1=Other, 2=System | Actor perspective |

**Key states:**
- `000` — Personal concrete memories (past, concrete, self)
- `111` — Current abstract collaboration (present, abstract, other)
- `222` — System-level future vision (future, meta, system)

**Implementation:** `src/c4/engine.py` — `C4Space.fingerprint(text)` returns a `C4State` coordinate.

### 3.2 QZRF — Quantum Z-Operators

**QZRF** (Quantum Z-Resonance Framework) provides operators that transform problems between cognitive states:

| Operator | Effect | Use Case |
|----------|--------|----------|
| Z-Shift | Moves along Time axis | Retrospective analysis |
| Z-Scale | Moves along Scale axis | Abstraction/concretion |
| Z-Agent | Moves along Agency axis | Perspective switching |
| Z-Resonance | Superposition of states | Creative synthesis |

**Implementation:** `src/metamodels/qzrf/operators.py` — `QzrfLibrary.select(c4_state)` returns applicable operators.

### 3.3 MP Rotation — 23 Core Metaprograms

The **MP Library** (`src/metamodels/mp/`) implements 23 core metaprograms (MP-01..MP-23) organized across 9 perceptual dimensions. Each metaprogram defines two poles that shape how an agent perceives and reasons about a problem:

| Dimension | MPs | Examples |
|-----------|-----|----------|
| **Thinking** (5) | MP-01..MP-05 | Toward/Away, Options/Procedures, Global/Detail, Match/Mismatch, Rational/Intuitive |
| **Feeling** (3) | MP-06..MP-08 | Optimistic/Pessimistic, Internal/External, Proactive/Reactive |
| **Doing** (3) | MP-09..MP-11 | Independent/Cooperative, Fast/Slow, Aggressive/Defensive |
| **Relating** (2) | MP-12..MP-13 | Similar/Different, Leading/Following |
| **Perceiving** (2) | MP-14..MP-15 | Visual/Auditory/Kinesthetic, Abstract/Concrete |
| **Time** (2) | MP-16..MP-17 | Past/Present/Future, Short-term/Long-term |
| **Chunking** (2) | MP-18..MP-19 | General/Specific, Deep/Wide |
| **Direction** (2) | MP-20..MP-21 | Goal/Process, Growth/Protection |
| **Reason** (2) | MP-22..MP-23 | Possibility/Necessity, Evidence/Tradition |

**Pipeline integration:**
1. `MPLibrary.rotate_profiles(problem, n=3)` selects 3 diverse profiles: `systems` + `critical` + a keyword-matched third ("design"→creative, "implement"→pragmatic, "feel"→intuitive).
2. `MPRotationEngine.analyze()` runs profiles against the problem, synthesizes a unified view, and computes a consensus score.
3. `step_04_mp_rotation.py` (pipeline step `s4`) executes rotation. Output: `perspectives` (list of `AgentPerspective` with confidence), `consensus_score`, `dynamic_profiles_used`.
4. Dynamic fallback: `MPLLMDynamicGenerator.generate_dynamic_profiles()` generates LLM-based profiles; falls back to static `MPLibrary` on failure.

**Implementation:** `src/metamodels/mp/` — `data.py` (23 MPs), `patterns.py` (MPLibrary), `profiles.py` (MPRotationEngine)

### 3.4 CDI — Contradiction Detection & Integration

**CDI** identifies logical contradictions in hypotheses and suggests resolutions:

1. **Detect** — Formal contradiction extraction
2. **Analyze** — Root cause tracing
3. **Resolve** — Synthesis of non-contradictory alternative

**Implementation:** `src/core/cdi_engine.py`

### 3.5 TOTE — Test-Operate-Test-Exit

The **TOTE loop** provides iterative refinement:
- **Test** — Evaluate hypothesis against criteria
- **Operate** — Apply transformation
- **Test** — Re-evaluate
- **Exit** — Return when threshold met

**Implementation:** Embedded in pipeline phases (`src/pipeline/hil_phases/`)

### 3.6 MatrixDream — Latent Space Exploration

**MatrixDream** generates novel hypotheses by traversing the latent space of existing knowledge:
- Vector embedding of literature
- Traversal along underexplored dimensions
- Synthesis of cross-domain analogies

**Implementation:** `src/metamodels/matrixdream.py`

### 3.7 IMPACT — Entity & Relation Extraction

**IMPACT** maps problems into entity-relation graphs:
- **Identify** entities (actors, objects, concepts)
- **Map** relations between them
- **Classify** relation types
- **Trace** causal chains

**Implementation:** `src/metamodels/impact.py`

---

## 4. Knowledge Layer — 33 Sources

### 4.1 Source Catalog

| # | Source | Type | Domain |
|---|--------|------|--------|
| 1 | ArXiv | API | Physics, Math, CS |
| 2 | PubMed | API | Biology, Medicine |
| 3 | Semantic Scholar | API | AI/ML |
| 4 | CrossRef | API | General DOI |
| 5 | ORCID | API | Author profiles |
| 6 | Brave Search | API | Web |
| 7 | Google Scholar | Scraping | General |
| 8 | IEEE Xplore | API | Engineering |
| 9 | ACM DL | API | CS |
| 10 | JSTOR | API | Humanities |
| 11 | Springer | API | Science |
| 12 | Nature | API | Science |
| 13 | Science | API | Science |
| 14 | PLOS | API | Open access |
| 15 | BioRxiv | API | Preprints |
| 16 | MedRxiv | API | Preprints |
| 17 | SSRN | API | Social science |
| 18 | RePEc | API | Economics |
| 19 | Astrophysics Data System | API | Astronomy |
| 20 | Inspire HEP | API | High-energy physics |
| 21 | DBLP | API | CS bibliography |
| 22 | Wikidata | API | Structured knowledge |
| 23 | OpenAlex | API | Open bibliography |
| 24 | Dimensions | API | Research analytics |
| 25 | Altmetric | API | Impact metrics |
| 26 | CORE | API | Open access papers |
| 27 | Europe PMC | API | Biomedical |
| 28 | ChemRxiv | API | Chemistry |
| 29 | PsyArXiv | API | Psychology |
| 30 | SocArXiv | API | Sociology |
| 31 | LawArXiv | API | Law |
| 32 | EarthArXiv | API | Earth science |
| 33 | Local Files | Filesystem | User corpus |

### 4.2 Orchestration

`MultiSourceSearcher` (`src/knowledge/orchestrator.py`) coordinates all sources:
- Parallel search with `asyncio.gather`
- Deduplication via content hash
- Caching with TTL
- Fallback chain (API → scraping → local)

### 4.3 MegaDB

`MegaDatabase` (`src/knowledge/mega_db.py`) provides unified storage:
- SQLite backend (default)
- PostgreSQL backend (production)
- Full-text search via `fts5`
- Vector embeddings for semantic similarity

---

## 5. Simulation Layer — 36 Engines, 32 Adapters

### 5.1 Engine Inventory

| # | Engine | Domain | GPU | Adapter |
|---|--------|--------|-----|---------|
| 1 | Newton | General physics | Yes | Internal |
| 2 | JaxSim | Differentiable sim | Yes | Internal |
| 3 | TorchSim | Atomistic | Yes | Internal |
| 4 | Schr | Quantum | Yes | Internal |
| 5 | Legacy | CPU fallback | No | Internal |
| 6 | FEniCSx | FEM/PDE | Yes | P1 |
| 7 | OpenFOAM | CFD | Yes | P1 |
| 8 | GROMACS | MD | Yes | P1 |
| 9 | LAMMPS | MD | Yes | P1 |
| 10 | MDAnalysis | Trajectory | No | P1 |
| 11 | PySCF | Quantum chem | Yes | P1 |
| 12 | Psi4 | Quantum chem | Yes | P1 |
| 13 | Quantum Espresso | DFT | Yes | P1 |
| 14 | Tellurium | Systems biology | No | P1 |
| 15 | NEURON | Neuron sim | No | P1 |
| 16 | Brian2 | SNN | No | P1 |
| 17 | Jaxley | Differentiable neuron | Yes | P1 |
| 18 | COPASI | Biochemical | No | P1 |
| 19 | Xarray | Climate data | No | P1 |
| 20 | WRF | Weather | Yes | P1 |
| 21 | Mesa | ABM | No | P1 |
| 22 | SimPy | Discrete event | No | P1 |
| 23 | Rebound | N-body | No | P1 |
| 24 | AMUSE | Astrophysics | No | P1 |
| 25 | MuJoCo | Robotics | Yes | P1 |
| 26 | PyBullet | Robotics | No | P1 |
| 27 | DiffEqPy | ODE/SDE/DDE | No | P1 |
| 28 | Taichi | GPU graphics | Yes | P1 |
| 29 | JAX MD | Differentiable MD | Yes | P1 |
| 30 | JAX-LaB | LBM | Yes | P1 |
| 31 | ModelingToolkit | Symbolic ODE | No | P1 |
| 32 | OpenMM | Molecular dynamics | Yes | P1 |
| 33 | Vina | Protein docking | No | P1 |
| 34 | BoolNet | Gene networks | No | P1 |
| 35 | COBRApy | Metabolic flux | No | P1 |
| 36 | SLiM | Population genetics | No | P1 |

### 5.2 Adapter Architecture

All P1 adapters inherit from `BaseSimulationAdapter` (`src/simulations/base_adapter.py`):

```python
class BaseSimulationAdapter(abc.ABC):
    _engine_name: str = ""
    _package_checks: list[str] = []
    _install_hint: str = ""

    def is_available(self) -> bool: ...
    def configure(self, params: dict) -> None: ...
    def run(self, input_data: dict | None = None) -> SimulationResult: ...
    def get_status(self) -> SimStatus: ...
    def cleanup(self) -> None: ...
```

**Key features:**
- Lazy import — adapters load only when requested
- Graceful fallback — `UNAVAILABLE` status with install hint
- Timing — all runs are timed
- Exception wrapping — errors become `ERROR` status with logs

### 5.3 Pattern Engine Map

`PatternEngineMap` (`src/simulations/pattern_engine_map.py`) maps 162+ simulation patterns to optimal engines:

- `PATTERN_ENGINE_MAP` — direct pattern → engine mapping
- `CATEGORY_ENGINE_MAP` — category aliases (e.g., `cfd → newton`)
- `GPU_PATTERNS` — patterns that benefit from GPU
- `ACCELERATION_FACTORS` — estimated speedup per pattern

### 5.4 Runner v2

`PatternRunnerV2` (`src/simulations/runner_v2.py`) executes simulations:
1. Determines engine via `PatternEngineMap`
2. Lazy-loads adapter via `_get_bridge()`
3. Runs with timing metadata
4. Falls back to `legacy` CPU mode if GPU unavailable

### 5.5 Virtual Bio Orchestrator

`VirtualBioOrchestrator` (`src/simulations/virtual_bio.py`) provides bio-specific simulation coordination:
- 6 domains: molecular dynamics, protein docking, gene networks, metabolic flux, population genetics, quantum chemistry
- Cost estimation for vast.ai GPU instances
- GPU-aware install hints
- Adapter-based execution via `BaseSimulationAdapter`

---

## 6. API Layer

### 6.1 FastAPI Server

`src/api/server.py` — RESTful API with:
- **SSE/WebSocket** streaming for real-time pipeline progress
- **Auth** — JWT with dev-mode bypass
- **Metrics** — Prometheus `/metrics` endpoint
- **Tracing** — OpenTelemetry (optional, lazy-loaded)

### 6.2 MCP Server

`src/mcp_server/server.py` — Model Context Protocol server:
- 21+ tools exposed via `blast serve --mcp`
- Tools: `blast_solve`, `blast_turbo`, `blast_flash`, `blast_turbofactory`, `blast_auto`
- JSON schemas for structured function calling

### 6.3 Auth

- `AuthManager` — JWT validation with dummy secret fallback
- `web3.py` — Web3 auth with lazy secret loading
- Dev mode — bypasses auth for local development

---

## 7. CLI Layer

### 7.1 Typer + Rich

`src/cli/typer_app.py` — shared design system:
- **StyledPanel** — `rich.Panel` with CyberpunkTheme colors
- **ProgressIndicator** — `rich.Progress` with spinner + bar
- **ResultDisplay** — formatted tables/panels for results
- **StyledTable** — `rich.Table` with theme colors
- **StatusIndicator** — colored status badges

**Color palette (TUI v9 sync):**
- Primary: `#00FF41` (Matrix Green)
- Secondary: `#00D4FF` (Cyber Cyan)
- Accent: `#FF006E` (Neon Pink)
- Warning: `#FFB800` (Amber)
- Danger: `#FF2A2A` (Blood Red)

### 7.2 Commands

| Command | Description |
|---------|-------------|
| `turbo discover` | Multi-agent collaborative discovery |
| `turbo research` | Search Semantic Scholar / arXiv |
| `turbo c4` | C4 state analysis |
| `turbo triz` | TRIZ contradiction resolution |
| `turbo system` | System status |

---

## 8. TUI Layer

### 8.1 Textual v8

Bubble Tea-based terminal interface (`src/tui/v9/`; there is no `src/tui/v7/`):
- 7-phase cognitive pipeline visualization
- Reactive widget tree
- Living Quantum Mascot (emotional ASCII companion)
- Lock-free theme reads via `atomic.Value`

### 8.2 Key Widgets

| Widget | Role |
|--------|------|
| `V7Header` | Status bar, API health, news ticker |
| `V7Input` | Query + mode buttons |
| `V7Pipeline` | 7-phase progress + narrative |
| `V7Result` | Metrics, hypotheses, sources |
| `V7C4Frame` | Interactive 3×3×3 cognitive grid |
| `LivingCubeMascot` | Emotional ASCII companion |

---

## 9. Data Flow

```
User Input
    │
    ▼
┌─────────────┐
│  Sanitize   │  → strip HTML, normalize unicode, block injection
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  C4 Space   │  → fingerprint problem into Z₃³ coordinate
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Knowledge  │◄───►│  Cognitive  │
│  Search     │     │  Analysis   │
│  (33 src)   │     │  (QZRF/CDI) │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 ▼
        ┌─────────────┐
        │  Hypothesis │
        │  Generation │
        └──────┬──────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│  Simulation │ │ Verification│
│  (36 eng)   │ │ (Lean4/etc) │
└──────┬──────┘ └──────┬──────┘
       │               │
       └───────┬───────┘
               ▼
        ┌─────────────┐
        │   Quality   │
        │   Gates     │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │   Output    │
        │ (Dissertation│
        │  / Report)  │
        └─────────────┘
```

---

## 10. Observer Position Shifts (O₀→O₁→O₂)

The pipeline integrates **meta-cognitive self-reflection** via `ObserverController` (`src/c4/observer.py`) inside `PipelineExecutor` (`src/agents/pipeline/executor.py`).

### Three Observer Positions

| Position | Code | Visibility | Blind Spots |
|----------|------|------------|-------------|
| **Immersed** | `O₀` | Immediate C4 neighbors only | Meta-level patterns, system-wide consequences |
| **Observing** | `O₁` | All states within Hamming distance ≤ 2 | Own observational bias, second-order effects |
| **Meta** | `O₂` | All 27 C4 states | Concrete emotional/tactical details |

### When Shifts Happen

1. **O₀ → O₁** (self-diagnostic): After step s8 (synthesis). `_run_observer_diagnostic()` shifts observer up, checks if current C4 path passes through blind spots. If yes — flag `blind_spots_detected` + recommendation. Insights injected into synthesis context (`state["observer_insights"]`).
2. **O₁ → O₂** (meta-reflection): When `PipelineObserver.should_halt()` detects stagnation (novelty ≤ 0.05 across 3 iterations). `_run_meta_reflection()` creates META frame, generates system-level recommendation: "consider alternative routes or scientist paths".
3. **Post-pipeline O₂ loop**: If final `confidence < 0.72`, meta-reflection re-runs automatically.

### Alternative C4 Derivation

`_derive_alternative_c4()` parses O₂ insights for keywords and shifts the corresponding axis:
- "future"/"long-term" → **T+1** (Time axis up)
- "meta"/"abstract" → **S+1** (Scale axis up)
- "system"/"collective" → **A+1** (Agency axis up)
- "present"/"immediate" → **T−1**
- "concrete"/"specific" → **S−1**
- "self"/"individual" → **A−1**

If no keyword matches → deterministic rotation `(T+1, S+1, A+1) mod 3` to force exploration.

### Events

| Event | Stage | Payload |
|-------|-------|---------|
| `observer_diagnostic` | `observer_o1` | `position`, `visible_states_count`, `blind_spots`, `insights`, `flag` |
| `observer_meta` | `observer_o2` | `position`, `visible_states_count`, `blind_spots`, `insights`, `flag`, `recommendation` |

Consumed by TUI v9 and WebSocket clients for real-time meta-cognitive feedback.

---

## 11. Security & Resilience

| Concern | Mitigation |
|---------|------------|
| Input injection | `_sanitize()` strips HTML, normalizes Unicode, removes control chars |
| Prompt injection | Nonce delimiters, LaTeX escaping |
| JWT secret | `os.getenv("JWT_SECRET", "dev-secret-...")` with warning log |
| Import crashes | All heavy deps wrapped in `try/except ImportError` |
| Duplicate metrics | `_safe_metric()` helper for Prometheus |
| Rate abuse | Per-operation sliding-window limiters |
| Backend outage | Every bridge has `try/except` + safe default |
| GPU unavailability | Automatic fallback to CPU (`force_cpu=True`) |

---

## 12. Performance

| Component | Target |
|-----------|--------|
| Import audit | 0 errors across 1186+ modules |
| Test suite | 565+ tests, < 2 min full run |
| LLM calls | 10 / 60 s rate limit |
| Search | 5 / 60 s rate limit |
| Simulation | 30 s hard timeout |
| TUI pipeline | Per-phase expected durations (A=2s … G=2s) |
| Memory | < 100 MB under load |

---

## 13. Extension Points

| Extension | How To |
|-----------|--------|
| **New knowledge source** | Add adapter in `src/knowledge/sources/`, register in `orchestrator.py` |
| **New simulation engine** | Create `*_bridge.py` inheriting `BaseSimulationAdapter`, add to `runner_v2.py` and `pattern_engine_map.py` |
| **New cognitive model** | Add metamodel in `src/metamodels/`, integrate in pipeline phases |
| **New pipeline phase** | Add `_phase_*` method in TUI / pipeline, wire in orchestrator |
| **New CLI command** | Add Typer sub-app in `src/cli/typer_*.py`, register in `typer_app.py` |
| **New API endpoint** | Add router in `src/api/routers/`, register in `server.py` |
| **New MCP tool** | Add async function in `src/mcp_server/blast_tools.py`, register schema |

---

## 14. File Map

```
C4REQBER/
├── src/
│   ├── api/                    # FastAPI server, routers, auth, metrics
│   ├── auth/                   # JWT, Web3 auth
│   ├── c4/                     # C4 cognitive engine
│   ├── cli/                    # Typer CLI (Rich UI)
│   ├── core/                   # CDI, profile manager
│   ├── discovery/              # Discovery engine, gap analysis
│   ├── knowledge/              # 33 sources, orchestrator, MegaDB
│   ├── metamodels/             # QZRF, MP, IMPACT, MatrixDream
│   ├── mcp_server/             # MCP server, blast_tools, schemas
│   ├── models/                 # Pydantic schemas
│   ├── observability/          # OpenTelemetry tracing
│   ├── pipeline/               # HIL pipeline, quality gates
│   ├── plugins/                # Plugin registry
│   ├── simulations/            # 36 engines, 32 adapters, runner_v2
│   ├── tui/                    # Go TUI v9 cockpit
│   └── utils/                  # Shared utilities
├── tests/                      # Test suite (565+)
├── dissertations/              # Generated output
├── ARCHITECTURE_C4R.md         # This document
├── src/tui/v9/ARCHITECTURE.md  # TUI-specific architecture
└── AGENTS.md                   # Agent developer guide
```

---

*End of document. For developer setup, see `INSTALL.md` (Phase 6).*
