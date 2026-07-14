# C4REQBER v5.4.0 — Comprehensive QA Test Plan

**Date:** 2026-05-20 | **Tester:** Kilo (DeepSeek V4 Pro)
**Environment:** macOS Apple Silicon M1+, Python 3.14, 15/15 packages, 5/5 WASM plugins
**API Budget:** OpenRouter $7.79, DeepSeek $8.91, xAI $15.00

---

## System Status Pre-Test

| Component | Status | Notes |
|-----------|--------|-------|
| Unit tests (pytest) | 5,640 passed, 0 failed, 1,101 skipped | ✅ |
| API keys | 6 keys in `.env.dontredact` | ✅ |
| Packages | 15/15 installed (10 native + 5 isolated 3.12) | ✅ |
| LM Studio | Server ON, 23 models, DeepSeek R1 Qwen3 8B loaded | ✅ |
| MLX | Apple Silicon, 21 models cached | ✅ |
| WASM Runtime | wasmtime+WASI, 5 compiled plugins | ✅ |
| ChromaDB | v1.5.9 installed, 4 collections | ✅ |
| FastMCP | Installed, agent bridge wired | ✅ |
| OpenMM | v8.5.1 installed | ✅ |

---

## Phase 1: Pipelines — Critical User Path (12 tests, ~$1.80)

Diverse real-world queries across all 4 pipeline modes + auto-dispatch.

| # | Query | Mode | Domain | Acceptance Criteria |
|---|-------|------|--------|---------------------|
| 1.1 | `blast solve "why is the sky blue"` | solve | Physics/Optics | All 10 UniversalSolvePipeline steps executed, output non-empty |
| 1.2 | `blast solve "how to reduce employee turnover in tech companies"` | solve | Business/HR | Social-economic domain, structured output |
| 1.3 | `blast turbo "sleep and memory consolidation in mammals" --competing 2 --no-iterative` | turbo | Neuroscience | Phases A→G passed, dissertation saved, simulation+verification green |
| 1.4 | `blast turbo "nuclear fusion reactor materials science" --competing 1 --no-iterative` | turbo | Materials Science | Engineering domain, quality report filled |
| 1.5 | `blast flash "what is CRISPR gene editing"` | flash | Biology | LLM answer non-empty |
| 1.6 | `blast flash "explain blockchain consensus mechanisms"` | flash | CS/Crypto | Technical explanation returned |
| 1.7 | `blast turbofactory "climate change mitigation strategies" --scale mini --max-concurrent 2` | turbofactory | Ecology | 5 sub-problems generated, ≥3 pipelines successful, report saved |
| 1.8 | `blast turbofactory "AI safety research directions" --scale mini --pipeline solve --max-concurrent 2` | turbofactory | AI Safety | Pure solve mode, no PipelineConfig crash |
| 1.9 | `blast turbofactory "quantum computing applications" --scale mini --pipeline turbo --max-concurrent 2` | turbofactory | Quantum | Pure turbo mode, quality distribution table |
| 1.10 | `blast analyze "supply chain resilience after pandemic"` | analyze | Logistics | entities≥3, dependency_graph, critical_path, C4 state non-empty |
| 1.11 | `blast auto "cancer early detection methods"` | auto | Medicine | Auto-routed to correct mode, pipeline executed |
| 1.12 | `blast auto "post-quantum cryptography standards"` | auto | Cryptography | Auto-routed, output produced |

---

## Phase 2: CLI Commands — Full Surface (19 tests, ~$0.10)

| # | Command | What we test |
|---|---------|-------------|
| 2.1 | `blast solve "test" --mode autopilot --format auto` | --mode, --format flags |
| 2.2 | `blast turbo "test" --verify-backend z3 --functors --no-iterative` | --verify-backend, --functors, --no-iterative |
| 2.3 | `blast flash "test" --with-sources --format concise` | --with-sources, --format |
| 2.4 | `blast analyze "test system"` | SystemAnalyzer: entities, deps, C4 state |
| 2.5 | `blast turbofactory "test" --scale mini --max-concurrent 1 --pipeline mixed` | All flags |
| 2.6 | `blast serve --mcp` (Ctrl+C after 3s) | Start + graceful shutdown |
| 2.7 | `blast agent --cmd "what is a p-value"` | AgentCore.process() → AgentResponse |
| 2.8 | `blast agent --config` | Config output: history_path, system_prompt, MCP servers |
| 2.9 | `blast packages` | 15 rows, all ✅ installed |
| 2.10 | `blast integrations status` | 5 providers with healthy/unhealthy |
| 2.11 | `blast integrations test` | Connection tests for all |
| 2.12 | `blast models` | ≥12 LLM providers listed |
| 2.13 | `blast config --show` | Current pipeline configuration |
| 2.14 | `blast setup --auto` | No errors, 15/15 installed |
| 2.15 | `blast modes` | Mode list displayed |
| 2.16 | `blast wasm-load wasm/plugins/monte_carlo_pi.wasm` | Loads, registers, shows exports |
| 2.17 | `blast wasm-list` | 5 modules with execute function |
| 2.18 | `blast wasm-execute modular_math execute 42 100` | Returns 23 |
| 2.19 | `blast social status` | Honest unavailable (no social keys) |
| 2.20 | `blast soul` / `blast policy` / `blast qa` / `blast guardian` | No traceback |
| 2.21 | `blast tui --packages` (Ctrl+C after 2s) | TUI starts without crash |

