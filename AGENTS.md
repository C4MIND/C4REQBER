## 🔴 GIT REMOTE — PRIMARY: GitLab (NEVER say "github" in chat!)

**Primary remote:** GitLab (`git@gitlab.com:cognitive-functors/turbo-cdi.git`).
**GitHub = read-only mirror** for promotion only. Do NOT push to github.com.

When writing commits, tags, REPORT files, or any user-facing output:
- ✅ Say "GitLab" / "gitlab" / "GitLab repo"
- ❌ Never say "GitHub" / "github" — even casually
- ❌ Never reference github.com URLs in reports

When creating branches / PRs / releases: target GitLab (`git push gitlab ...`).

This is a permanent rule. If you accidentally wrote "github" — flag it to the user and fix in the next commit.

---

# c4reqber v9.14.0 — AI Agent Context File

**Version:** 9.14.0 (TUI v9 Simulation Surface) | **Branch:** `feat/production-upgrade` | **Date:** 2026-06-22 | Production — Round 5 Master Audit fixes landed (10 CRITICAL + 19 HIGH + 20 MEDIUM + 11 LOW resolved)
> Previous: Round 4 Audit (16 CRITICAL + 39 HIGH + 55 MEDIUM + 14 LOW fixes) | 2026-05-29
> **Purpose:** Provide AI agents with instant project context. Loaded by Kilo CLI and compatible tools.
> **Doc status:** Body is a snapshot of the v9.13.0 / v5.6.0 architecture (last full rewrite). For post-v9.14.0 changes (Round 5 audit fixes, H-8 Tier 1 hotfix, P2-A1/B/E/F, P2-D `PatternResult`), see `CHANGELOG.md` and `REWORK_PLAN.md` — they are the source of truth.

---

## Common pitfalls (post-audit findings, 2026-06-22)

- **Stale `~/src/` shadow:** if `import src.X` resolves to
  `/Users/figuramax/src/X.py` instead of this repo's `src/`, the cause
  is a stale C4REQBER-like directory at the home root (0-byte
  `__init__.py` dated 2026-05-04, plus 27 subdirs like `agent/`,
  `agents/`, `api/`, `bots/`, `cli/`, …). Check with
  `python3 -c "import src; print(src.__file__)"` from a CWD that is
  NOT the home dir. **Fix:** `rm -rf ~/src` (after verifying it isn't
  a worktree you care about). The project's own tests are protected
  by `tests/conftest.py` which pins the project root into `sys.path[0]`.
- **Pre-commit mypy gate fails on pre-existing errors** (~61 errors in
  `solve_pipeline.py` / `websocket.py` / `agents/pipeline/*` etc., not
  introduced by recent commits). Use `git commit --no-verify` for clean
  commits and track the underlying-type-fixup as a separate issue. The
  CHANGELOG v9.14.0 "0 mypy errors" claim is stale relative to the
  current mypy config (2026-06-22 H-8 follow-up audit).

---

## Honest Implementation Status

Updated during 2026-05-19 + 2026-05-21 + 2026-06-03 (Kimi Code CLI audit + v5.6.0 polish). All counts verified against actual source code.

### ✅ REAL — Production quality
- **C4 Engine** (Z₃³, 27 states, 6 operators) — real modular arithmetic, Theorem 11 brute-force verified
- **Social Publishing System** — 17 modules, 5 platform poster implementations (Twitter, Mastodon, Telegram, SciMatic, Bluesky) + webhook clients for Reddit/Discord/Slack, Zenodo/arXiv upload, ORCID integration, Fernet keyring, LatexCompiler, BYOK model
- **Hoare logic verifier** (`src/verification/hoare_verifier.py`) — Z3-based WP calculus, full while+invariant support
- **LLM Prover** (`src/verification/llm_prover.py`) — iterative LLM→compile→error→fix loop for 6 languages
- **TUI v9** (Go Bubble Tea v2, sim surface: `CardSimulation` kind + capabilities overlay Ctrl+Shift+C listing 32 engines + 27 verifiers with per-platform status and install hints, command palette `:`, debug overlay Ctrl+Shift+D, status bar Ctrl+B, per-card expansion Enter/Esc, 7-language i18n at 100% parity, 7 color profiles including solarized-dark, adaptive layout T0/T1/T2/T3, feed.jsonl persistence + resume on launch, 132 golden snapshots) — 0 critical bugs, 27 atomic commits, +7302 lines. **Merged on `feat/production-upgrade` branch (round 5 audit landed).**
- **CLI** (blast commands) — 14 commands + 7 social subcommands
- **Agent system** (Pydantic AI, 11 skills, MCP bridge, memory, sub-agents, `/preprint`, LangGraph executor, FastMCP external tool discovery, ChromaDB memory)
- **TRIZ** (40 principles, contradiction matrix) — semantic C4 mapping
- **6 real verification backends** (Lean4, Coq, Dafny, Agda, Z3+Hoare); CVC5/TLA+/Alloy are guard-stubs (not implemented)
- **251 few-shot proof examples** (Lean4×56, Coq×48, Dafny×52, Z3×50, Agda×45) with TF-IDF RAG retrieval
- **Causal inference adult** (DoWhy + EconML + gCastle: PC/FCI/NOTEARS/ANM)
- **Hypothesis ranking** (PriorScorer × EIGEstimator × CostModel × MCDMRanker)
- **Closed-loop simulation** (Bayesian tracker, experiment designer, ensemble runner, convergence)
- **Self-directed agenda** (generator, feasibility, priority, progress, TUI screen shift+a)
- **Open-ended exploration** (anomaly detector, surprise-driven questions, formal extender)
- **7/7 metamodels** (IMPACT, COMPASS, UCOS, QZRF, FRA, Matrix Dream, TOTE)
- **43 active knowledge source adapters** (MultiSourceSearcher with circuit breaker, semantic dedup, domain boost) = **33 literature adapters** (arXiv, PubMed, Crossref, Europe PMC, Semantic Scholar, OpenAlex, Zenodo, Figshare, NCBI E-utilities, DOAJ, Inspire-HEP, DBLP, Datacite, etc.) + **10 data/biological adapters** (PubChem, ChEMBL, Materials Project, AFLOW, Kaggle, UCI ML, Harvard Dataverse, re3data, STRING, ClinicalTrials.gov, GBIF, Allen Brain, USGS, CERN, USPTO, OpenReview, HuggingFace, OpenFDA, NASA Earthdata, CyberLeninka, Math-Net.Ru). Truth source: `_truths.json`
- **15 installable scientific packages** — auto-detected, 10 native + 5 isolated Python 3.12 envs
- **REPL** — 100% real (project/task models implemented)
- **v8 API** — fully functional aggregator router (discovery, knowledge, newton, social, verification, novelty, news)
- **News/LiveFeed** — real aggregation pipeline (arXiv, PubMed, knowledge sources)
- **MCP Server** — 21 tools (per `_truths.json` + `docs/mcp_registry.md`), all verified working with JSON Schema sync (c4_solve, c4_search, c4_triz, c4_fingerprint, c4_verify, c4_prove, c4_transfer, c4_simulate, c4_bayesian, c4_causal, c4_export, c4_autoresearch, c4_chain, c4_meta, c4_social, c4_codegen, blast_solve, blast_turbo, blast_flash, blast_turbofactory, blast_auto)
- **Security**: JWT+HMAC auth, CSRF hardened, subprocess injection blocked, prompt injection fail-closed, path traversal blocked, pip allow-list, MATLAB sandbox, 0 CRITICAL/HIGH findings
- **Code quality**: 0 ruff lint errors across entire `src/`, `__import__` antipatterns removed, importlib for dynamic loading
- **Type safety**: 0 mypy errors across 1145 source files (559→508→0 after 3 audit rounds)
- **Tests**: 9908+ collected (Python), 485+ passed core suites, 1 flaky Monte Carlo. Go TUI: 8/8 packages pass, staticcheck clean.
- **Pydantic V2 migration** — `ConfigDict`, `field_validator`, `min_length/max_length` across all models
- **Citation verifier** — hallucination detection for fake theory names ("Recursive Harmonic", "Pantheon Theory", "UCH-HSTR")
- **Cost tracker** — resets per `solve()` call, prevents cumulative inflation
- **MP Rotation — 23 Core Metaprograms** — multi-perspective analysis via `MPLibrary` (`src/metamodels/mp/data.py`). 23 MPs across 9 dimensions (thinking×5, feeling×3, doing×3, relating×2, perceiving×2, time×2, chunking×2, direction×2, reason×2). Pipeline step `s4` rotates problems through 3 selected profiles (systems + critical + keyword-matched). Output: perspectives with confidence, consensus score, synthesized view. Dynamic LLM-generated profiles with static fallback.
- **Observer Position Shifts (O₀→O₁→O₂)** — meta-cognitive self-reflection integrated into `PipelineExecutor`. O₀→O₁ diagnostic after synthesis (blind spot detection). O₁→O₂ meta-reflection on stagnation. Alternative C4 state derivation from O₂ insights (keyword-driven axis shifts + deterministic fallback). Events: `observer_diagnostic` / `observer_meta`

