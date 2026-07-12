# MCP Server Tool Registry

> **Last regenerated:** 2026-06-22 03:10 UTC
> **Source of truth:** this file is regenerated from `@server.tool` decorators in
> `src/mcp_server/server.py` + `src/codegen/mcp_tool.py`. To update, run
> `python3 scripts/gen_mcp_registry.py` (or `--check` in CI).

**Total tools: 21**

## Tools

| # | Tool name | Parameters | Description |
|---|-----------|------------|-------------|
| 1 | `blast_auto` | `query: str` | Auto-route query to best BLAST mode and execute it. |
| 2 | `blast_flash` | `question: str, with_sources: bool = False, deep: bool = False` | Run BLAST flash mode — quick LLM answer with optional USP cognitive analysis. |
| 3 | `blast_solve` | `problem: str, output_format: str = "auto", domain: str \| None = None` | Run BLAST solve mode — produces strategic artifacts (PRD, plan, blueprint, code). |
| 4 | `blast_turbo` | `topic: str, verify_backend: str = "hybrid", functors: bool = True` | Run BLAST turbo mode — generates paradigm-shifting research proposal (A+ quality). |
| 5 | `blast_turbofactory` | `domain: str, scale: str = "standard", max_concurrent: int = 5, pipeline_mode: str = "mixed"` | Run BLAST turbofactory mode — parallel paradigm factory (5-100 pipelines). |
| 6 | `c4_autoresearch` | `file: str,
    metric: str = "val_bpb",
    max_iter: int = 100,` | Run Karpathy-style iterative autoresearch loop on a Python training file. |
| 7 | `c4_bayesian` | `models: dict[str, float], samples: int = 1000` | Run Bayesian inference (MCMC/BMA) on competing models. |
| 8 | `c4_causal` | `nodes: list[dict[str, Any]], treatment: str, outcome: str` | Perform causal discovery using do-calculus on SCM. |
| 9 | `c4_chain` | `problem: str,
    from_state: list[int] \| None = None,
    to_state: list[int] \| None = None,` | Compute C4 discovery chain (Theorem 11: ≤6 steps between any two states). |
| 10 | `c4_codegen` | `specification: str,
    language: str = "python",
    verify: bool = True,
    optimization_target: str \| None = None,` | Generate code from a natural language specification, then optionally verify it. |
| 11 | `c4_export` | `discovery: dict[str, Any], format: str = "markdown"` | Export discovery to LaTeX/Markdown/JSON/HTML/PDF/BibTeX. |
| 12 | `c4_fingerprint` | `problem: str` | Classify problem to C4 state (Z₃³ cube coordinates) with C4 → GapAnalyzer ABC resolution scoring. |
| 13 | `c4_meta` | `reasoning_trace: str, depth: int = 2` | Meta-cognitive reflection on reasoning quality and path optimization. |
| 14 | `c4_prove` | `hypothesis: str, language: str = "lean4"` | Prove a hypothesis using LLM-based formal proof generation + iterative error correction. |
| 15 | `c4_search` | `query: str, sources: list[str] \| None = None` | Search across 33 knowledge sources via orchestrator.py (arXiv, PubMed, ORCID, etc.). |
| 16 | `c4_simulate` | `pattern_id: str, hypothesis: dict[str, Any]` | Run physics simulation on any of 5 GPU engines (Newton, TorchSim, JaxSim, Schr, vast.ai). |
| 17 | `c4_social` | `action: str, draft_id: str = "", platform: str = ""` | Social publishing — preprint upload, post to platforms, health check. |
| 18 | `c4_solve` | `problem: str, domain: str = "science"` | Run 12-stage discovery pipeline with observer, final verifier, redundant gates. |
| 19 | `c4_transfer` | `problem: str, source_domain: str, target_domain: str` | Execute cross-domain structural isomorphism transfer. |
| 20 | `c4_triz` | `improving: int = 1,
    worsening: int = 2,
    mode: str = "matrix",
    problem: str = "",` | Resolve contradiction using TRIZ tools. |
| 21 | `c4_verify` | `code: str, language: str \| None = None` | Verify formal proof in lean4, coq, dafny, agda, z3, hoare, cvc5, tla, or alloy. |

## Verification

```bash
# Count @server.tool decorators
grep -c "@server.tool(" src/mcp_server/server.py src/codegen/mcp_tool.py

# Run integration smoke test (every tool returns a structured dict)
blast serve --mcp  # then connect with any MCP client
```

## Schema registry

JSON Schemas for inputs/outputs live in `src/mcp_server/tool_schemas.py`
(`INPUT_SCHEMAS`, `OUTPUT_SCHEMAS`). The fallback server reads `tool_func.schema`
when the SDK is unavailable; `c4_codegen` was added in audit 2026-06-22
(see `audit/MASTER_AUDIT_2026-06-22.md`).
