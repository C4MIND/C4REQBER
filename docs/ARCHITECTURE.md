# c4reqber v5.4.0 — BLAST Architecture Document

> ⚠️ **HISTORICAL (v5.4.0).** Superseded for the current architectural picture by
> [`/ARCHITECTURE_AUDIT.md`](../ARCHITECTURE_AUDIT.md) (refreshed 2026-06-24).
> Kept for historical context; treat version numbers and structural claims as dated.

## 🧠 System Overview

c4reqber (formerly TURBO-CDI) v5.4.0 is **BLAST** — Brain-like Adaptive System for Thought. A cognitive exoskeleton with a 4-mode pipeline system, terminal-first UI/UX, and formal C4-META architecture. **The UI/UX Polish + Code Quality Audit Release.**

**Theory vs. Implementation:** The C4-META framework (27-state cognitive space Z₃³, Theorem 11) is a formal theory from the `adaptive-topology` research repository. c4reqber is the **production implementation** — Python-based, with 9,800+ tests, **9 real verification backends** (incl. CVC5, TLA+, Alloy), 51 knowledge sources, 21 MCP tools, and regression-gated quality gates.

**Whitepaper:** [WHITEPAPER.md](../WHITEPAPER.md) (EN) · [WHITEPAPER.ru.md](../WHITEPAPER.ru.md) (RU) · [VERIFICATION_BACKENDS.md](VERIFICATION_BACKENDS.md)

### BLAST 4-Mode System

```
blast solve "problem"      → UniversalSolvePipeline v2    → Strategic artifacts
blast turbo "topic"        → HILDiscoveryPipeline v4      → Paradigm-shifting dissertations
blast flash "question"     → Quick LLM + USP cognitive    → Instant answers
blast turbofactory "dom"   → Parallel pipeline factory    → Ultimate domain reports

blast "query"              → Auto-router selects best mode → Zero-config entry
```

---

## 🏗 Architecture Layers (7 Layers)

### Layer 0: BLAST CLI (4-Mode Entry Point)
```
blast_cli/ (src/cli/)
├── blast_app.py          — Typer CLI app with 4 mode commands + auto-router
├── blast_core.py         — Core execution logic for solve/turbo/flash/turbofactory
├── mode_router.py        — Keyword-based auto-routing (scientific→turbo, paradigm→turbofactory, etc.)
└── commands/             — Legacy turbo commands (backward compatible)
```

**Mode Characteristics:**
| Mode | Pipeline | Duration | Output | Quality |
|------|----------|----------|--------|---------|
| solve | UniversalSolvePipeline v2 | 30-90s | Strategic artifact (PRD/plan/code) | Quality gates + reality check |
| turbo | HILDiscoveryPipeline v4 | 90-300s | Dissertation (A+ possible) | 7 gates, 0-100 score, iterative paradigm detection |
| flash | Quick LLM + USP cognitive | 2-10s | Concise answer | USP components in --deep |
| turbofactory | Parallel orchestrator (solve/turbo/mixed) | 5-30min | Synthesis of N pipelines | Quality-weighted aggregation |

**Auto-Router Logic:**
- Scientific keywords (hypothesis, quantum, neuro, etc.) ≥ 2 matches → turbo
- Paradigm keywords (survey, comprehensive, state of the art) ≥ 2 matches → turbofactory
- Short question (what is, how to, explain) ≤ 120 chars → flash
- Default → solve

### Layer 1: Core Engine (C4-META)
- **27 cognitive states** in Z₃³ cube — formal model from adaptive-topology theory
- **6 operators**: T, T_INV, S, S_INV, A, A_INV (extended from 3 in v5.2: T, S, A)
- **C4TransitionGraph**: 6 edges per node (was 3) — full bidirectional navigation with inverses
- **Theorem 11 corrected**: Undirected diameter = 3, Directed forward diameter = 6 — proven in Agda (see theory repo). The maximum directed forward path from any → any state is 6 steps; the undirected min-distance is at most 3.
- **shortest_path_length bug fixed**: was returning `hamming * 2` (double count), now returns correct Hamming distance
- **3 C4State classes unified**: `core.C4State`, `types.C4State`, `engine.C4State` all supporting `t/s/a` + `T/S/A` + `shift_time`/`scale`/`agency`/`invert`/`distance` fields — no more mismatch between layers
- **Core operators**: phi/mu placeholders replaced with real Z₃ operations
- **Pipeline Modes**: 3 modes — `autopilot` (default, full validation), `turbo` (parallel multi-agent, skips validation), `deep-work` (verification + proof export)
- **Adaptive Layout**: Auto-detects task type (minimal/standard/deep-work/turbo/tui-mode)
- **Session Timeline**: Visual history + time-travel debug

**Honest description:** The C4 state space is formally well-defined and the engine navigates it correctly. The "adaptive" part of the layout is rule-based heuristics, not learned.

---

## SystemAnalyzer (Phase A — Universal Entry Point)

`src/c4/system_analyzer.py` runs as **Phase A** before any pipeline mode is selected. It is the universal entry point for ALL user queries.

### What it does

1. **Extract entities** from the query — key concepts and multi-word phrases
2. **Build dependency graph** — explicit causal + implicit order + LLM-deepened hidden dependencies
3. **Classify systemicity** — 0.0 (pseudo-atomic) to 1.0 (deeply systemic)
4. **Decompose** into sub-problems with explicit dependency edges
5. **Rank by graph centrality** — most foundational sub-problems first
6. **Route each sub-problem** through C4 + scientist matching
7. **Find critical path** — chain of most-dependent sub-problems to solve first

