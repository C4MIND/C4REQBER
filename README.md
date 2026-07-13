# c4reqber — Cognitive Exoskeleton for AI Agents

**Terminal-first. MCP-native. One command to discovery.**

[![Tests](https://img.shields.io/badge/tests-9906%20collected-yellowgreen)]()
[![Lint](https://img.shields.io/badge/lint-41%20baseline%20%2B%20regression%20check-yellow)]()
[![Typecheck](https://img.shields.io/badge/typecheck-0%20mypy%20errors-brightgreen)]()
[![Version](https://img.shields.io/badge/version-5.6.0-magenta)]()
[![TUI](https://img.shields.io/badge/TUI-v9.13.0-blueviolet)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-AGPL--3.0-green)]()
[![PyPI](https://img.shields.io/pypi/v/c4reqber)](https://pypi.org/project/c4reqber/)
[![Security](https://img.shields.io/badge/security-round5%20audit%20passed-brightgreen)]()

> **Truth source:** all counts (tests, tools, sources, engines, providers, verifiers)
> are generated from `_truths.json` via `scripts/gen_truths.py --check`. Run the
> script in CI to catch drift. See `CHANGELOG.md` for release history.

## Quickstart

```bash
pip install c4reqber
blast setup                         # wizard: packages + API keys
cp .env.example .env                # add OPENROUTER_API_KEY — see docs/API_KEYS.md
blast solve "your problem"          # One-shot discovery → article/blueprint/whitepaper
blast turbo "your topic"            # Paradigm-shifting research proposal + verification
blast flash "your question"         # Quick answer
blast auto "your query"             # Auto-routed to best mode (solve/turbo/flash)
blast turbofactory "your domain"    # Parallel pipeline factory (mini/standard/mega/giga scale)
blast tui                           # TUI v9 Cockpit (feed-driven discovery UI)
blast serve --mcp                   # MCP server for AI agents (21 tools)
```

**Docker (optional API only):** [docs/INSTALL.md](docs/INSTALL.md) · `docker compose -f docker-compose.release.yml up -d`

## Verified pipeline outputs (July 2026)

Six **research proposals** from end-to-end `blast turbo` runs (400–500 literature sources, gap analysis, simulation, quality gates). Full index: [`discoveries/humanity_mission_2026-07-09/README.md`](discoveries/humanity_mission_2026-07-09/README.md).

> **Epistemic status:** hypotheses + computational pre-screening only — **not peer-reviewed**. Each file includes an explicit disclaimer. Do not cite as established science without empirical validation.

| Topic | Words | Proposal |
|-------|------:|----------|
| Marine cloud brightening | 5,083 | [`01_marine_cloud_brightening.md`](discoveries/humanity_mission_2026-07-09/01_marine_cloud_brightening.md) |
| Compact fusion energy | 4,859 | [`02_compact_fusion.md`](discoveries/humanity_mission_2026-07-09/02_compact_fusion.md) |
| Epigenetic aging reversal | 4,564 | [`04_epigenetic_aging.md`](discoveries/humanity_mission_2026-07-09/04_epigenetic_aging.md) |
| AMR phage–CRISPR cocktail | 5,058 | [`05_amr_phage_crispr.md`](discoveries/humanity_mission_2026-07-09/05_amr_phage_crispr.md) |
| Soil carbon / desertification | 5,102 | [`06_soil_carbon.md`](discoveries/humanity_mission_2026-07-09/06_soil_carbon.md) |
| Ocean plastic bioremediation | 5,395 | [`08_ocean_plastic_v2.md`](discoveries/humanity_mission_2026-07-09/08_ocean_plastic_v2.md) |

**Demo:** [TUI screenshots](docs/screenshots/) · [30s video](docs/demo/c4reqber_mission_demo_30s.mp4) · [Web gallery](https://c4reqber.org/discoveries/)

## What is this?

A cognitive exoskeleton for AI agents and humans.
- **C4-META**: 27 cognitive states, Z₃³ topology, 6 operators, Theorem 11 (undirected Ø=3)
- **9 real verification backends** (Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy)
- **251 few-shot proof examples**: 56 Lean4 + 48 Coq + 52 Dafny + 50 Z3 + 45 Agda, with TF-IDF RAG retrieval
- **Causal inference adult**: DoWhy + EconML + gCastle (PC, FCI, NOTEARS, ANM) with data-driven / toy fallback tagging
- **Hypothesis ranking**: PriorScorer × EIGEstimator × CostModel × MCDMRanker (weighted MCDM) integrated into discovery pipeline
- **Closed-loop simulation**: Bayesian tracker, experiment designer, ensemble runner, convergence checker, refiner
- **Self-directed agenda**: Generator, feasibility checker, priority scorer, progress tracker, TUI screen (shift+a)
- **Open-ended exploration**: Anomaly detector (IsolationForest), surprise-driven question generator, formal framework extender
- **6 output formats**: dissertation, article, whitepaper, blueprint, code, verification_report — auto-detected
- **Verification guardrails**: complexity pre-flight, memory caps (256MB-1GB), hang detection (5-60s), proof export (.lean/.v/.smt2)
- **Embedding pipeline acceleration**: semantic dedup, smart evidence matching, coverage analysis
- **Multi-LLM Council**: 3-model consensus with cheap/balanced/premium budgets
- **Kuhn Paradigm Shift Assessment**: 4-stage model, 5 values, iterative refinement
- **TUI v9 command palette** (`:` key): fuzzy-match 35+ commands (settings, capabilities, history, language, debug)
- **11 LLM providers**: OpenRouter, XAI, Mistral, Moonshot, DeepSeek, Liquid AI, NVIDIA NIM, YandexGPT, Ollama, LM Studio, MLX — auto-detected with depth-based routing
- **47 configured knowledge source integrations** (46 wired to `MultiSourceSearcher`; runtime-active subset depends on credentials and availability)

**v5.4.0:** "Agent System + Git Hygiene + Code Audit" — main AI agent with Pydantic AI, skills, MCP bridge, persistent memory, sub-agents; 3 critical eval() sandboxes fixed; git secrets removed

**v5.4.2:** "Round 4 Security & Correctness Audit" — 16 CRITICAL + 39 HIGH + 55 MEDIUM + 14 LOW fixes applied across Python backend and Go TUI v8. Highlights: prompt injection hardening with nonce delimiters, LaTeX escaping, ChromaDB race fixes, velocity Verlet integration, Bonferroni correction, lock-free theme reads via atomic.Value, unified error taxonomy, centralized security middleware, unbounded goroutine fixes, and 594 passing tests.

**v5.6.0:** "Dead Code Cleanup + API Integration + Pydantic V2 + TUI v8 Polish" — removed 6 dead modules (r1/, skills/, arxiv_adapter, prior_art, dependencies_v6, v6_schemas); integrated 14 API keys into MultiSourceSearcher; Pydantic V1→V2 migration complete; citation verifier hardened against hallucinated theory names; TUI v8 mascot rewritten (Quantum→Cube) with theme-aware colors and S-rank jump animation; Go audit: go vet clean, staticcheck 0 warnings; 9908+ tests collected.

**v9.13.0:** "TUI v9 Simulation Surface" — capabilities overlay (`Ctrl+Shift+C`) listing 38 engine bridges + 9 verifiers with per-platform status and install hints; `CardSimulation` kind rendered in the feed with engine/verdict/fallback-chain/install-hint; typed SSE decoder ready for backend's new `sim_started/sim_finished/sim_skipped` events; 4 new sim-specific achievements (Sim Explorer, Devil's Advocate, Fallback Chef, Cloud Native); command palette (`:`) fuzzy-matches 35+ commands; per-card expansion (Enter to see FullBody, Esc to collapse); adaptive layout (T0/T1/T2/T3); status bar (Ctrl+B); debug overlay (Ctrl+Shift+D); solarized-dark color profile; feed.jsonl persistence + resume on launch; 132 golden snapshots, 100% i18n parity across 7 languages via `regen_i18n.py`. 27 commits, +7302 lines, 0 critical bugs. TUI v9 merged on `main`; see `src/tui/v9/ARCHITECTURE.md`.

## Output Formats (6, auto-detected)

| Format | turbo pages | When auto-selected |
|--------|-------------|-------------------|
| **Dissertation** | 5-15 | "dissertation", "thesis", "paradigm shift" |
| **Article** | 4-12 | "paper", "journal", "study" |
| **Whitepaper** | 5-15 | "architecture", "whitepaper", "platform" |
| **Blueprint** | 3-12 | "blueprint", "specification", "api" |
| **Code** | 100-500 LOC | "code", "implement", "algorithm" |
| **Verification Report** | 1-5 | "verify", "prove", "theorem" |

## Verification Backends (9 real + MathDetector)

**Real (machine-checked when tool installed):** Lean4, Coq, Dafny, Agda, Z3/Hoare, Haskell, CVC5, TLA+, Alloy.
**TLA+:** bounded models only — see [docs/VERIFICATION_BACKENDS.md](docs/VERIFICATION_BACKENDS.md).

```
Lean4 → Coq → Dafny → Agda → Z3/CVC5 → Hoare → TLA+ → Alloy → Haskell
   │                              │
   Complexity pre-flight      Auto-fallback chain
   Memory + hang detection    Proof export .lean / .v / .smt2 / .tla / .als
```

## TUI v9 — Command Palette (`:` key)

Press `:` to open fuzzy-search command palette. Examples:

| Command | Action |
|---------|--------|
| Settings | `Ctrl+,` — LLM tier, language, color profile, history |
| Capabilities | `Ctrl+Shift+C` — 38 sim engine bridges + 9 verifiers |
| Help | `?` — keyboard shortcuts overlay |
| Debug | `Ctrl+Shift+D` — SSE/job debug snapshot |
| Language | `L` — cycle EN/RU/ZH/JA/DE/AR/HI |

Legacy Python TUI slash commands (`/models`, `/council`, …) apply to **v8 only**. Use `blast config` for LLM/council setup with v9.

## Quick Config & First Run (Polished Desktop Experience)

```bash
# First run — beautiful wizard that sets everything
blast init

# Full settings view
blast config user --show          # ~/.c4reqber/config.toml + keys
blast config keys                 # Quick key status
blast config --show               # Model assignments per phase

# Set models
blast config --set D=anthropic/claude-sonnet-4.6 --save
```

All keys (OpenRouter, DeepSeek, Brave, Tavily, Exa, XAI, Lean4...) are managed in `~/.c4reqber/config.toml` + `models.json`. The desktop app, CLI and TUI all read from the same place.

## Install from source

```bash
git clone https://gitlab.com/cognitive-functors/c4reqber.git
cd c4reqber
cp .env.example .env
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Data Sources

C4REQBER integrates with **33+ scientific data and literature sources** across all tiers of openness. Sources are categorized by integration difficulty and data type.

### Environment Variables for API Keys

> **Full registration guide (EN/RU):** [`docs/API_KEYS.md`](docs/API_KEYS.md) — step-by-step signup for every service.
> **Quick reference on GitLab Pages:** [API Keys setup](https://cognitive-functors.gitlab.io/turbo-cdi/docs/setup/api-keys.html) (links to the full doc).

Copy these into your `.env` file. Keys marked **Required** will disable the source if missing. **Optional** keys increase rate limits but the source works without them.

| Variable | Source | Status | How to obtain |
|----------|--------|--------|---------------|
| `NCBI_API_KEY` | NCBI E-utilities (PubMed, GEO, etc.) | Optional | [ncbi.nlm.nih.gov](https://www.ncbi.nlm.nih.gov/account/) |
| `MATERIALS_PROJECT_API_KEY` | Materials Project | Required | [materialsproject.org](https://materialsproject.org/) |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | Kaggle datasets | Required | [kaggle.com/settings](https://www.kaggle.com/settings) |
| `HARVARD_DATAVERSE_API_KEY` | Harvard Dataverse | Optional | [dataverse.harvard.edu](https://dataverse.harvard.edu/) |
| `OPENFDA_API_KEY` | OpenFDA / FAERS | Optional | [open.fda.gov/apis](https://open.fda.gov/apis/authentication/) |
| `NASA_EARTHDATA_TOKEN` | NASA Earthdata (CMR) | Required | [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov/) |
| `ORCID_CLIENT_ID` + `ORCID_CLIENT_SECRET` | ORCID Public API | Required | [orcid.org/developer-tools](https://orcid.org/developer-tools) |
| `OPENALEX_API_KEY` | OpenAlex | Optional | [openalex.org](https://openalex.org/) |
| `BRAVE_API_KEY` | Brave Search | Required | [brave.com/search/api](https://brave.com/search/api/) |
| `CORE_API_KEY` | CORE | Required | [core.ac.uk/services/api](https://core.ac.uk/services/api) |
| `BASE_API_KEY` | BASE Search | Required | [base-search.net](https://base-search.net/about/en/help_services_api.php) |
| `UNPAYWALL_API_KEY` | Unpaywall | Required | [unpaywall.org/products/api](https://unpaywall.org/products/api) |
| `OA_MG_API_KEY` | OA.mg | Required | [oa.mg/api](https://oa.mg/api) |
| `LENS_ORG_API_KEY` | Lens.org | Required | [lens.org](https://www.lens.org/lens/user/subscriptions) |

### Tier 1 — Open Access (no API key required)

| Source | Type | Coverage | Domain |
|--------|------|----------|--------|
| **arXiv** | Preprints | 2M+ papers | Physics, CS, Math |
| **Crossref** | DOI registry | 150M+ records | All disciplines |
| **Europe PMC** | Biomedical literature | 42M+ publications | Biomedicine |
| **DOAJ** | OA journals | 18K+ journals | All |
| **Zenodo** | Datasets, papers | 3M+ records | All |
| **Figshare** | Research outputs | 20M+ items | All |
| **re3data** | Repository registry | 3,000+ repos | All |
| **UCI ML Repository** | ML datasets | 600+ datasets | CS / ML |
| **Harvard Dataverse** | Research datasets | 100K+ datasets | Social sciences |
| **ClinicalTrials.gov** | Clinical trials | 460K+ trials | Medicine |
| **USPTO PatentsView** | US patents | 12M+ patents | Engineering |
| **GBIF** | Species occurrences | 2.5B+ records | Ecology, Biology |
| **USGS** | Earthquakes, geology | Global | Geoscience |
| **CERN Open Data** | LHC data | Particle physics | Physics |
| **OEIS** | Integer sequences | 360K+ sequences | Mathematics |
| **ConceptNet** | Semantic network | General knowledge | NLP, AI |
| **OpenReview** | ML conferences | NeurIPS/ICML/ICLR | CS / ML |
| **HuggingFace Datasets** | ML datasets | 500K+ datasets | CS / ML |
| **STRING DB** | PPI networks | 24.6M proteins | Biology |
| **Allen Brain Atlas** | Neuroanatomy | Gene expression | Neuroscience |
| **CyberLeninka** | Russian OA journals | Open access | Russian science |
| **Math-Net.Ru** | Math portal | Russian mathematics | Mathematics |

### Tier 2 — Free with API Key (recommended for production)

| Source | Type | Coverage | Key Required |
|--------|------|----------|-------------|
| **Semantic Scholar** | AI-enriched papers | 200M+ papers | Optional |
| **OpenAlex** | Open catalog | 250M+ works | Optional |
| **NCBI E-utilities** | Gene, GEO, ClinVar | Multi-database | Optional |
| **Materials Project** | DFT materials | 150K+ compounds | Required |
| **Kaggle** | ML datasets | 200K+ datasets | Required |
| **OpenFDA** | Adverse events | 20M+ reports | Optional |
| **NASA Earthdata** | Satellite data | Global | Required |
| **ORCID** | Author IDs | 20M+ researchers | Required |

### Tier 3 — Domain-Specific Open

| Source | Type | Coverage | Domain |
|--------|------|----------|--------|
| **PubChem** | Chemical structures | 110M+ compounds | Chemistry |
| **ChEMBL** | Bioactivity | 2M+ compounds | Pharmacology |
| **UniProt** | Proteins | 250M+ sequences | Biology |
| **GTEx** | Gene expression | 50+ tissues | Genomics |
| **DrugBank** | Drugs | 15K+ drugs | Pharmacology |
| **AFLOW** | Materials | 3.5M+ entries | Materials |
| **NOAA** | Climate data | Global | Environment |
| **Inspire-HEP** | HEP literature | 1.5M+ records | Physics |
| **DBLP** | CS bibliography | 7M+ publications | CS |
| **Datacite** | DOI metadata | 50M+ DOIs | All |

### Tier 4 — Commercial / Pending

| Source | Type | Coverage | Status |
|--------|------|----------|--------|
| **Web of Science** | Citation index | 90M+ records | Requires subscription |
| **Scopus** | Citation index | 100M+ records | Requires subscription |
| **Dimensions** | Analytics | 136M+ publications | Requires subscription |
| **eLIBRARY / РИНЦ** | Russian science | 79M+ publications | Requires agreement |
| **OMIM** | Human genetics | Genes, disorders | Pending approval |
| **DataCite** | DOI registry | 50M+ DOIs | Pending approval |

---

## Honest Limitations

> c4reqber is a **research-grade cognitive exoskeleton**, not an enterprise SaaS. It works reliably for single-user CLI research workflows. Here is what you should know about its current boundaries.

### What works reliably ✅
- **One-shot discovery** (`blast solve`) — hypothesis generation + paper retrieval + quality scoring
- **Multi-hypothesis search** (`blast turbo`) — parallel pipeline with deduplication
- **Formal verification** — Lean4, Coq, Dafny, Z3, Hoare backends with iterative error correction
- **Auto-formalization** — LLM-driven theorem extraction + multi-language consensus (Lean4 + Coq + Dafny) + semantic alignment check
- **Causal inference** — DoWhy/EconML estimation + ANM/PC/NOTEARS discovery + GP-SCM counterfactuals (data-driven); keyword-based fallback when no data
- **Hypothesis ranking** — Prior scoring + Expected Information Gain + cost model + MCDM ranker
- **Closed-loop simulation** — Bayesian hypothesis tracker + adaptive experiment design + ensemble simulation + convergence detection
- **Self-directed agenda** — Gap-driven / extension-driven / conflict-driven question generation with feasibility scoring
- **Open-ended exploration** — Literature anomaly detection (IsolationForest) + surprise-driven question generation + formal framework extension
- **Knowledge search** — 47 configured source integrations (arXiv, PubMed, Crossref, Europe PMC, Semantic Scholar, OpenAlex, Zenodo, Figshare, NCBI, PubChem, ChEMBL, Materials Project, AFLOW, Kaggle, UCI ML, Harvard Dataverse, re3data, STRING, ClinicalTrials.gov, GBIF, Allen Brain, USGS, CERN, USPTO, OpenReview, HuggingFace, OpenFDA, NASA Earthdata, CyberLeninka, Math-Net.Ru, and more)
- **Python TUI** (blast tui) — Textual interface with real-time progress, chat, history, slash commands
- **Go TUI v9** (src/tui/v9) — Bubble Tea v2 interface with 7-phase pipeline, C4 grid, sim surface (CardSimulation kind + capabilities overlay Ctrl+Shift+C), command palette `:`, debug overlay Ctrl+Shift+D, status bar Ctrl+B, 7-language i18n (100% parity), 7 color profiles (incl. solarized-dark), adaptive layout (T0/T1/T2/T3), 132 golden snapshots
- **Falsification** — Domain-aware simulation + statistical tests with Bonferroni correction
- **MCP server** — 21 tools verified working for AI agent integration

### Known limitations ⚠️

| Feature | Limitation | Why | Workaround |
|---------|-----------|-----|------------|
| **Causal inference (toy fallback)** | When no observational data is provided, returns keyword-based models tagged `"note": "toy_model_fallback_no_data"` | Real causal discovery requires data | Provide CSV/data to enable DoWhy/EconML estimation; otherwise treat output as directional hypotheses |
| **Closed-loop simulation** | Uses surrogate simulator (not actual physics simulators) for Bayesian update | Full integration requires per-simulator likelihood models | Use domain-specific simulators via `run_relevant_simulation()` for real validation |
| **Self-directed agenda** | Questions are generated heuristically, not via LLM by default | LLM generation is expensive for every discovery | Use `/agenda/generate` API endpoint for LLM-enhanced generation when needed |
| **Sentence tokenization** | Regex-based splitting; abbreviations ("Dr.", "e.g.") handled heuristically | NLTK/spaCy adds +500MB dependencies; regex is "good enough" for claim extraction | Output is "best effort"; review extracted claims manually |
| **Token counting** | Uses `tiktoken` when available; falls back to `len(text) // 4` | `tiktoken` is optional dependency; fallback is approximate | Install `tiktoken` for precise counts: `pip install tiktoken` |
| **ChromaDB** | Local, single-instance, sync operations | ChromaDB has no official async API | Sufficient for single-user local RAG; for concurrent multi-user → migrate to pgvector |
| **Hoare verifier** | Handles assignment, sequence, conditional, while (95% of real use) | Complex nested expressions may parse incorrectly | Simplify invariants; avoid deep nesting in Hoare triples |
| **Semantic dedup** | Threshold-based cosine similarity on sentence-transformers embeddings | Edge case: paraphrased papers with different titles may not deduplicate | Adjust threshold or review results manually |
| **Pipeline context** | Mutable dict passed between steps | Making it immutable requires breaking changes across 15+ files | Steps run sequentially; no race conditions in current architecture |

### Security posture 🔒
- **Prompt injection** — Regex + nonce delimiters + HTML entity decoding. Catches 95%+ of known attacks. For adversarial/obfuscated payloads (zero-width joiners, nested entity encoding), defense relies on rate limiting + max length truncation
- **SSRF** — Paper IDs validated; redirects disabled. Not a full URL sandbox
- **Subprocess** — Shell metacharacters blocked; symlink attacks guarded. Not a full seccomp sandbox
- **Path traversal** — Enforced within `~/.c4reqber`. Temp files validated

> For a full security audit report, see `audit/round4_audit.md` (150 findings → 0 CRITICAL, 0 HIGH, 55 MEDIUM resolved, 14 LOW resolved).

## Documentation

All documentation lives in the repo — no separate docs site needed.

| Document | Description |
|----------|-------------|
| **[WHITEPAPER.md](WHITEPAPER.md)** | **Technical whitepaper (EN)** — architecture, verification, simulation, metrics |
| **[WHITEPAPER.ru.md](WHITEPAPER.ru.md)** | **Технический whitepaper (RU)** — билингвальная пара к EN |
| `docs/VERIFICATION_BACKENDS.md` | 9 backends + TLA+ bounded-model guide |
| `AGENTS.md` | Master AI agent context — commands, architecture, code rules, competitive intel |
| `CHANGELOG.md` | Full version history |
| `TECHNICAL_DEBT_ROADMAP.md` | Deferred architectural fixes — when and why each debt item becomes payable |
| `ARCHITECTURE_C4R.md` | C4R system architecture (cognitive, knowledge, simulation, verification) |
| `src/tui/v9/ARCHITECTURE.md` | Go TUI v9 architecture (Bubble Tea v2, cards package, sim surface, command palette, golden snapshots) |
| `audit/TUI_V9_UNIFIED_PLAN_2026-06-11.md` | TUI v9 unified plan — 25 sections, 8 sprints, 27 design decisions, 13 backend contracts |
| `INSTALL.md` | Full developer setup (Python + Go + engines + API keys) |
| `QUICKSTART.md` | First discovery in 5 minutes |
| `docs/onboarding/API_KEYS.md` | How to obtain every API key (registration links, pricing, rate limits) |
| `docs/onboarding/ENGINES.md` | Installing all 38 simulation engines |
| `src/tui/v9/README.md` | Building and running the Go TUI v9 |
| `docs/onboarding/SECRETS.md` | Secure team secrets sharing |
| `docs/API.md` | REST API reference |
| `docs/DESIGN.md` | Design system, visual identity, design tokens |
| `docs/C4_META_Preprint_v5.3.3.md` | C4 cognitive architecture preprint |
| `docs/current/C4_THEOREM_11.md` | Formal proof: C4 graph diameter ≤6 |
| `docs/current/C4_META_SEMANTIC_ISOMORPHISMS.md` | Semantic isomorphism theory |
| `docs/current/UCOS_ARCHITECTURE.md` | UCOS meta-model architecture |
| `formal-proofs/` | Lean4, Coq, Dafny, Agda, Hoare, TLA+ formal verification proofs |
| `docs/mcp_registry.md` | MCP tool registry (21 tools, regenerated by `scripts/gen_mcp_registry.py`) |
| `LICENSE` | AGPL-3.0 (open source) / Commercial License available |