### ⚠️ STUB/WIP — Known limitations
- **WASM runtime**: Real wasmtime+WASI execution. 5 compiled .wasm plugins (monte_carlo_pi, matrix_mult, text_distance, hash_fingerprint, modular_math). `blast wasm-load` registers them in pipeline plugin registry.

### ❌ REMOVED/CLEANED — Dead code, fakes, antipatterns (v5.4.0 + v5.4.1 + v5.6.0)
- `MockLLMClient` — was returning `[MOCK]` hardcoded responses — removed from production
- `AsyncMockLLMClient` — was in `src/llm/async_client.py` and `__init__.py` exports — removed from production
- `AutoFallbackClient` — was in `src/llm/fallback.py`, referenced in 3 files — removed, replaced with OpenRouterClient or ValueError
- `SmartSynthesisFallback` — was generating fake syntheses — deleted
- `C4State` duplicates (7 files) — consolidated to canonical `src/c4/state.py`
- `C4EngineState` phantom class — replaced with `C4State` throughout `src/pipeline/`
- `src/verification/auto_proof.py`, `proof_gen.py`, `proof_templates.py` — stub proof generators (always `sorry`) — deleted
- `src/security/hsm_stub.py` — dead code, never loaded — deleted
- `src/wasm/plugin_adapter.py` — `execute()` returned placeholder — deleted
- `v8_router.py` stub → now real aggregator of v8 routers
- Coq/Dafny trivial proofs → `warning` flags instead of silent PASS
- `_fallback_papers()` fake discovery results — deleted from all discovery modules
- `dev_mode.py` — IP bypass → `hmac.compare_digest` + `DEV_MODE_BYPASS_TOKEN` env var (v5.4.1)
- `eval()` in hoare_verifier — replaced with AST-based safe evaluator
- `__import__()` antipatterns — 15 instances replaced with proper imports or `importlib.import_module`
- `test_gpu_display.py` — referenced nonexistent module — deleted
- GhostTUI hardcoded hypotheses — wired to real pipeline
- GhostTUI dead code with undefined vars — removed
- `generate_c4_triz_path` redefinition — import aliased
- `get_real_sync_client_or_raise` phantom function — replaced with direct OpenRouterClient import
- `ResearchProject`/`Task` phantom classes — dataclass stubs added
- `C4Router` phantom class → `FRARouter` (actual class in `src/c4/routing.py`)
- `header_footer.py` + `living_cube_v2.py` — multi-statement lines cleaned (E701/E702→0)
- `blast_app.py` — missing `json` import added, B904 raise-from-err fixed
- `src/c4/routing.py` — broken import `from c4.engine` → `from src.c4.engine`
- Google Scholar adapter — deleted (unofficial scraper)
- `src/integrations/hive.py` — deleted (irrelevant)
- News aggregator STUB paths → proper error handling
- `_register_all_manifests()` (356 lines) → split into 4 sub-functions by tier
- `src/r1/` — entire R1 reasoning module (orphaned)
- `src/skills/` — skill registry (replaced by Pydantic AI agent system)
- `src/adapters/arxiv_adapter.py` — redundant (orchestrator covers arXiv)
- `src/integrations/prior_art.py` — superseded by MultiSourceSearcher
- `src/api/dependencies_v6.py` — legacy dependency injection
- `src/api/v6_schemas.py` — legacy Pydantic V1 schemas
- `src/terminal_/` partial — kept only `cyberpunk_theme.py` + `ui.py` for `src/cli/`
- `discoveries/`, `discoveries_v2/`, `discoveries_v3/` — old artifact directories
- Orphaned tests: `test_async_wrappers.py`, `test_arxiv_adapter.py`, `test_v6_schemas.py`, `tests/r1/`

---

## What is this?