### Systemicity Classification

| Label | Range | Description |
|-------|-------|-------------|
| pseudo-atomic | 0.0–0.2 | Nearly independent sub-problems |
| weakly systemic | 0.2–0.4 | Some implicit connections |
| moderately systemic | 0.4–0.6 | Explicit dependencies detected |
| strongly systemic | 0.6–0.8 | Dense causal network |
| deeply systemic | 0.8–1.0 | Emergent, feedback-driven system |

**Formula:**
- Explicit indicators (causal words like "causes", "leads to"): +0.08 each, max 0.5
- Implicit indicators ("feedback", "system", "network", etc.): weighted ×0.1, max 0.4
- Graph complexity (edge ratio): max 0.3
- Entity count: max 0.2
- **Total capped at 1.0**

### 4-Layer Depth Tier Model

SystemAnalyzer classifies every query into one of four depth tiers that determine how much cognitive machinery is engaged:

| Tier | Name | Systemicity | What happens |
|------|------|-------------|--------------|
| 1 | **Atomic** | 0.0–0.2 | Single cognitive path, minimal decomposition |
| 2 | **Compositional** | 0.2–0.4 | Few sub-problems, shallow dependencies |
| 3 | **Relational** | 0.4–0.6 | Multiple interdependent sub-problems, full C4 routing |
| 4 | **Emergent** | 0.6–1.0 | Dense dependency graph, critical path analysis, all engines engaged |

### Internal Architecture

```
SystemAnalyzer
├── CognitiveRouter (src/c4/cognitive_router.py)
│   └── Routes each sub-problem to C4 state path + scientist pattern
└── CognitiveStateClassifier (src/c4/extended_engines.py)
    └── Classifies overall query to C4 Z₃³ state
```

### Pipeline Flow (v5.3.2)

```
User Query
    ↓
[SystemAnalyzer.analyze()] — Phase A
    ├── Extract entities
    ├── Build dependency graph (explicit + implicit + LLM-deepened)
    ├── Classify systemicity 0.0→1.0
    ├── Decompose → sub-problems
    ├── Rank by centrality (foundational first)
    └── Route each through C4 + scientist matching
    ↓
[Decision] — systemicity + sub-problem count
    ├── pseudo-atomic / 1–2 sub-problems → MultiPromptRouter (quick path)
    └── moderate+ systemic / 3+ sub-problems → SystemSynthesizer (full path)
    ↓
[CognitiveRouter] — C4 state classification + engine engagement
    ↓
[Selected Pipeline] — UniversalSolvePipeline / HILDiscoveryPipeline / flash / turbofactory
```

**Honest description:** Entity extraction is heuristic (stopword removal + phrase merging). Dependency detection is explicit causal + implicit order + optional LLM deepening. Systemicity is a weighted heuristic, not a learned model. The 4-tier depth model is rule-based. It works well for routing but is not a formal systems-theoretic measure.

---

### Layer 2: Knowledge & Discovery
- **37 knowledge sources** via `orchestrator.py`: arXiv, PubMed, Semantic Scholar, OpenAlex, CrossRef, CORE, DOAJ, Europe PMC, DBLP, GitHub, Zenodo, BioRxiv, MedRxiv, CiNii, RSCI, Brave, Tavily, Exa, Google Patents, EPO, Figshare, ScholarAPI, arXiv.gg, ORCID, NCBI E-utilities, PubChem, ChEMBL, Materials Project, AFLOW, Kaggle, UCI ML, Harvard Dataverse, re3data + 4 premium APIs. `multi_source.py` preserved as backward-compat shim.
- **GapAnalyzer ABC**: `src/discovery/gap_analyzer_base.py` — unified interface for `AutoGapAnalyzer` and `GapMiner`. Disconfirmatory `RESOLUTION_INDICATORS` added (10 phrases) to prevent gap-confirmation bias.
- **NoveltyValidator → HARD GATE**: Now adds to `abort_reasons` (was warning-only). Threshold: `min_novelty_score` (0.5).
- **AlreadyShiftedDetector → ITERATIVE**: Re-checked inside refinement loop on every iteration. No longer immortal across refinements. Subtractivnce terms added to confidence calculation.
- **Domain poisoning fixed**: Keyword lists extracted from paper corpus, no hardcoded neurological vocabulary fallback.
- **Dissertation**: `_llm_generate` uses OpenRouter API direct call (openai/gpt-4o-mini), max_tokens 2500/section, post-generation expansion at <800 words.

### Layer 3: TRIZ & Simulations
- **40 TRIZ principles** for contradiction resolution — complete library from classical TRIZ literature
- **TRIZ bridge**: Real implementation via `triz/matrix.py` (was placeholder `[1,2,3]` in v5.2) — proper contradiction matrix with principle rankings for all 39×39 engineering parameters
- **115 pattern mappings** in pattern engine map
- **Constraint solver**: Buckingham π-theorem implemented via `numpy.linalg.svd` null-space computation — honest numerical solution (was fake placeholder in v5.2)
- **4 simulation engines**: Newton (auto-detection, CPU functional, GPU via Warp), TorchSim (MLIP models — M3GNet, CHGNet, etc.), JaxSim (fallback Euler integration), vast.ai (GPU delegation for heavy workloads)
- **Newton Physics Engine**: Auto-detects problem type; CPU mode functional; GPU acceleration via Warp exists as interface, not production-tested

