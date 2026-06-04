# MCP Registry Submission Guide — c4reqber

This document covers how to list c4reqber on all major MCP registries and discovery platforms.

---

## 1. modelcontextprotocol.io Registry

### Registry URL
https://github.com/modelcontextprotocol/servers

### Submission Method
Create a PR adding c4reqber to the appropriate category in the README.

### Category
`🧠 Knowledge & Memory` or `🔬 Scientific Computing` (proposed new category)

### Entry Template

```markdown
### [c4reqber](https://github.com/c4reqber/turbo-cdi)

Cognitive exoskeleton for AI agents. Provides formal cognitive architecture (C4, 27 states, Z₃³), causal reasoning (do-calculus), 101 scientific simulations (5 physics engines), 14 knowledge sources, formal verification (Lean 4/Agda), and Bayesian inference (MCMC/BMA) via MCP.

- **Tools (10+):** `c4_fingerprint`, `triz_contradiction`, `pattern_simulate`, `abductive_infer`, `causal_analyze`, `paradigm_detect`, `lean4_verify`, `knowledge_search`, `bayesian_update`, `system_dynamics`
- **License:** AGPL-3.0 + Commercial
- **Install:** `pip install c4reqber && c4reqber serve --mcp`
```

### Required Files in Repo

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Project overview with MCP badge | ✅ Complete |
| `LICENSE` | AGPL-3.0 | ✅ Ready |
| `src/mcp/server.py` | MCP server implementation | Deploying |
| `CONTRIBUTING.md` | Contribution guidelines | ✅ Complete |
| `CODE_OF_CONDUCT.md` | Community standards | ✅ Complete |
| `SECURITY.md` | Security policy | ✅ Complete |

### MCP Server Configuration (for clients)

```json
{
  "mcpServers": {
    "c4reqber": {
      "command": "c4reqber",
      "args": ["serve", "--mcp"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
        "ARXIV_EMAIL": "your-email@example.com"
      }
    }
  }
}
```

### Claude Desktop Config

```json
{
  "mcpServers": {
    "c4reqber": {
      "command": "python",
      "args": ["-m", "c4_cdi_turbo.mcp.server"],
      "env": {
        "C4_CDI_CONFIG": "/path/to/config.yaml"
      }
    }
  }
}
```

### PR Description Template

```
## c4reqber — Cognitive Exoskeleton for AI Agents

### What it does
First MCP-native cognitive layer for AI agents. Provides:
- Formal cognitive architecture (C4: 27 states, Z₃³, Theorem 11)
- 8 cognitive layers (causal, Bayesian, system dynamics, decisions, discovery, literature intel, experimental design, meta)
- 101 scientific simulations on 5 GPU-accelerated physics engines
- 14 federated knowledge sources with unified search
- Formal verification via Lean 4 and Agda
- 10+ MCP tools

### Why it matters
14,208 MCP servers exist on GitHub. Zero provide cognitive layers. Agents have plumbing but no brain. c4reqber is the prefrontal cortex — giving agents structured scientific reasoning, not just API access.

### Repository
https://github.com/c4reqber/turbo-cdi

### Tests
9,857 tests, production grade 10/10

### License
AGPL-3.0 + Commercial
```

---

## 2. GitHub MCP Topic

### Topic Name
`mcp-server`

### How to Add

1. Go to https://github.com/c4reqber/turbo-cdi
2. Click the gear icon next to "About" on the right sidebar
3. Add topics: `mcp-server`, `mcp`, `cognitive-architecture`, `scientific-computing`, `ai-agents`

### Recommended Topics

| Topic | Rationale |
|-------|-----------|
| `mcp-server` | Primary discovery tag for MCP ecosystem |
| `mcp` | General MCP topic |
| `cognitive-architecture` | Differentiator from tool-only MCP servers |
| `scientific-computing` | Core domain |
| `formal-verification` | Unique capability |
| `causal-reasoning` | Key differentiator |
| `physics-simulation` | 5-engine integration |
| `bayesian-inference` | Cognitive layer |
| `triz` | Innovation methodology |
| `ai-agents` | Target audience |
| `open-source` | License visibility |

### GitHub Search Visibility

After adding topics, c4reqber will appear in:
- https://github.com/topics/mcp-server
- https://github.com/topics/mcp
- https://github.com/topics/cognitive-architecture
- `gh search repos --topic mcp-server` results

---

## 3. Smithery.ai

### Registry URL
https://smithery.ai

### Submission Method
Smithery auto-discovers MCP servers from npm/PyPI packages with `mcp-server` keyword. Ensure `pyproject.toml` includes:

```toml
[project]
name = "c4reqber"
keywords = ["mcp", "mcp-server", "cognitive-architecture", "scientific-computing", "ai-agents"]
classifiers = [
    "Framework :: Model Context Protocol (MCP)",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Scientific/Engineering :: Mathematics",
    "License :: OSI Approved :: GNU Affero General Public License v3",
]
```

### Smithery Listing Preview

**Name:** c4reqber
**Tagline:** Cognitive Exoskeleton for AI Agents — Formal cognitive layer with 101 simulations, 5 physics engines, formal verification
**Category:** Knowledge & Reasoning
**Tools:** c4_fingerprint, triz_contradiction, pattern_simulate, abductive_infer, causal_analyze, paradigm_detect, lean4_verify, knowledge_search, bayesian_update, system_dynamics
**Weekly Downloads:** (tracked after PyPI publish)
**License:** AGPL-3.0 + Commercial

### Installation Badge

```markdown
[![Smithery](https://smithery.ai/badge/c4reqber)](https://smithery.ai/server/c4reqber)
```

---

## 4. PyPI Listing

### Package Metadata (pyproject.toml)

```toml
[project]
name = "c4reqber"
version = "8.0.0"
description = "Cognitive Exoskeleton for AI Agents — MCP-native cognitive layer"
readme = "README.md"
license = {text = "AGPL-3.0"}
authors = [
    {name = "Nikolai Rozanov", email = "c4reqber@proton.me"}
]
keywords = ["mcp", "mcp-server", "cognitive-architecture", "scientific-computing"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Framework :: Model Context Protocol (MCP)",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Programming Language :: Python :: 3.11",
]
requires-python = ">=3.11"

[project.urls]
Homepage = "https://github.com/c4reqber/turbo-cdi"
Documentation = "https://github.com/c4reqber/c4reqber/tree/main/docs"
Repository = "https://github.com/c4reqber/turbo-cdi"
Issues = "https://github.com/c4reqber/c4reqber/issues"

[project.scripts]
c4reqber = "c4_cdi_turbo.cli:main"

[project.entry-points.mcp]
"c4reqber" = "c4_cdi_turbo.mcp.server:create_server"
```

### Publish Command

```bash
# Build
python -m build

# Check (optional)
twine check dist/*

# Publish to TestPyPI first
twine upload -r testpypi dist/*

# Publish to PyPI
twine upload dist/*
```

---

## 5. Additional Discovery Channels

### Awesome Lists

Create PRs to add c4reqber to:

| List | URL | Category |
|------|-----|----------|
| awesome-mcp-servers | github.com/punkpeye/awesome-mcp-servers | Knowledge & Memory |
| awesome-mcp | github.com/appcypher/awesome-mcp-servers | Scientific |
| awesome-llm-apps | github.com/Shubhamsaboo/awesome-llm-apps | Research Tools |
| awesome-scientific-computing | github.com/nschloe/awesome-scientific-computing | Frameworks |

### PR Template for Awesome Lists

```markdown
## c4reqber

**Description:** Cognitive exoskeleton for AI agents providing formal cognitive architecture (C4, 27 states, Z₃³), 101 scientific simulations, 5 physics engines, 14 knowledge sources, and formal verification (Lean 4/Agda). MCP-native with 10+ tools.

**GitHub:** https://github.com/c4reqber/turbo-cdi
**PyPI:** https://pypi.org/project/c4reqber
**License:** AGPL-3.0 + Commercial
**Tests:** 9,857 | Grade: 10/10
```

### Reddit Communities for Launch

| Subreddit | Focus | Post Type |
|-----------|-------|-----------|
| r/MachineLearning | ML research | Technical overview + arXiv link |
| r/LocalLLaMA | Local AI | MCP integration + local models |
| r/Python | Python devs | PyPI package announcement |
| r/Physics | Physicists | Physics engine integration |
| r/CompSocial | Computational social science | System dynamics + simulations |

### Discord/Slack Communities