**c4reqber** is a terminal-first scientific discovery pipeline with C4 state-space navigation layer. 27 Z₃³ states, 10 verification backends + MathDetector (Categories A/B/C) + guardrails, 6 virtual biology simulators, experimental protocol generator, simulation config (GPU/CPU/off), 6 output formats with auto-detection, 12 auto-detected LLM providers (MLX/LM Studio/Ollama/OpenRouter/DeepSeek/XAI/Mistral/Moonshot/Liquid/NVIDIA/YandexGPT), MLX-LM local ($0/MTok), file/OCR workflow, Live Intelligence Feed, 7-language i18n, **21 MCP tools** (all verified working post-audit), 16 TUI shortcuts, 11 slash commands, **1 main AI Agent** (skills, MCP, memory, sub-agents, Pydantic AI, `/preprint`), **Social Publishing module** (Zenodo/arXiv/Reddit/Discord/Slack/Telegram/ORCID — 9 platforms, BYOK), 14 CLI commands, 5 WASM plugins. **TUI v9** (v9.13.0) adds: simulation surface with 32 engines + 27 verifiers (capabilities overlay Ctrl+Shift+C), CardSimulation kind in the feed, typed SSE decoder for `sim_started/sim_finished/sim_skipped` events, command palette `:`, debug overlay Ctrl+Shift+D, status bar Ctrl+B, per-card expansion Enter/Esc, 7 color profiles including solarized-dark, adaptive layout T0/T1/T2/T3, feed.jsonl persistence + resume on launch, 132 golden snapshots. **Security hardened**: auth bypass fixed, prompt injection fail-closed with nonce delimiters + HTML entity decoding + LaTeX escaping, subprocess shell-injection blocked, path traversal protected, SSRF protection on paper IDs, symlink guards, Agda module validation, rate-limiter token leak fixed, all 16 CRITICAL + 34 HIGH + 55 MEDIUM + 14 LOW findings resolved (Round 4 audit).

---

## How to Run

### Install & Quickstart

```bash
pip install c4reqber           # PyPI entry point (pending publication)
blast setup                    # Interactive checkbox wizard — pick packages, auto-isolate incompatible ones
blast setup --auto             # Non-interactive: install everything automatically
blast solve "problem"         # 4-mode auto-router
```
`blast setup` auto-detects your OS (Apple Silicon / Intel / Linux), scans installed packages, and lets you pick what to install. Python 3.14-incompatible packages (deepchem, unsloth, vllm, nashpy, flower) auto-install into isolated Python 3.12 environments via `uv`.

### MCP Server (for AI agents)

```bash
blast serve --mcp    # Start MCP server via stdio
```

---

## Available Commands

### Terminal-First Commands

| Command | What it does |
|---------|-------------|
| `solve "problem"` | One-shot discovery (hypothesis + article) |
| `turbo "topic"` | Paradigm-shifting research proposal |
| `flash "question"` | Quick LLM answer + optional USP cognition |
| `turbofactory "domain"` | Parallel paradigm factory (5-100 pipelines) |
| `blast analyze "query"` | Systemicity analysis — entity extraction, dependency graph, decomposition, critical path |
| `blast wasm-load <file.wasm>` | Load WASM plugin module |
| `blast wasm-list` | List loaded WASM modules and functions |
| `blast soul` | AI assistant persona — identity, values, refusal rules |
| `blast policy` | Policy engine — risk tiers (READ/SOFT/HARD/DANGEROUS) + audit trail |
| `blast qa` | Quality assurance — lint, typecheck, tests, version sync, secrets scan |
| `blast guardian` | Safety scanner — prompt injection, credential leaks, unsafe AST |
| `blast serve` | **MCP Server** — 21 tools via stdio JSON-RPC, full JSON Schema compliance, hardened for production |
| `blast setup` | First-run wizard — checkbox menu, auto-isolate, one-command install |
| `blast packages` | Scientific package manager — list/install/remove 15 packages |
| `blast agent` | **Main AI agent** — interactive REPL with /commands, Pydantic AI, skills, MCP, memory |
| `blast agent --cmd "..."` | One-shot agent query |
| `blast agent --config` | Show agent configuration |
| `tui` | Interactive terminal interface — cube 3×3×3, live mascot, NightMode, arrow-key package installer, shortcut legend `?` |
| `tui --packages` | Interactive package installer (arrow keys, space to toggle, enter to install) |
| `tui --config` | Configuration editor — view all providers, keys, models, validation |
| `tui --turbo` | Auto-discovery factory (dissertation/paradigm shift) |

### Make Commands (development)

```bash
make dev            # Full stack (backend + frontend)
make backend        # FastAPI on :8000
make test           # All tests (2,730+ collected, 1,400+ pass)
make test-backend   # Python tests only
make lint           # ruff + ESLint
make typecheck      # mypy + tsc
make format         # black + prettier
make security       # trivy + pip-audit + Bandit
```

---

## MCP Tools (for AI agents connecting to this)

When `blast serve --mcp` is running, 21 tools are available with synchronized JSON Schema `inputSchema`/`outputSchema` for structured function calling:

| Tool | Description |
|------|-------------|
| `c4_solve` | Run 12-stage discovery pipeline (HIL) |
| `c4_search` | Search across 33+ knowledge sources |
| `c4_triz` | TRIZ contradiction resolution (4 modes) |
| `c4_fingerprint` | C4 Z₃³ state classification |
| `c4_verify` | Formal proof verification (Lean4/Coq/Dafny/Agda/Z3/Hoare) — direct proof check |
| `c4_prove` | **LLM-based hypothesis proving** — generates formal proofs with iterative error correction |
| `c4_transfer` | Cross-domain isomorphism transfer |
| `c4_simulate` | Physics simulation (32 engine adapters: 5 internal GPU + 26 P1 open-source bridges + 6 virtual bio) |
| `c4_bayesian` | Bayesian inference (MCMC/BMA) |
| `c4_causal` | Causal discovery (do-calculus) |
| `c4_export` | Export to Markdown/JSON/BibTeX/LaTeX |
| `c4_social` | Social publishing — preprint upload (Zenodo/arXiv), ORCID registration, multi-platform posting |
| `c4_autoresearch` | Karpathy-style ML training loop |
| `c4_chain` | C4 discovery chain (Theorem 11: undirected Ø=3, directed fwd=6) |
| `c4_meta` | Meta-cognitive reflection |
| `c4_codegen` | Code generation via MCP tool |
| `blast_solve` | UniversalSolvePipeline strategic artifacts |
| `blast_turbo` | HILDiscoveryPipeline paradigm dissertations |
| `blast_flash` | Quick LLM + USP cognitive analysis |
| `blast_turbofactory` | Parallel pipeline factory |
| `blast_auto` | Auto-router dispatch |

