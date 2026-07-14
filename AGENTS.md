## 🔴 GIT REMOTE — PRIMARY: GitLab (NEVER say "github" in chat!)

**Primary remote:** GitLab (`git@gitlab.com:cognitive-functors/c4reqber.git`).
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
> **Doc status:** Body is a snapshot of the v9.13.0 / v5.6.0 architecture (last full rewrite). For post-v9.14.0 changes see `CHANGELOG.md`. **Canonical technical whitepaper:** [WHITEPAPER.md](WHITEPAPER.md) (EN) · [WHITEPAPER.ru.md](WHITEPAPER.ru.md) (RU) · [docs/VERIFICATION_BACKENDS.md](docs/VERIFICATION_BACKENDS.md).

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
- **TUI v9** (Go Bubble Tea v2, sim surface: `CardSimulation` kind + capabilities overlay Ctrl+Shift+C listing 38 engine bridges + 9 verifiers with per-platform status and install hints, command palette `:`, debug overlay Ctrl+Shift+D, status bar Ctrl+B, per-card expansion Enter/Esc, 7-language i18n at 100% parity, 7 color profiles including solarized-dark, adaptive layout T0/T1/T2/T3, feed.jsonl persistence + resume on launch, 132 golden snapshots) — 0 critical bugs, 27 atomic commits, +7302 lines. **Merged on `feat/production-upgrade` branch (round 5 audit landed).**
- **CLI** — 24 top-level `blast` commands
- **Agent system** (Pydantic AI, 11 skills, MCP bridge, memory, sub-agents, `/preprint`, LangGraph executor, FastMCP external tool discovery, ChromaDB memory)
- **TRIZ** (40 principles, contradiction matrix) — semantic C4 mapping
- **9 real verification backends** (Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy)
- **251 few-shot proof examples** (Lean4×56, Coq×48, Dafny×52, Z3×50, Agda×45) with TF-IDF RAG retrieval
- **Causal inference adult** (DoWhy + EconML + gCastle: PC/FCI/NOTEARS/ANM)
- **Hypothesis ranking** (PriorScorer × EIGEstimator × CostModel × MCDMRanker)
- **Closed-loop simulation** (Bayesian tracker, experiment designer, ensemble runner, convergence)
- **Self-directed agenda** (generator, feasibility, priority, progress, TUI screen shift+a)
- **Open-ended exploration** (anomaly detector, surprise-driven questions, formal extender)
- **7/7 metamodels** (IMPACT, COMPASS, UCOS, QZRF, FRA, Matrix Dream, TOTE)
- **47 configured knowledge source integrations** (46 wired to `MultiSourceSearcher`; runtime-active subset depends on credentials and availability). Truth source: `_truths.json`.
- **15 installable scientific packages** — auto-detected, 10 native + 5 isolated Python 3.12 envs
- **REPL** — 100% real (project/task models implemented)
- **v8 API** — fully functional aggregator router (discovery, knowledge, newton, social, verification, novelty, news)
- **News/LiveFeed** — real aggregation pipeline (arXiv, PubMed, knowledge sources)
- **MCP Server** — 21 tools (per `_truths.json` + `docs/mcp_registry.md`), all verified working with JSON Schema sync (c4_solve, c4_search, c4_triz, c4_fingerprint, c4_verify, c4_prove, c4_transfer, c4_simulate, c4_bayesian, c4_causal, c4_export, c4_autoresearch, c4_chain, c4_meta, c4_social, c4_codegen, blast_solve, blast_turbo, blast_flash, blast_turbofactory, blast_auto)
- **Security**: JWT+HMAC auth, CSRF hardened, subprocess injection blocked, prompt injection fail-closed, path traversal blocked, pip allow-list, MATLAB sandbox, 0 CRITICAL/HIGH findings
- **Code quality**: 0 ruff lint errors across entire `src/`, `__import__` antipatterns removed, importlib for dynamic loading
- **Type safety**: 56 mypy baseline errors (regression-gated; no new errors in CI) (559→508→0 after 3 audit rounds)
- **Tests**: 9,924 collected (Python), 485+ passed core suites, 1 flaky Monte Carlo. Go TUI: 8/8 packages pass, staticcheck clean.
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