- MCP Discord (if exists)
- LangChain Discord (#showcase)
- EleutherAI Discord
- Hugging Face Discord (#research)

---

## 6. MCP Tool Specification (for Registry Documentation)

### Tool: `c4_fingerprint`
**Description:** Classify a problem into the C4 cognitive space (Z₃³, 27 states).
**Input:** `problem_text` (string) — natural language problem description.
**Output:** `{state: (t, s, a), confidence: float, reasoning: string}` — C4 state coordinates with confidence score.
**Uses:** OpenAI/OpenRouter LLM for classification (with keyword-heuristic fallback).

### Tool: `triz_contradiction`
**Description:** Solve engineering contradictions using the TRIZ 39×39 matrix.
**Input:** `improving_param` (int, 1-39), `worsening_param` (int, 1-39).
**Output:** `{principles: [int], descriptions: [string], examples: [string]}` — recommended inventive principles.
**Algorithm:** Lookup in 1,482-cell contradiction matrix (precomputed from TRIZ literature).

### Tool: `pattern_simulate`
**Description:** Run a scientific simulation pattern against a hypothesis.
**Input:** `pattern` (string, e.g., "seir_epidemic"), `params` (dict), `hypothesis` (string).
**Output:** `{metrics: dict, charts: [bytes], execution_time_ms: float}` — simulation results.
**Engines:** Newton, TorchSim, JaxSim, Schr, vast.ai (auto-detected hardware).

### Tool: `causal_analyze`
**Description:** Discover causal relationships using Pearl's do-calculus.
**Input:** `variables` (list), `observations` (list of dicts), `query` (string).
**Output:** `{graph: dict, do_effect: float, counterfactuals: [dict]}` — causal DAG and estimated effects.
**Algorithm:** PC/FCI for DAG discovery, do-calculus for interventions.

### Tool: `paradigm_detect`
**Description:** Detect paradigm shifts in scientific literature.
**Input:** `domain` (string), `time_range` (years), `threshold` (float).
**Output:** `{anomalies: [dict], contradictions: [dict], shift_probability: float}` — potential paradigm shifts.
**Algorithm:** Temporal knowledge graph analysis + contradiction mining.

### Tool: `lean4_verify`
**Description:** Formally verify a discovery using Lean 4 theorem prover.
**Input:** `hypothesis` (string), `premises` (list).
**Output:** `{lean_file: string, verification_status: string, proof_log: string}` — Lean 4 proof output.
**Requires:** Lean 4 toolchain installed locally.

### Tool: `knowledge_search`
**Description:** Unified search across 14 federated knowledge sources.
**Input:** `query` (string), `sources` (list, default: all), `max_results` (int).
**Output:** `{results: [{source, title, url, abstract, license}], total: int}` — ranked results.
**Sources:** arXiv, PubMed, ORCID, Semantic Scholar, CrossRef, bioRxiv, medRxiv, GitHub, Zenodo, Figshare, CiNii, RSCI, BASE.

### Tool: `bayesian_update`
**Description:** Update beliefs using Bayesian inference.
**Input:** `prior` (dict), `likelihood` (dict), `method` (string: MCMC/BMA).
**Output:** `{posterior: dict, model_probabilities: dict, diagnostics: dict}` — posterior distributions.
**Methods:** Metropolis-Hastings, Gibbs, HMC, NUTS, Bayesian Model Averaging.

### Tool: `system_dynamics`
**Description:** Simulate feedback loops using Stock-Flow DSL.
**Input:** `stocks` (list), `flows` (list), `params` (dict), `time_range` (years).
**Output:** `{trajectory: [float], archetype: string, leverage_points: [dict]}` — simulation results.
**Archetypes:** Limits to Growth, Shifting the Burden, Tragedy of the Commons, and 2 more.

### Tool: `abductive_infer`
**Description:** Generate and rank explanatory hypotheses (IBE).
**Input:** `observations` (list), `domain_context` (string).
**Output:** `{hypotheses: [{text, score, explanation}], ranking: [int]}` — ranked hypotheses.
**Algorithm:** Inference to the Best Explanation with consistency, simplicity, and explanatory power scoring.

---

## 7. Launch Checklist

| # | Task | Platform | Status |
|---|------|----------|--------|
| 1 | Publish to PyPI | PyPI | Ready |
| 2 | Add GitHub topics | GitHub | Ready |
| 3 | PR to MCP registry | modelcontextprotocol.io | Draft ready |
| 4 | Submit to Smithery | Smithery.ai | Auto-discovered via PyPI |
| 5 | PR to awesome-mcp-servers | GitHub | Draft ready |
| 6 | PR to awesome-mcp | GitHub | Draft ready |
| 7 | Post on r/MachineLearning | Reddit | Draft in twitter_launch.md |
| 8 | Post on r/LocalLLaMA | Reddit | Ready |
| 9 | Post on r/Python | Reddit | Ready |
| 10 | arXiv preprint submission | arXiv.org | Draft in arxiv_preprint.md |
| 11 | Show HN post | Hacker News | Draft in show_hn.md |
| 12 | Twitter/X thread | X.com | Draft in twitter_launch.md |
| 13 | Product Hunt listing | producthunt.com | Draft in launch/product-hunt.md |