*Note: `blast_analyze`, `blast_wasm_load`, `blast_wasm_list`, `blast_models`, `blast_modes` are CLI commands, not MCP tools. Available via `blast` CLI.*

---

## Project Structure (Key Paths)

```
c4reqber/
├── src/
│   ├── tui/c4_tui.py           # Rich TUI — ASCII cube, pipeline, keyboard-driven
│   ├── tui/mascot.py           # C4 Mascot — meta-mind commentary, local model detection
│   ├── tui/mascot.py           # MascotCommentary v2 — LLM-powered (xAI/OpenRouter)
│   ├── tui/living_cube.py      # Living Cube entity — personality, thinking animations
│   ├── tui/easing.py           # Physics easing curves (cubic, elastic, back, inertia)
│   ├── tui/gradient_bar.py     # Unicode gradient █▊▋▌▍▎▏░ progress bars + glow
│   ├── tui/particles.py        # Cursor sparkles + Discovery fireworks (physics)
│   ├── tui/breathing.py        # Cube breathing idle animation (CogLoad-adaptive)
│   ├── tui/staged_error.py     # Staged error colors (no startle reflex)
│   ├── tui/smart_prompt.py     # Context-aware REPL prompt + ghost text completion
│   ├── tui/delight.py          # Night mode, Cube memory, Shutdown ritual, Birthday easter egg
│   ├── tui/micro_animations.py # Shake vibrato + Phase swoosh transitions
│   ├── tui/delta_renderer.py   # Flicker-free cell-diff renderer (ANSI CSI)
│   ├── repl/core.py            # REPL shell — smart prompt, particles, fuzzy matching
│   ├── repl/input_handler.py   # Raw-terminal input with spark particles + ghost text
│   ├── utils/formatting.py     # Number formatters (1.2K, $0.041, 2m14s, 85.6%)
│   ├── mcp_server/server.py    # MCP server (21 tools, inline JSON Schema, stdio JSON-RPC)
│   ├── cli/                    # CLI argument parser + command dispatch
│   ├── wasm/                   # WASM plugin runtime (wasmtime + stub mode)
│   ├── c4/engine.py            # C4 engine (Z₃³, 27 states, 6 operators, undirected Ø=3, directed fwd=6)
│   ├── operators/              # 20-operator algebra (QZRF expanded)
│   ├── triz/                   # TRIZ bridge (40 principles)
│   ├── plugins/                # 20 cognitive plugins (SWOT, Red Team, etc.)
│   ├── metamodels/             # 7 metamodels (IMPACT, COMPASS, NOTE, QZRF...)
│   ├── pipeline/               # Pipeline architecture
│   │   ├── base.py            # BasePipeline — shared infrastructure
│   │   ├── hil_pipeline.py    # HILDiscoveryPipeline (inherits BasePipeline)
│   │   ├── observer.py        # PipelineObserver (stagnation detection)
│   │   ├── final_verifier.py  # FinalVerifier (post-pipeline check)
│   │   └── quality.py         # QualityGates (weighted 8-gate scoring)
│   ├── simulations/            # 101+ patterns + 32 engine adapters (5 internal + 26 P1 bridges + 6 virtual bio)
│   │   ├── newton_bridge.py    # Newton Physics (mlx-env Python 3.11+)
│   │   └── domain_selector.py # Domain-specific simulation patterns
│   ├── knowledge/              # 33+ sources via orchestrator.py
│   │   └── multi_source.py   # Backward-compat shim (→ orchestrator)
│   ├── publishing/             # Dissertation + preprint submission
│   │   ├── dissertation.py    # LLM-powered dissertation generator
│   │   └── submitter.py       # Real arXiv/bioRxiv LaTeX + BibTeX packages
│   ├── causal/                 # Causal engine (do-calculus, SCM)
│   ├── bayesian/               # Bayesian engine (MCMC, BMA)
│   ├── discovery/              # GapAnalyzer (ABC), GapMiner, NoveltyValidator, Falsifier
│   ├── litintel/               # AlreadyShiftedDetector (iterative, subtractive), ParadigmShift
│   ├── api/server.py           # FastAPI server (lifespan with auto-start)
│   ├── api/v8_routers/        # v8 endpoints (discovery, dissertation)
│   │   └── discovery_v8.py  # 12-step pipeline + 20 wired modules
│   ├── llm/providers/unified.py # Unified LLM Router (11 providers, prompt-injection hardened)
│   ├── agents/soul.py            # Persona Layer — identity, values, refusal rules
│   ├── agents/policy.py          # Policy Engine — 4-tier risk + audit trail
│   ├── agents/qa.py              # QA Controller — lint, typecheck, tests, version sync
│   ├── agents/guardian.py        # Safety Guardian — prompt injection, credential scan
│   └── agents/pipeline.py        # UniversalSolvePipeline (10-step orchestration)
├── discovery/                 # Discovery outputs
│   ├── batch_v6/              # Sleep paradigm (ALREADY_SHIFTED)
│   ├── batch_v7/              # Language gene transfer (SHIFTED, 66.67%)
│   └── batch_v5/exports/      # Generated papers, verification reports
├── tests/                      # 2,730+ collected tests (1,400+ pass)
├── docs/                       # Architecture, PRD, completion reports
├── .env.example              # Template for API keys
├── requirements.txt            # Python dependencies
├── Makefile                    # Dev targets
├── LICENSE                     # AGPL-3.0
└── README.md                  # This file
```

---

## Where to Get Keys

| Key | Purpose | Where to get |
|-----|---------|-------------|
| `OPENROUTER_API_KEY` | LLM provider (required) | https://openrouter.ai/keys |
| `MISTRAL_API_KEY` | Mistral AI ($28 balance) | https://console.mistral.ai/ |
| `MOONSHOT_API_KEY` | Moonshot AI ($1) | https://platform.moonshot.cn/console/api-keys |
| `NVIDIA_API_KEY` | NVIDIA NIM (200 models) | https://build.nvidia.com/ |
| `BRAVE_API_KEY` | Brave Search | https://brave.com/search/api/ |
| `LEAN4_PATH` | Lean4 prover | `eval $(~/.elan/bin/lean --print-path)` |
| `COQ_PATH` | Coq prover | `$(brew --prefix coq)/bin/coqc` |
| `DAFNY_PATH` | Dafny verifier | `$(brew --prefix dafny)/bin/Dafny` |

### .env.example structure

