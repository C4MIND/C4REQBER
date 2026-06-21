# QUICKSTART — First Discovery in 5 Minutes

> **Prerequisite:** `c4reqber` installed.
> First run: `blast init` — sets up `~/.c4reqber/` with all keys and models (recommended).
> See [INSTALL.md](INSTALL.md) and the new `blast config keys` / `blast config user --show`.

---

## 1. One-Shot Discovery

```bash
blast solve "Design a self-healing polymer for aerospace applications"
```

**What happens:**
- 33 knowledge sources searched (arXiv, PubMed, Semantic Scholar, etc.)
- C4 cognitive fingerprint extracted (Z₃³ state)
- TRIZ contradiction resolution
- Gap analysis + novelty validation
- Simulation engine auto-selected (if available)
- Quality gates (A+ to F)
- Output: strategic artifact (PRD / blueprint / code)

---

## 2. Paradigm-Shifting Research

```bash
blast turbo "Quantum error correction with topological codes"
```

**What happens:**
- USP cognitive components (IMPACT, QZRF, MatrixDream, CDI, TOTE)
- 9 functor agents for deep analysis
- Hybrid verification (Lean4/Coq/Dafny/Z3/Hoare/Agda)
- 36 simulation engines evaluated
- Output: research proposal + LaTeX paper skeleton

---

## 3. Quick Answer

```bash
blast flash "What is the current SOTA for protein folding?" --with-sources
```

---

## 4. Interactive TUI (v9 Cockpit)

```bash
# Start backend first (in another terminal):
uvicorn src.api.server:app --port 8000

# Launch TUI v9:
blast tui
# or: cd src/tui/v9 && ./bin/c4tui-v9

# Demo without backend:
blast tui --demo --story=crispr
```

**Key bindings:**
- `Enter` — run discovery
- `Tab` — cycle mode (Discover / Flash / Turbo / TurboFactory)
- `:` — command palette (settings, capabilities, language, debug)
- `?` — help overlay
- `Ctrl+Shift+C` — simulation/verifier capabilities overlay

---

## 5. Auto-Router (Let BLAST Choose)

```bash
blast auto "your query"   # Automatically routes to solve / turbo / flash
```

**Routing logic:** problem complexity → `solve`, research depth → `turbo`, simple question → `flash`.

---

## 6. Parallel Factory (Advanced)

```bash
blast turbofactory "materials science" --scale standard --max-concurrent 5
```

**What happens:**
- Spawns N parallel pipelines (solve + turbo + mixed)
- Auto-selects scale: `mini` (3 pipelines) → `standard` (5) → `mega` (10) → `giga` (20)
- Aggregates results, ranks hypotheses, generates comparative report
- Budget-aware: stops if estimated cost exceeds threshold

---

## 7. MCP Server (for AI Agents)

```bash
blast serve --mcp
```

Exposes 20 tools: `c4_solve`, `c4_search`, `c4_triz`, `c4_verify`, `c4_simulate`, `c4_causal`, `blast_solve`, `blast_turbo`, `blast_turbofactory`, etc.

---

## Next Steps

- [Who can use C4REQBER?](docs/RESEARCH_AUDIENCES.md) — detailed guide for 11 research audiences with example studies
- [GPU Setup](docs/GPU_SETUP.md) — use local CUDA/Metal or vast.ai
- [Architecture](ARCHITECTURE_C4R.md) — understand the system
- [Plugins](docs/) — extend with custom cognitive operators