**Honest description:** TRIZ principles and contradiction matrix are complete and correct per Altshuller. TRIZ bridge now has a real implementation. Constraint solver uses true SVD null-space computation. Physics simulations: Newton CPU works; TorchSim MLIP interface is functional; JaxSim is fallback; vast.ai delegation is interface-only. Quantum backends are not implemented.

### Layer 4: Verification & Export (v5.6.0)
- **9 real verification backends**: Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy
- **MathDetector**: Classifies hypotheses into Categories A/B/C — Category A (mathematically scaffolded → full formal verification), B (empirical with math bridge → structural check + flagged assumptions), C (qualitative → skip, literature consistency only)
- **Verification guardrails**: Complexity pre-flight estimation → skip/fallback decision. Memory limits: 256MB (Z3/CVC5) — 1GB (Agda). Hang detection: 5-60s stall timeout per backend. Fallback cascade: Lean4→Z3/CVC5→TLA+→Alloy→skip.
- **Known hang patterns**: Lean4: `simp/omega/native_decide`. Coq: `auto/ring/firstorder`. Dafny: `forall/exists` triggers. Agda: `termination/mutual`. TLA+: `liveness/fairness`. Alloy: `reachable/transitive`.
- **Proof export**: Each verified backend exports to file (.lean/.v/.smt2/.dfy/.tla/.als) + verification_summary.json
- **Appendix A**: All generated documents include verification appendix with proof summaries and file references
- **Export formats**: LaTeX, Markdown, JSON, HTML, PDF, BibTeX — functional

**Honest description:** Lean4, Coq, Dafny, Agda, CVC5, TLA+, and Alloy have real client implementations with install scripts (`tools/install-verifiers.sh`). Success rate depends on problem domain — trivial properties verify, complex scientific hypotheses may need LLM proof generation.

### Layer 4.5: Verification v8 (6-Layer Defense Pipeline)

The verification system was refactored from a single `HybridVerifier` into a **6-layer defense**:

| Layer | Component | Role | Speed |
|-------|-----------|------|-------|
| L1 | `StatisticalValidator` (SciPy) | Fast path for numerical claims (t-test, χ², KS, correlation) | <1s |
| L2 | `AutoTheoremFormulator` (Z3) | Numerical bounds / constraint checking | <5s |
| L3 | `LLMProver` + RAG | Few-shot proof generation across 6 languages | 15-60s |
| L4 | `ConsensusEngine` | Parallel Lean4 + Coq + Dafny, requires 2/3 agreement | 60-180s |
| L5 | `SemanticAlignmentChecker` | Verifies proof actually proves the stated theorem | 5-10s |
| L6 | `UnifiedScoreCalculator` | Aggregates all backends into 0-100 score + recommendations | <1s |

**Few-Shot Example Library:**
| Language | Examples | Coverage |
|----------|----------|----------|
| Lean4 | 56 | Nat proofs, induction, lists, inequalities |
| Coq | 48 | Arithmetic, booleans, lists, divisibility |
| Dafny | 52 | Methods, loops, invariants, data structures |
| Z3 | 50 | Integer/real constraints, parity, divisibility |
| Agda | 45 | Dependent types, equality, list proofs |

**RAG Retriever**: `ProofExampleRetriever` (TF-IDF + cosine similarity) selects top-k similar examples for few-shot prompting. Zero GPU required.

**Endpoints:**
- `POST /v8/verification/hypothesis` — unified entry point (L1→L6 cascade)
- `POST /v8/verification/verify` — legacy direct backend access

### Layer 4.6: Causal Inference Engine (v8)

**Libraries**: DoWhy 0.8 + EconML 0.16 + gCastle 1.0.4 (all installed on Python 3.14.5). CausalNex excluded (requires Python ≤3.10, not used in codebase).

**Components:**
- `CausalDiscoveryEngine` — PC, FCI, NOTEARS, ANM algorithms. Falls back to correlation matrix if gCastle unavailable.
- `CausalEstimationEngine` — ATE estimation via DoWhy backdoor methods + EconML CausalForest/DoubleML. Falls back to linear regression without DoWhy.
- `GPSCM` — Gaussian Process Structural Causal Model for counterfactuals.

**Pipeline integration**: `run_causal_do_calculus()` uses real causal discovery + estimation when `len(df) >= 100`, otherwise returns toy SCM with explicit `note: "toy_model_fallback_no_data"`.

### Layer 4.7: Hypothesis Ranking (P2)

**MCDM-based ranking** inserted between hypothesis generation and simulation:

1. `PriorScorer` — novelty (embedding distance), plausibility (citation support), formalizability, falsifiability
2. `EIGEstimator` — Expected Information Gain via Monte Carlo simulation sampling
3. `CostModel` — LLM cost, CPU seconds, API call estimates
4. `MCDMRanker` — Weighted sum TOPSIS with criteria: EIG 0.35, novelty 0.20, plausibility 0.20, falsifiability 0.15, cost_inverse 0.10