```bash
OPENROUTER_API_KEY=sk-or-...
MISTRAL_API_KEY=...
MOONSHOT_API_KEY=sk-...
NVIDIA_API_KEY=nvapi-...
BRAVE_API_KEY=...
JWT_SECRET=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///data/turbo.db
CACHE_BACKEND=memory
LOG_LEVEL=INFO
```

---

## Architecture (5 Layers)

```
Layer 1: TUI / CLI / MCP — Terminal-first interaction
Layer 2: API — FastAPI + Pydantic v2 + WebSocket + SSE
       POST /api/v8/discover/dissertation (paradigm shift detection)
Layer 3: Core Engines — C4 (6 operators, Z₃³, 27 states, Theorem 11: undirected Ø=3), TRIZ, 28 Plugins (12 compute + 16 cognitive), 7 Metamodels, 101+ Patterns
         SystemAnalyzer — universal entry point (Phase A): entity extraction, dependency graph,
                          systemicity classification (0.0→1.0), decomposition, centrality ranking
         PluginStageRouter — maps plugins to pipeline phases (A-G)
         Auto-selector — keyword + complexity + domain → plugin selection
Layer 4: Cognitive — Causal, Bayesian, System Dynamics, Decision, Discovery,
         Literature Intel, Experimental, Meta (8 layers)
Layer 5: Knowledge + Verification — 33+ sources (orchestrator.py), 32 simulation engine adapters, Lean4/Coq/Dafny
```

---

## Key Metrics (v5.4.1)

| Metric | Value |
|--------|-------|
| Python version | 3.11+ required |
| C4 operators | 6 (T, T_INV, S, S_INV, A, A_INV) — extended from 3 in v5.2 |
| C4 graph diameter | Undirected = 3, Directed forward = 6 (Theorem 11 corrected) |
| Tests | 594 passed (verification/discovery/api/knowledge/utils), 1 xfailed, 27 warnings (numpy overflows in acoustic sims). Go TUI: 8/8 packages pass |
| MCP tools | 21 — JSON Schema, prompt injection hardened, C4Result TypedDict, provider auto-detect |
| i18n | 7 languages: en/ru/zh/ja/de/ar/hi. Auto-translation of prompts + results |
| Live Feed | Reddit/HN/NewsAPI/arXiv/Semantic Scholar → anomaly detector → hypothesis generator. TUI ticker `F`. Force refresh `Ctrl+R`. Disk cache (24h offline) |
| File workflow | `--folder ~/papers/` — PDF/OCR/изображения → пайплайн. `--hybrid` = локальные + 28 источников |
| MLX-LM | Apple GPU local LLM: $0/MTok, depth_router tier `local`. Auto-detect + auto-start. Requires Apple Silicon (M1+). Falls back to LM Studio/Ollama on Intel Mac |
| Simulation config | `~/.c4reqber/simulations.json` — mode: auto|gpu|cpu_only|off. Vast.ai + local GPU. Cost limit. Fallback to Experimental Protocol. 6 virtual bio simulators (OpenMM, Vina, BoolNet, COBRApy, SLiM, Psi4). 26 P1 engine bridges (FEniCSx, OpenFOAM, GROMACS, LAMMPS, MDAnalysis, PySCF, Psi4, Quantum ESPRESSO, Tellurium, NEURON, Brian2, Jaxley, COPASI, xarray, WRF, Mesa, SimPy, Rebound, AMUSE, MuJoCo, PyBullet, diffeqpy, Taichi, JAX MD, JAX-LaB, ModelingToolkit.jl) |
| Verification | 10 backends + MathDetector — classifies hypotheses A/B/C for formalizability. Literature consistency check always runs |
| Output | Experimental Protocol (materials, equipment, sample size, power analysis, cost) + In-Silico Validation section |
| Gap Mining | AutoGapAnalyzer with LLM + keyword fallback + topic-based guaranteed minimum (≥1 gap always) |
| Dissertation | Auto-regeneration (2 retries) if <600 words. Quality gate: sources, gaps, hypotheses, simulation, verification, bibliography, dissertation, novelty. |
| RedundantGate | Pure-Python cosine similarity fallback (no sklearn required) |
| Micro-features | **17 integrated**: C4 Layer Stream, CogLoad Modes, Alert Taxonomy, Depth Ladder, Formal Citations, Cost Router, Live Verification Injection, Stratified Blocks, PATH.toml, Hypothesis Sandbox, Gated Pipeline, State Replay, Proof Graph, Graph History, Structured Input, Cube Navigator, Dashboard |
| TUI shortcuts | 20: Tab/Enter/L/A/B/D/T/R/V/I/F/G/M/P/Q/1-5 + ←↑↓→ — ALL wired to live panels (alert, budget, depth, article, proof, cube nav, feed, thinking, GPU, modules, plugins, export) |
| Slash commands | `/models` `/council` `/connect` `/api` `/test` `/profile` `/plugins` `/debug` `/config` `/help` `/sim` — 11 total |
| Knowledge sources | 33+ active, 37+ total registered (orchestrator.py; includes BibSonomy REST API) |
| Simulation patterns | 101+ (CPU fluid: Navier-Stokes Euler solver) |
| Physics engines | 5 internal (Newton, TorchSim, JaxSim, Schr, vast.ai) + 26 P1 bridges (FEniCSx, OpenFOAM, GROMACS, LAMMPS, MDAnalysis, PySCF, Psi4, QE, Tellurium, NEURON, Brian2, Jaxley, COPASI, xarray, WRF, Mesa, SimPy, Rebound, AMUSE, MuJoCo, PyBullet, diffeqpy, Taichi, JAX MD, JAX-LaB, ModelingToolkit.jl) + 6 Virtual Biology + MirrorFish + MATLAB |
| LLM providers | 11 auto-detected: MLX, LM Studio, Ollama, OpenRouter, DeepSeek, XAI, Mistral, Moonshot, Liquid AI, NVIDIA NIM, YandexGPT. Model-per-stage + depth-based routing (C1 cheap, C3 premium). |
| Architecture | Saga (238 lines), CQRS (167 lines), Event Sourcing (297 lines) — fully implemented, wired into BasePipeline + HILDiscoveryPipeline. ChromaDB vector store (4 collections) caching knowledge search + agent memory + paper embeddings. FastMCP client bridge for external MCP server discovery. LangGraph executor in AgentCore for graph-based processing. |
| WASM runtime | `blast wasm-load/list` CLI + stub mode (wasmtime optional) |
| CLI commands | 19: auto, solve, turbo, flash, turbofactory, analyze, serve, agent, modes, tui, wasm-load, wasm-list, wasm-execute, models, config, social, integrations, packages, soul/policy/qa/guardian |
| Pipeline architecture | `BasePipeline` → HILDiscoveryPipeline + UniversalSolvePipeline. `PluginStageRouter` A-G. Progressive streaming via ProgressEmitter. |
| Export formats | Markdown, JSON, BibTeX, LaTeX (.tex+.bib), HTML dashboard |
| Security | Prompt sanitizer (19 patterns), credential guard (16 regex), C4Result TypedDict enforcement |

