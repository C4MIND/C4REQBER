---
layout: default
---

<link rel="stylesheet" href="assets/css/style.css">

# API Reference

> API documentation for c4reqber v5.4.0. Commands are available via `blast` CLI.

## Blast Commands

### `blast solve "problem"`

Solve a problem — produces strategic artifacts (PRD, plans, blueprints, code).

**Options:**
- `--mode, -m` — Pipeline mode: autopilot|turbo|deep-work
- `--format, -f` — Output: auto|prd|code|plan|blueprint|protocol
- `--domain, -d` — Domain hint
- `--output, -o` — Output file path
- `--verbose, -v` — Show detailed output

### `blast turbo "topic"`

Generate paradigm-shifting research proposal with scientific rigor.

**Options:**
- `--verify-backend` — Verification: hybrid|z3|lean4|coq|dafny|agda|hoare
- `--functors/--no-functors` — Enable 9 cognitive functor agents
- `--plugins, -p` — Plugins: swot,six_hats,first_principles...
- `--output, -o` — Output file path
- `--verbose, -v` — Show quality report

### `blast flash "question"`

Get a quick answer — no pipeline, just fast LLM + optional web search.

**Options:**
- `--sources, -s` — Include source citations
- `--deep, -d` — Deep mode: USP cognitive components + multi-source search
- `--format, -f` — Output format: concise|detailed|bullet|code

### `blast turbofactory "domain"`

Run parallel paradigm factory (10-100 pipelines) for ultimate domain reports.

**Options:**
- `--scale, -s` — Scale: mini(5)|standard(10)|mega(25)|giga(100)
- `--output, -o` — Output file path
- `--max-concurrent, -c` — Max concurrent pipelines
- `--pipeline, -p` — Pipeline: solve|turbo|mixed

### `blast "query"`

Auto-route query to best mode based on query characteristics.

## Backends

6 formal verification backends: Z3 (numerical/fast), Lean4, Coq, Dafny, Agda, Hoare.

### Agenda API

`POST /v8/agenda/generate` — Generate research agenda from knowledge graph + gaps.
`POST /v8/agenda/approve` — Approve a research question for execution.
`GET /v8/agenda/progress` — Track agenda progress and covered topics.

### Verification API

`POST /v8/verification/hypothesis` — Unified hypothesis verification (statistical → formal → unified score).
Supports few-shot RAG retrieval across 251 examples (Lean4×56, Coq×48, Dafny×52, Z3×50, Agda×45).

## Search Sources

37 knowledge sources + Brave Search: arXiv, PubMed, Semantic Scholar, OpenAlex, CrossRef, DOAJ, Europe PMC, DBLP, DataCite, Zenodo, FigShare, CORE, NCBI E-utilities, PubChem, ChEMBL, Materials Project, AFLOW, Kaggle, UCI ML Repository, Harvard Dataverse, re3data, and 16 additional sources via orchestrator.py.

## Python API

```python
from src.agents.pipeline import UniversalSolvePipeline
from src.pipeline.hil_pipeline import HILDiscoveryPipeline

# Solve a problem
pipeline = UniversalSolvePipeline()
result = pipeline.solve("your problem", mode="autopilot")

# Generate research proposal
hil = HILDiscoveryPipeline()
record = await hil.discover("your topic")
```

## REST API Endpoints (v5.3.0)

### Discovery

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/v8/discover/dissertation` | POST | Paradigm shift detection (12-step pipeline, 20 wired modules) |
| `/api/v8/discover/export` | POST | Export results (LaTeX, MD, JSON, HTML, PDF, BibTeX) |
| `/api/v8/discover/gaps` | POST | Gap analysis via GapAnalyzer (ABC) |
| `/api/v8/discover/novelty` | POST | Novelty validation (HARD gate) |
| `/api/v8/discover/already_shifted` | POST | Check if paradigm already shifted (iterative, subtractive confidence) |
| `/api/v8/discover/falsify` | POST | Falsification engine (Popper) |

### Pipeline v5.3.0

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/v8/pipeline/start` | POST | Start pipeline with BasePipeline |
| `/api/v8/pipeline/status` | GET | Pipeline status + step progress |
| `/api/v8/pipeline/competing_hypotheses` | POST | Generate competing hypotheses |
| `/api/v8/pipeline/redundant_gates` | POST | N-version redundant gates validation |
| `/api/v8/pipeline/discovery_memory` | GET | Query discovery memory cache |
| `/api/v8/pipeline/auto_fix` | POST | Self-healing import resolution |

### Knowledge

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/v8/knowledge/search` | POST | Multi-source search (28 sources via orchestrator) |
| `/api/v8/knowledge/temporal` | POST | Temporal knowledge graph query |
| `/api/v8/knowledge/contradictions` | POST | Contradiction mining across sources |

## MCP Tools

18 MCP tools available via `c4reqber serve --mcp`:

| Tool | Description |
|------|-------------|
| `c4_solve` | Run 10-step discovery pipeline |
| `c4_fingerprint` | Classify problem to C4 state (Z₃³) |
| `c4_search` | Search across 28 knowledge sources |
| `c4_simulate` | Run 101+ scientific simulation patterns |
| `c4_triz` | Resolve contradiction via TRIZ matrix (40×40) |
| `c4_verify` | Generate Lean4/Coq/Dafny proof |
| `c4_bayesian` | Run Bayesian inference (MCMC/BMA) |
| `c4_causal` | Causal discovery (do-calculus) |
| `c4_export` | Export to LaTeX/Markdown/JSON/HTML/PDF/BibTeX |