**Integration**: `multi_hypothesis_discovery()` runs `rank_hypotheses()` before simulation, executing simulations only on top-N ranked hypotheses (budget-aware).

### Layer 4.8: Closed-Loop Simulation (P3)

**Bayesian iterative refinement** for hypotheses:
- `BayesianHypothesisTracker` — Bayes factor updates per simulation iteration
- `ExperimentDesigner` — Latin Hypercube Sampling, adaptive sample size
- `EnsembleRunner` — Parallel simulator runs with different seeds
- `ConvergenceChecker` — Stops when `bayes_factor > 10` (accept), `< 0.1` (reject), or max iterations reached
- `HypothesisRefiner` — LLM-based refinement given simulation results
- `ClosedLoopOrchestrator` — Main loop tying all components

### Layer 4.9: Self-Directed Agenda (P4)

**Research question generation and management**:
- `AgendaGenerator` — Gap-driven, conflict-driven, extension-driven question generation from knowledge graph
- `FeasibilityChecker` — Tool availability, cost/time estimates, tractability scoring
- `PriorityScorer` — Weights: novelty 0.3, tractability 0.3, impact 0.2, alignment 0.2
- `ProgressTracker` — Open gaps vs. covered topics tracking
- **TUI Screen**: `shift+a` opens agenda overlay with approve/reject/modify actions
- **API**: `/v8/agenda/generate`, `/v8/agenda/approve`, `/v8/agenda/progress`

### Layer 4.10: Open-Ended Exploration (P5)

**Surprise-driven discovery**:
- `AnomalyDetector` — IsolationForest on literature embeddings + simulation residual outliers
- `SurpriseDrivenQuestionGenerator` — Generates candidates, filters by embedding distance from existing questions
- `FormalFrameworkExtender` — Proposes new definitions/lemmas, compiles against existing libraries

### Layer 4.11: P6 Data Sources (Tier-2 Expansion)

**9 new P6 clients** on `BaseP6Client` (TTL cache, connection pooling, httpx):

| Client | Domain | Auth |
|--------|--------|------|
| `NCBIEUtilsClient` | Biomedical (Gene, GEO, ClinVar) | API key optional |
| `PubChemClient` | Chemical structures | None |
| `ChEMBLClient` | Bioactive molecules | None |
| `MaterialsProjectClient` | DFT materials | API key |
| `AflowClient` | Computational materials | None |
| `KaggleClient` | Datasets/notebooks | Credentials |
| `UciMlClient` | ML datasets | None |
| `HarvardDataverseClient` | Research datasets | API key optional |
| `Re3dataClient` | Repository registry | None |

**Integration**: All 9 wrapped by `P6Adapter` → `BaseSourceAdapter` → `MultiSourceSearcher` with feature flags in `SOURCE_REGISTRY`.

### Layer 5: LLM Layer (5 Auto-Detected Providers)
```
LLM Providers (auto-detected):
├── Local: MLX-LM (Apple Silicon, $0/MTok), LM Studio (MLX acceleration), Ollama (cross-platform)
├── Cloud: OpenRouter (primary, arbitrary model strings), DeepSeek (direct API)
└── Fallback cascade: MLX → LM Studio → Ollama → OpenRouter → DeepSeek
```

**Arbitrary model strings supported**:
```bash
c4reqber chat --model "anthropic/claude-sonnet-4.6"
c4reqber chat --model "qwen/qwen-2.5-72b-instruct"
```

**Mock Provider**: `LLMProvider.MOCK = "mock"` for testing.

**Honest description:** LLM routing works. 5 providers are auto-detected on startup across macOS (M1-M4), Intel Mac, and Windows. OpenRouter is primary cloud provider; MLX-LM provides $0/MTok local inference on Apple Silicon. Quality of discovery is directly proportional to LLM capability. No LLM-agnostic guarantee of correctness.

### Layer 6: Pipeline Architecture (L1-L4 v5.3.0)
```
Pipeline Architecture:
├── BasePipeline (src/pipeline/base_pipeline.py) — unified base class for all 5 pipeline variants
├── StepDefinition (src/pipeline/step_definition.py) — config-driven step plan
├── PipelineResult (src/pipeline/result.py) — unified result protocol
├── PipelineObserver (src/pipeline/observer.py) — meta-observer: stagnation/halt detection
├── FinalVerifier (src/pipeline/final_verifier.py) — post-pipeline Jaccard novelty check
├── RedundantGate (src/pipeline/redundant_gates.py) — N-version voting (3 variants per critical gate)
├── DiscoveryMemory (src/pipeline/discovery_memory.py) — persistent SHA256 fingerprints
├── AutoFixRegistry (src/pipeline/auto_fix.py) — 8 known breakage patterns, self-healing imports
└── Simulation: lightweight fallback on Insufficient resources → delegated status passes gate
```

**Self-Healing Layer:** `AUTO_FIX_REGISTRY` intercepts known broken imports (e.g., `multi_source` → `orchestrator`, `result.get()` on dataclass → attribute access) and applies fixes before raising ImportError. Opt-in per module via `import_hook()`.

**Redundant Gates:** `ParadigmShiftGate`, `NoveltyGate`, `SelfCritiqueGate` — each runs 3 independent check variants with majority voting (min 2/3 agreement). Dissenting rationales are logged.

**Discovery Memory:** Every discovery is SHA256-hashed and stored in `discovery/memory/fingerprints.json`. Jaccard similarity >0.7 rejects near-duplicates. Prevents re-discovering the same idea.