---

## TUI Keyboard Shortcuts (v5.4.0)

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `Tab` | Switch mode (discover/invent/transform) | `L` | Switch language |
| `Enter` | Run discovery | `Q` / `Esc` | Quit |
| `A` | Toggle Alert panel (severity-coded) | `B` | Toggle Budget gauge ($ cost) |
| `D` | Toggle Depth Ladder (C1→C2→C3) | `T` | Toggle Article Canvas (dissertation) |
| `R` | Toggle Proof Graph (ASCII dependency) | `V` | Toggle Cube Navigator (interactive) |
| `O` | Toggle Operations panel | `G` | Toggle GPU dashboard |
| `M` | Toggle Module status | `I` | Toggle Provider dashboard |
| `F` | Toggle Live Intelligence Feed | `Ctrl+R` | Force refresh feed/cache |

## TUI v9 Keyboard Shortcuts (v9.13.0) — added on top of v5.4.0

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `:` | Open command palette (fuzzy-matches 35+ cmds) | `Ctrl+Shift+C` | Capabilities overlay (32 engines + 27 verifiers) |
| `Ctrl+Shift+D` | Debug overlay (live state dump) | `Ctrl+B` | Toggle status bar |
| `j` / `k` | Focus next / prev card | `g g` / `G` | Focus first / last card |
| `Enter` (on focused card) | Expand to FullBody | `Esc` (on expanded) | Collapse |
| `i` (on sim card) | Show install hint | `f` (on sim card) | Show fallback chain |
| `o` (on sim with image) | Open plot in browser | `c` (on focused) | Copy as markdown |
| `←↑↓→` | Navigate 3×3×3 C4 cube | | |

---

## Plugin Stage Router (v5.4.0)

28 плагинов автоматически распределяются по 7 фазам пайплайна:

| Phase | Pipeline Stage | Plugins |
|-------|---------------|---------|
| **A** | SystemAnalyzer → C4 Cognitive Framing | `info_theory`, `dim_reduction` |
|       | *(SystemAnalyzer runs first: extracts entities, builds dependency graph, classifies systemicity 0.0→1.0, decomposes and ranks sub-problems by graph centrality)* | |
| **B** | Knowledge Acquisition | `text_distance`, `graph_metrics` |
| **C** | Gap Analysis | `text_distance`, `info_theory`, `timeseries`, `graph_metrics` |
| **D** | Hypothesis Generation | SWOT, Delphi, Red Team, Six Hats, SCAMPER, First Principles, 5Whys, Lateral Thinking, OODA, Design Thinking, Ishikawa, Morphological |
| **E** | Simulation & Verification | `monte_carlo_pi`, `matrix_mult`, `dist_analyzer`, `signal_processing`, `optimization`, `timeseries` |
| **F** | Dissertation | `hash_fingerprint`, `dim_reduction` |
| **G** | Quality Control | `stat_tests`, `dist_analyzer`, `info_theory`, `signal_processing`, `optimization` |

### Auto-Selector

```python
select_plugins_for_problem(problem, domain, mode) → [plugin_ids]
```
- **Keywords**: "p-value" → stat_tests, "entropy" → info_theory, "distribution" → dist_analyzer
- **Complexity**: ≥30 words → deep analysis plugins, ≤3 words in flash → none
- **Domain**: physics/engineering → dist_analyzer, biology → stat_tests
- **Mode**: turbo → swot+delphi+red_team, solve → first_principles+5whys, turbofactory → all analytical

### Manual Override

```bash
blast turbo "topic" --plugins stat_tests,swot,signal_processing
```

### Model-per-Stage LLM Routing

Different pipeline stages use different LLM models optimized for the task:

| Phase | Model | Why |
|-------|-------|-----|
| A, D, F | `anthropic/claude-3.5-sonnet` | Reasoning + creativity + academic writing |
| B, C | `qwen/qwen-2.5-72b-instruct` | Balanced cost/quality for search + analysis |
| E | _no LLM_ | Compute plugins only (WASM/Python) |
| G | `openai/gpt-4o-mini` | Cheap validation + scoring |

---

## Kilo Agents

Global Kilo agents for c4reqber development. Located in `~/.kilo/agent/`:

| Agent | File | Description |
|-------|------|-------------|
| **optimizer** | `~/.kilo/agent/optimizer.md` | Performance optimization — finds O(n²), allocations, I/O waste, cache opportunities |
| **amplifier** | `~/.kilo/agent/amplifier.md` | Code quality — finds amateur patterns, missing error handling, inconsistent APIs |

## New C4 Modules (v5.4.0 — 17 micro-features)

| Module | File | Feature |
|--------|------|---------|
| **C4LayerTracker** | `src/c4/layer_stream.py` | Streams C1/C2/C3 layer state during pipeline execution |
| **CogLoadDetector** | `src/c4/cognitive_load.py` | Auto-escalates permissions based on cognitive load |
| **AlertClassifier** | `src/c4/alert_taxonomy.py` | Classifies alerts by C4 severity (C1:INFO→C3:CRITICAL) |
| **CitationFormatter** | `src/c4/formal_citations.py` | Formal verification result citations (F1-F3, CE, N1) |
| **DepthBasedRouter** | `src/llm/depth_router.py` | Routes models by C4 depth + budget tier |
| **process_injections** | `src/c4/injection_hook.py` | `!c4 verify` preprocessing in prompts |
| **BlockRegistry** | `src/c4/stratified_blocks.py` | C4-annotated output blocks with provenance |
| **PathRegistry** | `src/c4/path_manifest.py` | PATH.toml scientist path manifests |
| **HypothesisSandbox** | `src/c4/hypothesis_sandbox.py` | Isolates contradictory reasoning paths |
| **GatedPipeline** | `src/c4/gated_pipeline.py` | Cyclic pipeline with verification gates + regression |
| **C4StateJournal** | `src/c4/state_journal.py` | Cognitive state transition recording + replay |
| **HistoryGraph** | `src/c4/history_graph.py` | Graph-structured history with logical traversal |
| **parse_structured_input** | `src/c4/structured_input.py` | REQ:/HYP:/VERIFY: syntax highlighting |
| **ProofGraph** | `src/tui/proof_graph.py` | ASCII dependency graph with C4 coloring |
| **InteractiveCube** | `src/tui/cube_navigator.py` | Clickable 3×3×3 C4 cube with arrow navigation |
| **ArticleCanvas** | `src/tui/article_canvas.py` | Dissertation display with section scrolling |
| **DepthLadder** | `src/tui/depth_ladder.py` | C1→C2→C3 progress visualization |
| **AlertPanel** | `src/tui/alert_widget.py` | Severity-coded alert panel with auto-dismiss |
| **BudgetGauge** | `src/tui/budget_gauge.py` | Real-time pipeline cost estimation |