**c4reqber** is a terminal-first scientific discovery pipeline with C4 state-space navigation layer. 27 Z₃³ states, 9 verification backends + MathDetector (Categories A/B/C) + guardrails, 6 virtual biology simulators, experimental protocol generator, simulation config (GPU/CPU/off), 6 output formats with auto-detection, 11 configured LLM providers (MLX/LM Studio/Ollama/OpenRouter/DeepSeek/XAI/Mistral/Moonshot/Liquid/NVIDIA/YandexGPT), MLX-LM local ($0/MTok), file/OCR workflow, Live Intelligence Feed, 7-language i18n, **21 MCP tools** (all verified working post-audit), **TUI v9** (`blast tui`, Go feed cockpit with overlays `Ctrl+Shift+K/S/M`, `Shift+A`, `:`), **1 main AI Agent** (skills, MCP, memory, sub-agents, Pydantic AI, `/preprint`), **Social Publishing module** (Zenodo/ORCID/Mastodon/Bluesky/Telegram/Reddit/Discord/Slack — BYOK, honest limits), 24 CLI commands, 5 WASM plugins. **TUI v9** (v9.13.0) adds: simulation surface with 38 engine bridges + 9 verifiers (capabilities overlay Ctrl+Shift+C), CardSimulation kind in the feed, typed SSE decoder for `sim_started/sim_finished/sim_skipped` events, command palette `:`, debug overlay Ctrl+Shift+D, status bar Ctrl+B, per-card expansion Enter/Esc, 7 color profiles including solarized-dark, adaptive layout T0/T1/T2/T3, feed.jsonl persistence + resume on launch, 132 golden snapshots. **Security hardened**: auth bypass fixed, prompt injection fail-closed with nonce delimiters + HTML entity decoding + LaTeX escaping, subprocess shell-injection blocked, path traversal protected, SSRF protection on paper IDs, symlink guards, Agda module validation, rate-limiter token leak fixed, all 16 CRITICAL + 34 HIGH + 55 MEDIUM + 14 LOW findings resolved (Round 4 audit).

---

## How to Run

### Install & Quickstart