### Layer 7: CLI Display (Cyberpunk TUI v3.1)
```
CLI Display Module (cli/display.py + terminal_/):
├── C44TCDIHeader      (brand + metrics + sparklines + C4 state badge)
├── CubeMascot         (8-bit states: idle/thinking/processing/discovery/error/done/paradigm)
├── LayoutManager      (5 layouts: minimal/standard/deep-work/turbo/tui-mode, multi-language auto-detect)
├── SessionTimeline    (visual history + branch rendering + time-travel cursor)
├── CyberpunkTheme     (Neon Noir palette: true-color ANSI, gradients, glow effects)
├── AnimationEngine    (60fps: MatrixRain, StateMorph, DiscoveryBurst, Glitch, Scanline, PulseGlow)
├── MiniMetricsPanel   (live token/cost/latency sparklines)
├── SystemResourceMonitor (CPU/RAM/GPU bars, optional psutil)
├── ServiceMonitor     (live service status + [B] balance refresh for Tavily/Exa/OpenRouter)
├── HumanityProblemsWidget (Crisis Radar — RSS-fed ranking by urgency×C4-fit×novelty)
└── SplashScreen       (6-phase C4 cube animation + 3-step config wizard)
```

**Cube States (8-bit enhanced):**
| State | ASCII | Effect | Commentary |
|-------|-------|--------|------------|
| idle | ▫▫▫ | Breathing pulse | C4 space ready. 27 dimensions. |
| thinking | ▫◈▫ | Blinking | Navigating cognitive space... |
| processing | ◈▣▫ | Progress fill | TRIZ matrix accessed. |
| discovery | ◈▣◈ | Rainbow + burst | Novel hypothesis detected! |
| error | ✖▫▫ | Red pulse + glitch | Anomaly in cognitive field. |
| done | ◈▣◈ ✓ | Green glow fade | Pipeline step completed. |
| paradigm | ✦◈▣◈✦ | Blink + bold | Paradigm shift cascade! |

**Honest description:** The CLI is a genuine differentiator — fast, terminal-native, and visually informative. The ASCII cube and commentary are decorative but useful for state awareness.

---

## 🔧 MCP Server (21 Tools)

### Core C4 Tools (9)
| Tool | Description | Implementation | Status |
|------|-------------|----------------|--------|
| `c4_solve` | Run discovery pipeline (HIL) | `c4/engine.py` | ✅ Stable |
| `c4_search` | Search 27 knowledge sources | `knowledge/multi_source.py` | ✅ Stable |
| `c4_triz` | Resolve contradiction via TRIZ | `triz/principles.py` | ✅ Stable |
| `c4_fingerprint` | Classify to C4 state (Z₃³) | `c4/engine.py` | ✅ Stable |
| `c4_verify` | Verify formal proof (Z3/Lean4/Coq/Dafny/Agda/Hoare) | `verification/` | ✅ Stable |
| `c4_transfer` | Cross-domain transfer | `c4/transfer_pipeline.py` | ⚠️ Beta |
| `c4_chain` | Discovery chaining | `discovery/chainer.py` | ⚠️ Beta |
| `c4_codegen` | Generate code + verify | `codegen/mcp_tool.py` | ✅ Stable |
| `c4_export` | Export discovery | `export/manager.py` | ✅ Stable |

### BLAST Mode Tools (5) — v5.2
| Tool | Description | Pipeline | Status |
|------|-------------|----------|--------|
| `blast_solve` | Strategic artifact generation | UniversalSolvePipeline v2 | ✅ Stable |
| `blast_turbo` | Paradigm-shifting dissertation | HILDiscoveryPipeline v4 | ✅ Stable |
| `blast_flash` | Quick answer + USP cognitive | Quick LLM + C4/MP/QZRF/CDI | ✅ Stable |
| `blast_turbofactory` | Parallel paradigm factory (solve/turbo/mixed) | 5-100 concurrent pipelines | ✅ Stable |
| `blast_auto` | Auto-route + execute best mode | Mode router + dispatch | ✅ Stable |

### Meta & Scientific Tools (4)
| Tool | Description | Implementation | Status |
|------|-------------|----------------|--------|
| `c4_bayesian` | Bayesian inference (MCMC/BMA) | `bayesian/router.py` | ✅ Stable |
| `c4_causal` | Causal discovery (do-calculus) | `causal/do_calculus.py` | ✅ Stable |
| `c4_autoresearch` | Iterative autoresearch loop | `operators/autoresearch.py` | ⚠️ Beta |
| `c4_meta` | Meta-cognitive reflection | `c4/routing.py` | ✅ Stable |

### Extended CLI/System Tools (3) — v5.3.6+
| Tool | Description | Implementation | Status |
|------|-------------|----------------|--------|
| `blast_analyze` | Systemicity analysis (entities, dependency graph, decomposition) | `c4/system_analyzer.py` | ✅ Stable |
| `blast_wasm_load` | Load WASM plugin module | `wasm/runtime.py` | ✅ Stable |
| `blast_wasm_list` | List loaded WASM modules and functions | `wasm/runtime.py` | ✅ Stable |

---

## 🧪 Data Flow (Example: `blast turbo "topic"`)