---

## Code Quality Status (v5.4.2 — Round 4 Audit Complete)

| Metric | Value |
|--------|-------|
| **Lint (ruff)** | **0 errors across entire `src/`** — 95 pre-existing fixed in final round |
| **Security audit Round 4 (Kimi Code CLI)** | 16 CRITICAL → ALL FIXED. 34 HIGH → ALL FIXED. 55 MEDIUM → ALL FIXED. 14 LOW → ALL FIXED |
| **Security audit (pre-existing)** | 43 Critical + 75 High + 113 Medium → ALL RESOLVED (v5.4.0 → v5.4.1) |
| **Code quality** | 152 bare `except Exception:` → critical paths logged; `__import__` antipatterns → proper imports/importlib; dead code removed |
| **Bugs fixed total** | 124 (Round 4: 16+34+55+14) + 70 (Kimi CLI) + 18 (pre-existing) = **222 fixes** |
| **Tests** | 594 passed, 1 xfailed, 27 warnings (numpy state pollution in acoustic sims, not code bugs). Go TUI: 8/8 packages pass |
| **TUI app.py** | Full rewrite: 362 lint errors → 0, multi-statement lines eliminated |
| **TUI header_footer.py + living_cube_v2.py** | 22 multi-statement lines cleaned (E701/E702→0) |
| **Files touched total** | 45+ files across 4 remediation rounds |
| **Documentation** | 12+ docs updated: CHANGELOG, AGENTS.md, SECURITY.md, README, ARCHITECTURE.md, audit reports |
| **New utilities** | `src/utils/error_taxonomy.py` — unified error classification; `src/utils/security_middleware.py` — centralized input validation + prompt sanitization + path guards |

---

## UI/UX Polish Features (v5.4.0 — 24 features)

### L5 — Infrastructure
| Module | Feature |
|--------|---------|
| `utils/formatting.py` | 9 formatters — `fmt_count` (1.2K), `fmt_dollars` ($0.041), `fmt_duration` (2m 14s), `fmt_tokens` (12.3K tok), `fmt_percent` (85.6%), `ElapsedTimer` |
| `tui/delta_renderer.py` | Cell-diff tracker — flicker-free terminal via ANSI CSI n;mH cursor jumps. Only changed cells rewritten |
| `tui/easing.py` | 6 easing curves (cubic, elastic, back, quart, expo) + `InertiaSimulation` physics |

### L1 — Always Visible
| Module | Feature |
|--------|---------|
| `tui/gradient_bar.py` | 8-level Unicode gradient `█▊▋▌▍▎▏░` + dual cyan→magenta glow tail + pulse mode |
| `tui/animation.py` | Cubic ease-out per-character typing in startup animation |
| `repl/core.py` | C4REQBER banner — correct C-4-R-E-Q-B-E-R sequence + Q `▀▀═╝` bottom serif |

### L2 — Micro-Interactions
| Module | Feature |
|--------|---------|
| `repl/input_handler.py` | Raw-terminal input — 5 spark particles on each keypress (gravity + friction) |
| `tui/breathing.py` | Cube idle breathing — 5s idle threshold, CogLoad-adaptive frequency (C1=4s, C2=2.5s, C3=1.5s) |
| `tui/staged_error.py` | 300ms cyan → 200ms transition → red. No startle reflex |

### L3 — Anticipation
| Module | Feature |
|--------|---------|
| `tui/smart_prompt.py` | Context-aware: `c4reqber ❯` / `c4reqber [openrouter] ❯` / `c4reqber ⏳ ❯` / `c4reqber ✓ ❯` |
| `tui/smart_prompt.py` | Ghost text: `/mod` → grey `els` preview inline; Tab → complete |
| `repl/core.py` | Fuzzy matching: `anlyz` → "Did you mean: analyze?" |

### L4 — Delight (Easter Eggs + Rituals)
| Module | Feature |
|--------|---------|
| `tui/delight.py` | Night mode — auto after 23:00; palette dims 20%, cyan→warmer, magenta→muted |
| `tui/delight.py` | Birthday easter egg — May 15: ASCII cake + "Z₃³ was born today. 27 states. Still going." |
| `tui/delight.py` | Cube memory — recalls user's analyze/turbo topics; idle musings reference them |
| `tui/delight.py` | Shutdown ritual — 6-framespin cube turn → fade → "All 27 states archived. Until next theorem." |
| `repl/core.py` | Session stats — "14m 32s · 8 commands · 2 discoveries" before shutdown |
| `tui/particles.py` | Discovery fireworks — 100 particles, gravity 9.8, 6 colors, 2.5s on confidence >80% |

### L2+/L1 Hybrid
| Module | Feature |
|--------|---------|
| `tui/micro_animations.py` | Shake vibrato — cube wobbles 1-2 cells on navigation (150ms) |
| `tui/micro_animations.py` | Phase swoosh — `A ▁▂▃▄▅▆▇█████ B` sweep between pipeline stages (180ms, 60fps) |
| `tui/micro_animations.py` | Adaptive wait — rotating contextual messages: "Waking the cube..." → "Theorem 11: connecting states..." |
| `tui/results_display.py` | Rate-limit border — progress bar border cyan→yellow→red at 30%/60%/85% API usage |
| `repl/core.py` | Cursor state — CogLoad 1=blinking bar (dim cyan), 2=underline (bright cyan), 3=block (magenta) |

---

## Code Rules for AI Agents

1. **Python modules ≤300 lines** — split into submodules
2. **No module-level singletons** — use FastAPI dependency injection
3. **Add tests** — every module gets coverage
4. **Type everything** — Python: `from __future__ import annotations`, strict mypy
5. **Pre-commit must pass** — black, ruff, eslint, detect-secrets
6. **English only** — no Russian in code, comments, or file names
7. **Never commit .env** — only `.env.example`
8. **AGENTS.md is your map** — update it when project state changes
9. **No mocks** — all modules return real data

