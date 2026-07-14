# TEST FIX PLAN — 2,768 failures, 153 errors → 0

Generated 2026-05-19 after full hardening audit. All 0 collection errors — failures are runtime.

## Failure Breakdown by Root Cause

### Category 1: Old v6/v7 API Tests (320 failures)
**Files:** test_v6_complete.py (130), test_v6_router_full.py (128), test_v6_router.py (70), test_routers_complete.py (70)
**Root cause:** Tests import removed v7 router code and mock/stub v6 endpoints. After hardening, v7 API removed from server.py, v6 routes changed.
**Fix:** Delete. These test deprecated APIs that no longer exist. v8 is the canonical API.
- `rm tests/api/test_v6_complete.py tests/api/test_v6_router_full.py tests/api/test_v6_router.py tests/api/test_routers_complete.py`

### Category 2: Old Pipeline Tests (112 failures)
**Files:** test_pipeline_full.py (80), test_agents.py (32)
**Root cause:** Tests import deleted modules (synthesis_fallback, old pipeline executor). Pipeline architecture changed.
**Fix:** Delete or rewrite to test against new pipeline API.
- `rm tests/agents/test_pipeline_full.py` (references removed modules)
- `tests/agents/test_agents.py` — rewrite to test against AgentCore.process() instead of old API

### Category 3: Network-Dependent Tests (~150 failures)
**Files:** test_semantic_scholar.py (34+31), test_orcid_client.py (25), test_mega_db_extended.py (33), test_mega_db.py (27), test_pubmed_client.py, test_openalex_client.py, test_arxiv_client_extended.py
**Root cause:** Tests make real HTTP calls to external APIs without API keys. Time out or return 401.
**Fix:** Add `@pytest.mark.skipif(not os.getenv("API_KEYS_CONFIGURED"))` or mark as integration tests requiring env. Or delete — these test connectivity, not logic.

### Category 4: AST/Module API Removals (~50 failures)
**Files:** test_calculator.py (34)
**Root cause:** `ast.Num` removed in Python 3.14. Test uses old AST API.
**Fix:** Already fixed — replaced `ast.Num` with `ast.Constant`. Need to verify remaining failures.

### Category 5: Missing Dependencies (~40 failures)
**Files:** test_cache_tiered.py (26), test_cache.py (36), test_database.py (25)
**Root cause:** Tests require Redis/PostgreSQL not configured in test env.
**Fix:** Add `@pytest.mark.skipif` checks or mock the connection.

### Category 6: Snapshot/Mock Mismatch (~300 failures)
**Files:** test_codegen.py (26), test_agents/test_functor_orchestrator.py (28), test_llm/test_router.py (24), test_patterns/runner.py (24), test_discovery_utils.py (25), test_auth.py (24+25), test_knowledge/sources.py (25)
**Root cause:** Tests expect old mock/stub behavior. After hardening, functions return real errors instead of mock data.
**Fix:** Rewrite tests to match new behavior — functions now raise errors when LLM unavailable, don't return fallback data.

### Category 7: Patterns Library (~500 failures)
**Files:** All files under tests/patterns/library/
**Root cause:** Pattern simulation tests require heavy dependencies (PySpice, OpenFOAM, LAMMPS, etc.) not installed.
**Fix:** Add `@pytest.mark.skipif` for each pattern requiring uninstalled dependencies.

### Category 8: WASM Stub Tests (~10 failures)
**Files:** test_wasm_runtime.py
**Root cause:** Tests exercise WASM stub mode. Stub behavior changed.
**Fix:** Update test expectations to match new stub API.

### Category 9: 153 Errors (misc)
**Root cause:** Mix of missing env vars (JWT_SECRET, API keys), import errors from changed module paths, fixture setup failures.
**Fix:** Per-file fixes — mostly add `os.environ.setdefault` or skipif markers.

---

## Execution Plan (in order)

### Phase 1 — Delete Tests for Removed APIs (340 failures gone)
- [ ] `rm tests/api/test_v6_complete.py tests/api/test_v6_router_full.py tests/api/test_v6_router.py tests/api/test_routers_complete.py`
- [ ] `rm tests/agents/test_pipeline_full.py`

### Phase 2 — Skip Network Tests (150 failures → skipped)
- [ ] Add `pytestmark = pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="Requires API key")` to: test_semantic_scholar.py, test_orcid_client.py, test_mega_db_extended.py, test_mega_db.py, test_pubmed_client.py, test_openalex_client.py, test_arxiv_client_extended.py

### Phase 3 — Rewrite Mock-Dependent Tests (400 failures → pass)
- [ ] test_codegen.py — update to expect RuntimeError instead of mock response
- [ ] test_agents/test_functor_orchestrator.py — update to use AsyncMock instead of deleted AsyncMockLLMClient
- [ ] test_llm/test_router.py — update to expect errors instead of fallback responses
- [ ] test_patterns/runner.py — update assertions for changed API
- [ ] test_discovery_utils.py — remove _fallback_papers references
- [ ] test_auth.py — add JWT_SECRET setup
- [ ] test_knowledge/sources.py — remove Google Scholar tests, fix adapter imports

### Phase 4 — Skip Missing Dependency Tests (500 failures → skipped)
- [ ] Add skipif for each patterns/library test requiring external deps (PySpice, OpenFOAM, LAMMPS, Vina, etc.)
- [ ] Add skipif for Redis/PostgreSQL in cache/database tests

### Phase 5 — Fix 153 Errors
- [ ] Add JWT_SECRET to test env setup
- [ ] Fix fixture imports for changed module paths
- [ ] Handle remaining env-dependent test errors

### Estimated Effort
- Phase 1: 2 min (file deletion)
- Phase 2: 10 min (add skipif decorators)  
- Phase 3: 20 min (rewrite assertion logic)
- Phase 4: 15 min (dependency skipif)
- Phase 5: 15 min (per-file fixes)
- **Total: ~60 min**

### Target
- After Phase 1: ~2,430 failures
- After Phase 2: ~2,280 failures  
- After Phase 3: ~1,880 failures
- After Phase 4: ~1,380 failures
- After Phase 5: 0 errors, <200 failures
- Remaining <200 are deep logic bugs requiring individual investigation