```
User Input (natural language)
    ↓
[SystemAnalyzer.analyze()] — Phase A
    ├── Extract entities + build dependency graph
    ├── Classify systemicity 0.0→1.0
    ├── Decompose → ranked sub-problems
    └── Route each through C4 + scientist matching
    ↓
[ModeRouter.auto_route()] → Select blast mode (solve/turbo/flash/turbofactory)
    ↓
[EventBus.emit("pipeline_start")] → Broadcast to TUI subscribers
    ↓
[Cube-Mascot.set_state("thinking")] → ◈◇◇ Thinking...
    ↓
[PipelineExecutor.execute()] → Run selected pipeline
    ↓
  ├─ solve:  UniversalSolvePipeline v2  (12 steps + HIL enhancements + observer + final verifier)
  ├─ turbo:  HILDiscoveryPipeline v4     (7 phases A-G + competing hypotheses + iterative paradigm detection)
  ├─ flash:  Quick LLM + USP cognitive   (2-10s response)
  └─ turbofactory: Parallel orchestrator (5-100 concurrent pipelines)
    ↓
[EventBus.emit("phase_start")] → Real-time phase broadcast
    ↓
[QualityGates.evaluate()] → 7 gates, 0-100 score, A+/A/B+/B/C/F grade
    ↓
[IF score < threshold]
  ├─ [IterativeQualityLoop] → Analyze failed gates → parameter changes → re-run phases (max 3)
  └─ [SelfCorrectingDissertation] → Rewrite only affected sections
    ↓
[EventBus.emit("quality_report")] → Broadcast final score + grade
    ↓
[CubeMascot.react_to_content()] → If "discovery" → ◈▣◈, if "error" → ✖◇◇
    ↓
[SessionTimeline.add_event()] → Logs event with C4 state annotation
    ↓
[ServiceMonitor.update()] → Live progress bar + quality score + API balances
    ↓
[TurboCDIHeader.update_metrics()] → Tokens/cost/latency sparklines
    ↓
[EventBus.emit("pipeline_complete")] → Final broadcast
    ↓
[Beep("discovery")] → Terminal sound
    ↓
Output with Cube-Mascot + Quality Report + Metrics
```

---

## 🚨 Known Limitations (v5.3.9)

1. **Config-Driven Executor**: FIXED — 12 methods → STEP_PLAN + config-driven loop.
2. **Pipeline Consolidation**: FIXED — `UniversalSolvePipeline` inherits `BasePipeline`. `one_click_discovery()` extracted to 7 phase modules (1311→856 lines).
3. **N-version Voting**: FIXED — 6 RedundantGate stubs → real semantic (TfidfVectorizer) + LLM judge variants. Stubs now return `abstain` (None) instead of false dissenting votes.
4. **Hoare Verification**: Honest stub — returns `"not yet implemented"`. Use Dafny or Lean4 for full verification.
5. **External Validation**: No integration with external labs, experimental databases.
6. **Test Coverage**: 52% on target modules (100% on utils/validation/safety/math_utils). Target: 80%+. 200+ pipeline tests pass.
7. **Discovery Memory**: Token-level Jaccard. No semantic embedding comparison yet.
8. **Plugin Stage Integration**: PARTIAL — PluginStageRouter exists, HIL pipeline may not call `execute_phase_plugins()` at each phase. Cognitive plugins still run as flat list in Phase D.
9. **Dead Code Removed**: `src/payments/` deleted — was unused dead code. `MockLLMClient` removed from 3 production locations.
10. **Multi-Agent Coordination**: NEW — CoordinatedDiscovery cross-validates gaps across parallel pipelines. Smart Scheduler with token-bucket rate limiting. Still in beta.

---

## 📋 Citation

**Citation:** Selyutin I.G., Kovalev N.I. (2026). *c4reqber v5.3.9: BLAST — Brain-like Adaptive System for Thought. The Multi-Agent Discovery Release.*

**Repository:** https://gitlab.com/cognitive-functors/turbo-cdi
**License:** AGPL-3.0
**Version:** v5.3.9 (Release date: 2026-05-17)

---

## 📊 Phase History