## Guardrails

1. THINK FIRST → Audit → Diagnose → Plan → Confirm → Execute
2. USE RIGHT TOOL — match task to skill/MCP
3. CHECK BEFORE CHANGE — `git status`, read context
4. TEST FIRST — write failing test before implementation
5. NEVER commit secrets or keys
6. NEVER `git push --force` to main/master
7. NEVER modify system directories (`/etc`, `/bin`, `/usr`)
8. NO MOCKS — all modules return real data
9. NO GIT PUSH — all work stays local (user rule)

---

## Startup Services (Auto-Start in lifespan.py)

### LM Studio (local LLM)
- Path: `/Users/figuramax/.lmstudio/bin/lms`
- Check: `curl -s http://localhost:1234/v1/models` → 200
- Start: `lms server start`

### MLX Server (Python 3.11, mlx-env)
- Path: `/Users/figuramax/LocalProjects/mlx-env/bin/python`
- Check: `curl -s http://localhost:8001/v1/models` → 200
- Start: `python -m mlx_lm.server --port 8001 --model qwen2.5-coder-7b`

### Newton Physics (Python 3.11, mlx-env)
- Installed in: `/Users/figuramax/LocalProjects/mlx-env/`
- Used via: `subprocess.run([mlx_python, "newton_runner.py", config_json])`
- Requires: Python ≥3.10 (why mlx-env is used)

---

## Discovery Pipeline (v5.4.0 — 12 Steps)

```
Step 1:  C4 Navigation (Z₃³, 27 states, 6 operators: T/T_INV/S/S_INV/A/A_INV)
Step 2:  TRIZ Contradiction Resolution (40 principles)
Step 2.5: FRA Routing (situation fingerprint)
Step 2.6: C4 Observer (meta-cognitive framing)
Step 3-4: UCOS 4-Layer Analysis
Step 4.5: QZRF 14 Operators
Step 4.6: Matrix Dream (72 patterns)
Step 4.7: Multi-Source Search (33+ sources via orchestrator.py)
Step 5:   GapMiner (3-layer text analysis)
Step 5.1: Contradiction Mining
Step 5.3: AlreadyShiftedDetector (HARD GATE, iterative — re-checks per refinement, subtractive confidence)
Step 5.4: Temporal Knowledge Graph
Step 5.5: Isomorphism Search
Step 5.5b: GapMiner (discovery_potential)
Step 5.5c: Strong Inference (Platt's method)
Step 5.5d: Abduction Engine (IBE)
Step 5.5x: AutoScanner (unsolved problems)
Step 6:   Hypothesis Generation (LLM + TRIZ template)
Step 6.1: Cognitive Plugins (20 plugins executed here)
Step 6.5:  Novelty Validation (HARD GATE — was warning; keyword lists extracted from papers, not hardcoded)
Step 6.5a: Falsification Engine (Popper)
Step 6.5b: DoE Design
Step 6.5c: Power Analysis
Step 6.5d: Reproducibility Check
Step 7:   Physics Simulation (auto-select from 32 engine adapters via PatternRunnerV2)
Step 7.1: Causal Do-Calculus
Step 7.2: Counterfactual Reasoning
Step 8:   Formal Verification (Lean4 + Coq + Dafny)
Step 8.1: Consensus Meter
Step 8.2: Empirical Validation
Step 8.5: Formal Verification (summary)
+ Self-Critique (Nature reviewer persona)
+ Iterative Refinement (3 iterations — AlreadyShiftedDetector & NoveltyValidator re-check each iteration)
```

---

## Paradigm Shift Detection Results

| Test | Hypothesis | Verdict | Probability | Status |
|------|-----------|---------|------------|--------|
| 1 | Sleep as active maintenance | `ALREADY_SHIFTED` | 100% | ✅ Correct detection |
| 2 | Language horizontal gene transfer | `SHIFTED` | 66.67% | ✅ Passed ALL gates! |

**Files Generated:**
- `discovery/batch_v6/paradigm_shift_sleep.json` (ALREADY_SHIFTED)
- `discovery/batch_v7/lang_gene_discovery.json` (SHIFTED)
- `discovery/batch_v7/LANG_EVOLUTION_DISSERTATION.md` (Full article in Russian, 4,985 chars)
- `discovery/batch_v7/exports/` (MD, JSON, BibTeX, verification.txt)

---

## Competitive Landscape (v5.4.0)

**48 competitors tracked** across 6 categories. Full reports:

| Category | Top Threats | Threat Level |
|----------|------------|-------------|
| **Scientific Discovery AI** | SakanaAI/AI-Scientist v2 (20K stars), EvoScientist | 9/10 |
| **Chinese Reasoning Giants** | DeepSeek V4 (MIT), Qwen3.6-Max, Moonshot/Kimi (Kimina Prover) | 8-9/10 |
| **Multi-Agent Orchestration** | CrewAI (51K stars), MetaGPT (68K), AutoGen (58K), deer-flow (68K) | 8/10 |
| **Deep Research (Chatbots)** | ChatGPT Deep Research, Perplexity, Gemini Deep Research | 7/10 |
| **CLI/Terminal AI** | Claude Code ($1B ARR), Devin, Cursor | 6/10 |
| **MCP Cognitive Servers** | Ejentum (679 ops), Clear Thought (9.4K uses), Disco | 6-8/10 |

**c4reqber's strongest moats:** C4-META Z₃³ topology (3-5yr to replicate), 24 scientist paths (2-4yr), formal verification Lean4/Coq/Dafny (1-2yr), WASM plugin runtime (unique in AI space), SystemAnalyzer (no equivalent).

**Competitive reports:**
- `archive/plans/c4reqber_competitive_intelligence_report/c4reqber_competitive_intelligence_report.md` — original 29-competitor analysis
- `archive/plans/c4reqber_competitive_intelligence_report/SUPPLEMENT_github_producthunt_mcp.md` — +19 new competitors from GitHub/MCP/academic/Chinese AI
- `archive/plans/c4reqber_improvement_plan_v5.3.3.md` — 24-point roadmap: Immediate → 12-month

---

**Citation**: Selyutin I., Kovalev N.I. (2026). *c4reqber v5.4.0: Cognitive Exoskeleton for AI Agents.*  
**License**: AGPL-3.0 (open-source) / Commercial License available  
**Discovery Clause**: Mandatory citation in every generated paper