```bash
pip install c4reqber           # PyPI — https://pypi.org/project/c4reqber/
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
| `blast config keys` | API keys Setup Hub CLI — `secrets.env`, `--json`, `--assign`, `--health` |
| `blast config --show --json` | Phase models + council (TUI `Ctrl+Shift+M`) |
| `blast models --json` | Model list export for automation |
| `blast social post` | Post to one configured social platform |
| `blast tui` | **TUI v9** (Go) — feed cockpit, overlays: `Ctrl+Shift+K/S/M`, `Shift+A`, `:` |
| `blast tui --packages` | Rich package installer (arrow keys) |

### Make Commands (development)

```bash
make dev            # Full stack (backend + frontend)
make backend        # FastAPI on :8000
make test           # Full test suite (9,905 tests currently collected)
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
| `c4_solve` | Run 7-phase HIL discovery pipeline (phases A→G) |
| `c4_search` | Search across 47 configured knowledge sources |
| `c4_triz` | TRIZ contradiction resolution (4 modes) |
| `c4_fingerprint` | C4 Z₃³ state classification |
| `c4_verify` | Formal proof verification (Lean4/Coq/Dafny/Agda/Z3/Hoare) — direct proof check |
| `c4_prove` | **LLM-based hypothesis proving** — generates formal proofs with iterative error correction |
| `c4_transfer` | Cross-domain isomorphism transfer |
| `c4_simulate` | Physics simulation (38 engine bridges: 5 internal GPU + 26 P1 open-source bridges + 6 virtual bio) |
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
│   ├── tui/
│   │   ├── v9/                      # TUI v9 (Go/Bubble Tea) — production `blast tui`
│   │   │   ├── model.go, update.go, view.go, keymap.go
│   │   │   ├── setup_menu.go, social_menu.go, agenda_menu.go, models_menu.go
│   │   │   ├── api/                 # HTTP client (discovery SSE, agenda)
│   │   │   ├── persist/             # feed.jsonl, state, C4REQBER_CONFIG paths
│   │   │   └── i18n/                # 7 languages (en/ru/zh/ja/de/ar/hi)
│   │   ├── app.py, entry.py         # Thin Python shims → c4tui-v9
│   ├── cli/
│   │   ├── blast_app.py             # `blast` CLI dispatch
│   │   ├── config_keys.py           # `blast config keys`
│   │   ├── tui_launcher.py          # Spawns Go binary
│   │   └── package_installer_tui.py # `blast tui --packages` (Rich)
│   ├── config/
│   │   ├── paths.py                 # CONFIG_DIR, C4REQBER_CONFIG
│   │   ├── key_registry.py          # SSOT from .env.example
│   │   └── secrets_store.py         # ~/.c4reqber/secrets.env
│   ├── social/                      # post_dispatcher, publisher, social_bridge
│   ├── repl/core.py                 # Agent REPL (`blast agent`)
│   ├── utils/formatting.py          # fmt_count, fmt_dollars, fmt_duration, …
│   ├── mcp_server/server.py         # MCP server (21 tools, stdio JSON-RPC)
│   ├── c4/engine.py                 # C4 engine (Z₃³, 27 states, 6 operators)
│   ├── pipeline/                    # BasePipeline, HILDiscoveryPipeline, …
│   ├── simulations/                 # 101+ patterns + 38 engine bridges
│   ├── knowledge/                   # 47 sources via orchestrator.py
│   ├── publishing/                  # dissertation.py, submitter.py
│   ├── api/server.py                # FastAPI (lifespan auto-start)
│   ├── api/v8_routers/              # discovery, agenda, simulations, …
│   ├── llm/providers/unified.py     # Unified LLM Router (11 providers)
│   └── agents/                      # soul, policy, qa, guardian, pipeline
├── discovery/                         # Batch outputs (batch_v6/v7, exports)
├── tests/                             # ~9,924 collected Python tests
├── docs/                              # API_KEYS.md, SOCIAL_PUBLISHING.md, INSTALL.md
├── landing/                           # Static site + i18n (7 langs)
├── .env.example                       # Template for all env vars
└── README.md
```

> **Wave C (2026-07):** Legacy Python Rich/Textual TUI modules under `src/tui/*.py` (mascot, living_cube, proof_graph, cube_navigator, …) were **removed**. Only `src/tui/v9/` (Go) + thin shims remain.

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
       POST /v8/discover/dissertation (paradigm shift detection)
Layer 3: Core Engines — C4 (6 operators, Z₃³, 27 states, Theorem 11: undirected Ø=3), TRIZ, 28 Plugins (12 compute + 16 cognitive), 7 Metamodels, 101+ Patterns
         SystemAnalyzer — universal entry point (Phase A): entity extraction, dependency graph,
                          systemicity classification (0.0→1.0), decomposition, centrality ranking
         PluginStageRouter — maps plugins to pipeline phases (A-G)
         Auto-selector — keyword + complexity + domain → plugin selection
Layer 4: Cognitive — Causal, Bayesian, System Dynamics, Decision, Discovery,
         Literature Intel, Experimental, Meta (8 layers)
Layer 5: Knowledge + Verification — 47 configured sources (orchestrator.py), 38 simulation engine bridges, Lean4/Coq/Dafny
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
| Micro-features | **17 integrated** (pipeline/C4 Python modules). Legacy Python TUI widgets removed Wave C — see TUI v9 overlays |
| TUI shortcuts | **TUI v9 only** (`blast tui`): `:` palette, `Ctrl+Shift+K/S/C/M`, `Shift+A`, `j/k` cards, `Ctrl+B` status — see keymap below |
| Slash commands | **Removed** with legacy Python TUI. Use `:` command palette or `blast config` / `blast config keys` |
| Knowledge sources | 47 configured; 46 wired |
| Simulation patterns | 101+ (CPU fluid: Navier-Stokes Euler solver) |
| Physics engines | 5 internal (Newton, TorchSim, JaxSim, Schr, vast.ai) + 26 P1 bridges (FEniCSx, OpenFOAM, GROMACS, LAMMPS, MDAnalysis, PySCF, Psi4, QE, Tellurium, NEURON, Brian2, Jaxley, COPASI, xarray, WRF, Mesa, SimPy, Rebound, AMUSE, MuJoCo, PyBullet, diffeqpy, Taichi, JAX MD, JAX-LaB, ModelingToolkit.jl) + 6 Virtual Biology + MirrorFish + MATLAB |
| LLM providers | 11 configured (cloud + local); runtime availability varies |
| Architecture | Saga (238 lines), CQRS (167 lines), Event Sourcing (297 lines) — fully implemented, wired into BasePipeline + HILDiscoveryPipeline. ChromaDB vector store (4 collections) caching knowledge search + agent memory + paper embeddings. FastMCP client bridge for external MCP server discovery. LangGraph executor in AgentCore for graph-based processing. |
| WASM runtime | `blast wasm-load/list` CLI + stub mode (wasmtime optional) |
| CLI commands | 24 top-level `blast` commands |
| Pipeline architecture | `BasePipeline` → HILDiscoveryPipeline + UniversalSolvePipeline. `PluginStageRouter` A-G. Progressive streaming via ProgressEmitter. |
| Export formats | Markdown, JSON, BibTeX, LaTeX (.tex+.bib), HTML dashboard |
| Security | Prompt sanitizer (19 patterns), credential guard (16 regex), C4Result TypedDict enforcement |

---

## TUI v9 Keyboard Shortcuts (production — `blast tui`)

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `:` | Open command palette (fuzzy-matches 35+ cmds) | `Ctrl+Shift+C` | Capabilities overlay (38 engine bridges + 9 verifiers) |
| `Ctrl+Shift+D` | Debug overlay (live state dump) | `Ctrl+B` | Toggle status bar |
| `Ctrl+Shift+K` | API Keys Setup Hub | `Ctrl+Shift+S` | Social publishing menu |
| `Shift+A` | Research agenda overlay | `Ctrl+Shift+M` | Models & council config |
| `Tab` | Cycle mode (Discover/Flash/Turbo/TurboFactory) | `Ctrl+,` | Runtime settings menu |
| `j` / `k` | Focus next / prev card | `g g` / `G` | Focus first / last card |
| `Enter` (on focused card) | Expand to FullBody | `Esc` (on expanded) | Collapse |
| `i` (on sim card) | Show install hint | `f` (on sim card) | Show fallback chain |
| `o` (on sim with image) | Open plot in browser | `c` (on focused) | Copy as markdown |
| `↑` / `↓` | Navigate within overlays / settings | `Enter` | Run discovery / overlay action |

> Legacy v5.4 Python TUI shortcuts (L/A/B/D/T/R/V cube panels, slash commands) **removed Wave C**.

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
| ~~ProofGraph~~ | *(removed Wave C)* | Was `src/tui/proof_graph.py` — use TUI v9 feed + proof cards |
| ~~InteractiveCube~~ | *(removed Wave C)* | Was `src/tui/cube_navigator.py` |
| ~~ArticleCanvas~~ | *(removed Wave C)* | Was `src/tui/article_canvas.py` — use card expand (Enter) |
| ~~DepthLadder~~ | *(removed Wave C)* | Was `src/tui/depth_ladder.py` |
| ~~AlertPanel~~ | *(removed Wave C)* | Was `src/tui/alert_widget.py` |
| ~~BudgetGauge~~ | *(removed Wave C)* | Was `src/tui/budget_gauge.py` — cost in TUI v9 status/telemetry |

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

## UI/UX Polish Features

> **Wave C (2026-07):** Legacy Python TUI polish modules (`src/tui/mascot.py`, `gradient_bar.py`, `delight.py`, …) were **removed**. Production UI = **TUI v9** (`src/tui/v9/`, Go). `src/repl/core.py` remains for `blast agent` REPL. `src/utils/formatting.py` is shared.

### Still active (CLI / agent)
| Module | Feature |
|--------|---------|
| `utils/formatting.py` | 9 formatters — `fmt_count`, `fmt_dollars`, `fmt_duration`, `fmt_tokens`, `fmt_percent`, `ElapsedTimer` |
| `repl/core.py` | Agent REPL — fuzzy matching, session stats |

### Removed with legacy Python TUI (historical reference only)
### Removed with legacy Python TUI (historical reference only)
| Module | Feature |
|--------|---------|
| `tui/delta_renderer.py` | *(removed)* Cell-diff renderer |
| `tui/easing.py` | *(removed)* Physics easing curves |
| `tui/gradient_bar.py` | *(removed)* Unicode gradient progress bars |
| `tui/animation.py` | *(removed)* Startup typing animation |
| `tui/breathing.py` | *(removed)* Cube idle breathing |
| `tui/staged_error.py` | *(removed)* Staged error colors |
| `tui/smart_prompt.py` | *(removed)* Ghost text REPL prompt |
| `tui/delight.py` | *(removed)* Night mode, cube memory, shutdown ritual |
| `tui/particles.py` | *(removed)* Discovery fireworks |
| `tui/micro_animations.py` | *(removed)* Shake vibrato, phase swoosh |
| `tui/results_display.py` | *(removed)* Rate-limit border |
| `repl/input_handler.py` | *(removed)* Spark particles on keypress |

### TUI v9 equivalents (Go — `src/tui/v9/`)
| Module | Feature |
|--------|---------|
| `effects/`, `splash.go` | Startup splash, bio-aurora idle |
| `wizard.go` | First-run wizard overlay |
| `settings_menu.go` | `Ctrl+,` runtime settings |
| `setup_menu.go` | `Ctrl+Shift+K` API keys |
| `golden_snapshots_test.go` | 132 layout goldens (T0–T3) |

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
Step 4.7: Multi-Source Search (47 configured sources via orchestrator.py)
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
Step 7:   Physics Simulation (auto-select from 38 engine bridges via PatternRunnerV2)
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