### Phase 10: Multi-Agent Discovery v5.3.9 ✅ (2026-05-17)
- **MULTI-AGENT**: CoordinatedDiscovery — parallel pipelines sharing findings, cross-validating gaps, detecting contradictions, merging consensus
- **PROVIDER AUTO-DETECT**: 5 providers (MLX, LM Studio, Ollama, OpenRouter, DeepSeek) auto-detected on startup. ProviderAwareCoordinator assigns pipelines intelligently
- **SMART SCHEDULER**: Token-bucket rate limiting + exponential backoff for `blast turbofactory`
- **TUI**: I key for Provider Dashboard (real-time status: local/cloud, load, rate limits, cost). Footer now 16 shortcuts
- **SLASH**: /sim command for simulation config
- **MCP**: 21 tools (was 18) — blast_analyze, blast_wasm_load, blast_wasm_list added
- **WAVE 6 FIXES**: 15 findings → 0: CRITICAL stub functions, ClickableCube→InteractiveCube, Body(default={}), __version__ bumped. 4x except:pass→logger. README synced. 0 bare except:pass, 0 hardcoded keys, 0 Body(default={}), 60/60 pipeline tests
- **C4 ARCHITECTURE**: C4Operator extended 3→6 (T/T_INV/S/S_INV/A/A_INV). C4TransitionGraph: 6 edges/node (was 3). Theorem 11 corrected: undirected Ø=3, directed fwd=6. shortest_path_length bug fixed (hamming*2→hamming). 3 C4State classes unified (core/types/engine). Core operators phi/mu placeholders→real Z₃.
- **BUG FIXES**: TransferResult crash with non-existent fields. MockLLMClient removed from 3 functor agent locations. Circular imports in LLM layer resolved. 80+ print()→logger.info() in pipeline. Payments module (src/payments/) deleted (dead code). TRIZ bridge placeholder [1,2,3]→real matrix.py. Buckingham π-theorem fake→numpy SVD. HF classification: 3-dim validation fix. Simulation fallback "delegated"→honest failure. Russian keywords removed from llm_classifier. torch.load security: weights_only=True. redundant_gates: stubs return abstain (None).
- **LLM CLEANUP**: MockLLMClient removed from router.py (MOCK→ValueError). AutoFallbackClient: honest error. async_client: RuntimeError retry fixed. reasoner_client: sync httpx→httpx.Client. retry_pkg imports corrected.
- **TEST QUALITY**: 14+ broken imports fixed (conftest.py sys.path). mcp_server: true→True, false→False. 66 pipeline_full failures→0. 31 C4 graph test failures→0.
- **NEW AGENTS**: `.kilo/agent/optimizer.md` (performance), `.kilo/agent/amplifier.md` (code quality).

### Phase 6: BLAST v5.2 ✅
- BLAST 4-mode CLI: `blast solve/turbo/flash/turbofactory`
- Auto-router by query keywords
- USP ↔ HIL pipeline cross-integration
- MCP: 5 new blast tools + Z3 backend

### Phase 8: Deep Audit v5.3.1 ✅ (2026-05-14)
- **CRITICAL**: Entry point fixed. API keys removed. Prompt injection + path traversal hardened. Silent errors → logged.
- **HIGH**: AlreadyShiftedDetector 5 bugfixes. Refinement loop break + dedup. Quality weighting fix. ProviderExhaustedError. PipelineObserver active. N-version stubs → honest abstain. 6 RedundantGate variants → real semantic/LLM.
- **ARCHITECTURE**: BasePipeline + USP/HIL inheritance. one_click_discovery() 1311→856 lines (7 phases). Config-driven executor (12 methods→loop). WASM CLI. MCP JSON Schema 18 tools. BibTeX/LaTeX submitter.
- **PLUGINS**: 28 total (8 compute + 16 cognitive + 4 built-in). 8 new: stat_tests, info_theory, dist_analyzer, timeseries, graph_metrics, signal_processing, dim_reduction, optimization. PluginStageRouter maps to phases A-G.
- **ROUTING**: Model-per-stage LLM (Claude 4.5 → reasoning, Qwen 72B → search, GPT-4o-mini → validation). Auto-selector by keyword/complexity/domain/mode.
- **SCIENTIFIC**: Google Scholar enabled. Navier-Stokes fluid sim. Hoare stub honest. Configurable dissertation model. Full config deserialization. Input validation.
- **DEBT**: `src/agent/` removed. v6/v7 deprecated (30 files). Test imports fixed (2712 pass).
- **TESTS**: +40 new tests. 200 pipeline tests, zero regressions.
- **EXPERT AUDIT**: 6 domain experts × full codebase audit.

### Phase 7: Self-Healing v5.3.0 ✅ (prior)
- Council of Geniuses audit (9 experts, 18 findings)
- 28-source orchestrator migration (P0.1)
- Iterative AlreadyShiftedDetector + subtractivnce (P0.2, P2.4)
- Domain poisoning fix (P0.3)
- GapAnalyzer ABC + RESOLUTION_INDICATORS (P1.1, P1.2)
- NoveltyValidator → HARD gate (P1.4)
- Competing hypotheses + domain stability (P1.3, P0.3)
- Full gate re-evaluation in refinement loop (P0.2, P1.5)
- PipelineObserver + FinalVerifier (P1.7, P1.8)
- 9/15 steps → PipelineStep subclasses (P3.1)
- BasePipeline + StepDefinition (L1)
- AUTO_FIX_REGISTRY + SelfHealingImporter (L2)
- N-version RedundantGate (L3)
- DiscoveryMemory + fingerprints (L4)
- TUI/CLI/MCP/docs updated to v5.3.0
- 13,992 tests, 0 errors

---

## 📊 Phase History

### Phase 1: Critical Fixes ✅
- `LLMProvider.MOCK` added to `src/llm/config.py` (fixes 57+ tests)
- Import fixes: `pythonpath = src` added to `pytest.ini`
- Exception handling: `except:` replaced with specific types + logging

### Phase 2: Improvements ✅
- Integrations restored: `openfang.py`, `hive.py`, `liquid_ai.py`, `eigent.py`, `yandex.py`, `n8n.py`
- Critical TODOs implemented: Hoare/Dafny stubs, SciMatic export stub

### Phase 3: Optimization & Typing ✅
- Utility extraction: `utils/error_handlers.py` with `safe_execute()`
- Type annotations for public functions
- Monitoring: `TraceLogger` integration

### Phase 4: New Features ✅
- Newton Physics Engine: CPU functional, GPU interface added
- Formal Verification: 5 backend clients implemented
- ORCID Integration: `AsyncORCIDClient` functional
- Mega-Database: 27 sources integrated