---

## Phase 3: MCP Server — Tool Validation (7 tests, ~$0.05)

| # | MCP Tool | Input | Acceptance |
|---|----------|-------|------------|
| 3.1 | `tools/list` | — | 21 tools with JSON Schema inputSchema |
| 3.2 | `c4_fingerprint` | `{"problem": "quantum computing"}` | C4 state tuple returned |
| 3.3 | `c4_search` | `{"query": "gravity"}` | Papers list returned |
| 3.4 | `c4_triz` | `{"contradiction": ["speed","weight"]}` | TRIZ principles returned |
| 3.5 | `c4_verify` | `{"code":"x=1","backend":"z3"}` | Verification result |
| 3.6 | `blast_turbofactory` | `{"domain":"test","scale":"mini","max_concurrent":1}` | Pipeline result |
| 3.7 | `blast_solve` | `{"problem":"test"}` | Solve result returned |

---

## Phase 4: Integrations & Bridges (6 tests, ~$0.01)

| # | Component | Test | Acceptance |
|---|-----------|------|------------|
| 4.1 | LM Studio CLI | `lms status` | Server ON, model loaded |
| 4.2 | MLX Provider | `generate("Hello")` → LLMResponse | content non-empty |
| 4.3 | ChromaDB | `add_knowledge` + `search_knowledge` roundtrip | Results returned |
| 4.4 | FastMCP | `discover_servers()` | Returns list from .mcp.json |
| 4.5 | OpenMM | `simulate_protein(pdb_id="1CRN", steps=10)` | Energy + coords returned |
| 4.6 | PyMC MCMC | POST `/bayesian/pymc_mcmc` | Backend=pyMC or fallback |

---

## Phase 5: Edge Cases & Robustness (5 tests, ~$0.02)

| # | Test | Command | Expected |
|---|------|---------|----------|
| 5.1 | Empty input | `blast solve ""` | Error message, no crash |
| 5.2 | Non-existent command | `blast nonexistent` | Help text |
| 5.3 | Zero competing hypotheses | `blast turbo "test" --competing 0 --no-iterative` | Pipeline completes gracefully |
| 5.4 | High concurrency | `blast turbofactory "test" --scale mini --max-concurrent 10` | No crash, semaphore works |
| 5.5 | Unset API key | `unset OPENROUTER_API_KEY; blast flash "test"` | Honest error, no crash |

---

## Phase 6: WASM Pipeline Integration (3 tests, ~$0)

| # | Test | Acceptance |
|---|------|------------|
| 6.1 | Load all 5 wasm plugins | monte_carlo_pi (51), matrix_mult (17), text_distance (47), hash_fingerprint (62), modular_math (23) |
| 6.2 | Execute with different params | `modular_math.execute(7, 13)` ≠ `execute(42, 100)` |
| 6.3 | Plugin registry check | Plugins registered in `PLUGIN_REGISTRY` after wasm-load |

---

## Summary

| Metric | Value |
|--------|-------|
| Total tests | **46** |
| Phases | 6 |
| Estimated duration | ~35 minutes |
| Estimated API cost | ~$1.98 (DeepSeek $0.14/MTok + OpenRouter $0.35/MTok) |
| Pages of text generated | ~50-100 pages (dissertations + reports) |
| WASM plugins tested | 5/5 |
| CLI commands tested | 19/19 |
| Diverse domains tested | 12 (physics, business, neuroscience, materials, biology, CS, ecology, AI safety, logistics, medicine, cryptography, sociology) |

---

**Ready to execute.** Type "go" to start.