### Phase 5: Alpha Release Prep ✅
- Honest documentation (this file + README.md)
- Benchmark framework created (`src/benchmarks/`)
- Validation protocol drafted (`docs/planning/VALIDATION_PROTOCOL.md`)
- Version unified to v5.0-alpha

### Phase 6: BLAST v5.2 ✅
- BLAST 4-mode CLI: `blast solve/turbo/flash/turbofactory`
- Auto-router by query keywords
- USP ↔ HIL pipeline cross-integration
- MCP: 5 new blast tools + Z3 backend
- FlashMode: USP cognitive components in `--deep`
- Turbofactory: parallel orchestrator (5-100 pipelines)
- Quality Gates A+: 7 gates, weighted scoring
- Documentation: README, ARCHITECTURE, PRD, landing page

---

## 🎯 Roadmap

### v5.3.4 (Current — Critical Bug Fixes)

**Date:** 2026-05-16  
**Status:** ✅ Production

**Critical Fixes (6):**
- **Gap Mining**: `_topic_based_gaps()` fallback guaranteeing ≥1 gap always — even with LLM rate-limits or empty sources
- **Dissertation length**: Auto-regeneration loop (2 retries) when word count <600; eliminates empty-body dissertations from LLM rate-limits
- **TOTE validation**: Fixed `ToteEngine.run()` crash — added 4 required arguments with sensible defaults
- **Lean4 infinite retry**: Hard timeout 120s→45s, retries 3→2, log throttled to every 15s. Total verification: 25min→5min
- **RedundantGate**: Pure-Python `_simple_cosine_sim()` — no sklearn dependency
- **FunctorOrchestrator**: Confirmed ValueError on None llm_client (fixed v5.3.5)

**Performance**: Verification pipeline 80% faster. Gap Mining always produces results. Dissertation never generates empty.

### v5.3.5 (Corrected-Diameter Release)
- C4 6-operator architecture with corrected Theorem 11
- 18 MCP tools (9 core + 5 blast + 4 meta/scientific)
- 6 verification backends (Z3/Lean4/Coq/Dafny/Agda/Hoare)
- 37 knowledge sources, 101 simulation patterns
- Quality gates A+ with weighted scoring
- Dead code purged (payments, MockLLMClient)
- Test quality: 97 pipeline failures resolved → 0

### v5.4 (Target: 2026-Q3)
- **Entry point fixed**: `pyproject.toml` entry `main`→`app` — `pip install` + `blast solve` now work
- **TUI crash fixed**: 5 undefined references resolved in `c4_tui.py`
- **20 cognitive plugins**: Template stubs → LLM-powered reasoning (SWOT, 5Whys, Delphi, SCAMPER, etc.)
- **Dissertation model**: Hardcoded `gpt-4o-mini` → configurable via `DISSERTATION_MODEL` env var
- **Hoare verification**: Fake success → honest `"not yet implemented"` stub
- **WASM CLI**: `blast wasm-load/list` commands wired
- **Google Scholar**: Re-enabled (was disabled by default)
- **CPU fluid simulation**: Random noise → Navier-Stokes Euler solver
- **MCP JSON Schema**: `inputSchema` added to all 18 tools
- **BibTeX/LaTeX export**: Real `PreprintSubmitter` with .tex + .bib generation
- **BasePipeline**: Shared infrastructure in `src/pipeline/base.py`; `HILDiscoveryPipeline` inherits
- **Config save/load**: All 35 `PipelineConfig` fields deserialized
- **LLM router**: `ProviderExhaustedError` + proper exception handling + atexit session cleanup
- **Pipeline refinement**: AlreadyShiftedDetector breaks refinement loop; abort reasons deduplicated
- **AlreadyShiftedDetector fixes**: Citation velocity default 0.0, keyword fallback, per-year plateau rates
- **Quality scoring**: Weight normalization when novelty gate fails
- **Input validation**: All 4 BLAST modes reject empty strings
- **Expert audit**: 6 experts × full codebase — C4 engine, TRIZ, abduction, falsification, gaps, Bayesian, causal, MCP, pipelines, TUI, WASM, plugins
- **81 pipeline tests, zero regressions**

### v5.3.2 (2026-05-16 — SystemAnalyzer Integration)
- **SystemAnalyzer**: Universal entry point at `src/c4/system_analyzer.py` — entity extraction, dependency graph, systemicity classification, decomposition, centrality ranking, critical path
- **`blast analyze` CLI command**: Shows systemicity report for any query
- **4-layer depth tier model**: Atomic → Compositional → Relational → Emergent
- **Phase A pipeline**: SystemAnalyzer runs before MultiPromptRouter / SystemSynthesizer / CognitiveRouter

### v5.4 (Target: 2026-Q3)
- Config-driven executor (550→30 lines)
- Remaining 6 steps → PipelineStep subclasses
- All 5 pipelines inherit from BasePipeline
- N-version gate semantic/LLM stubs → real implementations

### v6.0 (Target: 2026-Q4)
- External experimental validation hooks
- Full 72 composite agents
- Real-time collaboration
- Telegram Mini App integration

---

**Project c4reqber v5.3.9 — BLAST architecture implemented. Core features production-ready. 21 MCP tools. 5 auto-detected providers. Multi-agent coordinated discovery in beta.**
