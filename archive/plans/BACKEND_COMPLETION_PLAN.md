# TURBO-CDI Backend Completion Plan
# Version: v6.5-completion
# Date: 2026-04-24
# Status: Professional implementation roadmap

================================================================================
PHASE 1: CRITICAL LLM INFRASTRUCTURE (Week 1)
================================================================================

1.1 MULTI-PROVIDER LLM ROUTER [HIGH PRIORITY]
    Current: Only OpenRouter supported. XAI, Mistral, Moonshot, DeepSeek keys exist in .env but unused.
    Problem: AsyncLLMClient hardcodes OpenRouter base_url. No provider abstraction.
    
    Implementation:
    - Create src/llm/providers/ package with base class LLMProviderBase
    - Implement: OpenRouterProvider, XAIProvider, MistralProvider, MoonshotProvider, DeepSeekProvider
    - Each provider handles its own base_url, auth headers, response parsing
    - ProviderRouter updated to route by model prefix (e.g., "xai/grok-2" -> XAI, "mistral/..." -> Mistral)
    - Fallback chain: Primary -> Secondary -> Local -> Mock
    
    Files to modify:
    - src/llm/async_client.py (refactor to use provider plugins)
    - src/llm/provider_router.py (add new providers to presets)
    - src/llm/providers/__init__.py (new)
    - src/llm/providers/base.py (new)
    - src/llm/providers/openrouter.py (new)
    - src/llm/providers/xai.py (new)
    - src/llm/providers/mistral.py (new)
    - src/llm/providers/moonshot.py (new)
    - src/llm/providers/deepseek.py (new)

1.2 MODEL REGISTRY [HIGH PRIORITY]
    Current: MODELS dict in async_client.py with 4 hardcoded models.
    Problem: No centralized model catalog. No cost tracking. No context window awareness.
    
    Implementation:
    - Create src/llm/models_registry.py with ModelInfo dataclass
    - Fields: id, provider, context_window, cost_per_1k_input, cost_per_1k_output, capabilities[]
    - Register all available models from all 5 providers
    - Auto-select model by task + budget constraints

================================================================================
PHASE 2: TRIZ SYSTEM COMPLETION (Week 1-2)
================================================================================

2.1 FULL 40 PRINCIPLES DATABASE [HIGH PRIORITY]
    Current: bridge.py has all 40 principles defined (TRIZ_PRINCIPLES dict lines 81-371)
    Status: COMPLETE on backend
    Problem: Frontend Triz.tsx only shows 9 principles (lines 10-20)
    
    Frontend fix needed:
    - web-v2/src/pages/Triz.tsx: Replace TRIZ_PRINCIPLES array with API call to /bridge/principles
    - Or at minimum expand to all 40 principles with full descriptions

2.2 FULL CONTRADICTION MATRIX (39x39) [HIGH PRIORITY]
    Current: contradiction_matrix.py has only ~25 entries (classic_data lines 124-162)
    Problem: Classic TRIZ matrix has ~1200 cells. Current coverage <2%.
    
    Implementation:
    - Load full matrix from data file (JSON/YAML) instead of hardcoding
    - Source: Altshuller's original matrix or modernized version
    - File: data/triz_contradiction_matrix.json
    - Structure: {"improve": N, "worsen": M, "principles": [p1, p2, p3, p4]}
    - Add matrix cell lookup API: /bridge/matrix/{improve}/{worsen}
    - Add parameter name resolution (39 engineering parameters)

2.3 76 STANDARD SOLUTIONS [MEDIUM PRIORITY]
    Current: Not implemented
    Implementation: Add StandardSolution dataclass + database

2.4 ARIZ-85C [MEDIUM PRIORITY]
    Current: Not implemented
    Implementation: Step-by-step ARIZ algorithm with LLM assistance

================================================================================
PHASE 3: ANALOGY ENGINE — STRUCTURAL VS SEMANTIC (Week 2)
================================================================================

3.1 CURRENT STATE ANALYSIS
    Current analogy/engine.py implements:
    - Semantic: Sentence-BERT/TF-IDF cosine similarity (surface-level)
    - Structural: Word2Vec vector arithmetic (A:B::C:D) - requires pre-trained model
    - Knowledge-based: Hardcoded conceptual metaphors (570 mappings)
    - Graph-based: Knowledge graph lookup (empty on startup)
    
    Problem: No true structural analogy discovery. Semantic similarity != structural isomorphism.

3.2 STRUCTURAL ANALOGY DISCOVERY [HIGH PRIORITY]
    Implementation:
    - Domain representation: Extract relational structure from text using LLM
    - Prompt: "Extract entities and relations from: {text}. Format: JSON with nodes[] and edges[]"
    - Graph matching: Use NetworkX graph_edit_distance or subgraph isomorphism
    - Attribute matching: Compare node degrees, centrality, clustering coefficients
    - Path matching: Find similar causal chains A->B->C vs X->Y->Z
    
    New file: src/analogy/structural.py
    Classes:
    - DomainGraphExtractor (LLM-based entity/relation extraction)
    - StructuralMatcher (graph isomorphism + edit distance)
    - CausalChainMapper (path-based analogy)

3.3 LLM-POWERED ANALOGY GENERATION [HIGH PRIORITY]
    Current: Relies on pre-defined conceptual metaphors
    Problem: Can't discover novel analogies
    
    Implementation:
    - Prompt engineering for cross-domain analogy generation
    - "Given domain A with structure {graph_A}, find analogous structure in domain B"
    - Use strongest LLM (Claude Sonnet) for synthesis step
    - Cache discovered analogies in knowledge graph

3.4 ANCHOR-BASED ANALOGY [MEDIUM PRIORITY]
    Implementation:
    - User provides known analogy: "neuron is like a node in a network"
    - System generalizes: "What else in biology maps to CS concepts?"
    - Uses Word2Vec with domain-specific embeddings

================================================================================
PHASE 4: PRIOR ART SEARCH ENGINE (Week 2-3)
================================================================================

4.1 CURRENT STATE
    File: src/integrations/prior_art.py
    Current: Empty implementation (not found in codebase — likely missing)
    Pipeline references it but it returns mock data

4.2 IMPLEMENTATION [HIGH PRIORITY]
    Sources to integrate:
    - arXiv: API exists (src/adapters/arxiv_adapter.py)
    - Semantic Scholar: API exists (src/search/semantic_scholar.py)
    - PubMed: API exists (src/adapters/pubmed_adapter.py)
    - Patents: Google Patents / USPTO / EPO
    - CrossRef / OpenAlex
    
    New file: src/integrations/prior_art.py
    Classes:
    - PriorArtSearchEngine
    - Methods: search(query, sources[], max_results, year_range)
    - Result deduplication by DOI/title similarity
    - Relevance ranking: semantic similarity + citation count + recency
    - Caching: Redis/memory with 1h TTL

4.3 SEMANTIC SEARCH [HIGH PRIORITY]
    Implementation:
    - Embed query using same model as papers
    - Vector similarity search against indexed papers
    - Index: FAISS or Annoy for fast nearest neighbors
    - Re-index on new paper ingestion

================================================================================
PHASE 5: PIPELINE HARDENING (Week 3)
================================================================================

5.1 DISCOVERY PIPELINE [HIGH PRIORITY]
    Current: Discover.tsx is a mock (setTimeout + hardcoded results)
    Fix: Connect to real backend endpoints
    - Option A: Use /discover (one_shot_solver)
    - Option B: Use /v6/solve/stream (full pipeline with SSE)
    - Option C: Use WebSocket /ws/{client_id} with discovery_stream
    
    Recommended: Option B with streaming for real-time progress

5.2 PIPELINE STAGE ENHANCEMENTS [MEDIUM PRIORITY]
    - C4 Fingerprint: Currently keyword-based. Upgrade to LLM-based classification.
    - MP Rotation: Currently template-based. Upgrade to LLM-generated perspectives.
    - Isomorphism Search: Integrate structural analogy engine.
    - Synthesis: Ensure LLM always called (currently falls back to template).
    - Validation: Upgrade from word-overlap to LLM-based critique.

5.3 ERROR HANDLING & RESILIENCE [HIGH PRIORITY]
    - Circuit breaker for LLM APIs (fail fast after N errors)
    - Graceful degradation: if synthesis fails, return best prior art
    - Timeout per stage: 30s max per step
    - Retry with exponential backoff

================================================================================
PHASE 6: SECONDARY SYSTEMS (Week 3-4)
================================================================================

6.1 FEDERATED DISCOVERY [MEDIUM PRIORITY]
    Current: Mock peers (peer-1, peer-2) in v6_router.py:1073-1090
    Implementation:
    - Define peer discovery protocol (mDNS or registry)
    - HTTP API for cross-instance query
    - Result aggregation with confidence weighting
    - Or remove feature if not needed

6.2 PLUGIN REGISTRY [MEDIUM PRIORITY]
    Current: src/plugins/registry.py — empty plugin list
    Implementation:
    - Define plugin interface (metamodel extensions)
    - Load plugins from plugins/ directory
    - Hot-reload capability
    - Or remove feature if not needed

6.3 AUTO-EXPERIMENT DESIGN [MEDIUM PRIORITY]
    Current: Template-based generation in v6_router.py:1098-1122
    Implementation:
    - LLM-powered experiment design from solution
    - Generate: hypothesis, variables, metrics, methodology, controls
    - A/B test structure generation
    - Export to standard formats (JSON, CSV)

6.4 KNOWLEDGE GRAPH SEEDING [MEDIUM PRIORITY]
    Current: Empty on startup
    Implementation:
    - Seed with default domains and concepts
    - Auto-populate from discoveries
    - Periodic snapshot to disk

================================================================================
PHASE 7: TESTING & VALIDATION (Week 4)
================================================================================

7.1 UNIT TESTS
    - Each provider: mock HTTP responses
    - TRIZ matrix: verify all 39x39 cells have data
    - Analogy engine: test structural vs semantic separation
    - Pipeline: test each stage independently

7.2 INTEGRATION TESTS
    - End-to-end discovery flow
    - LLM fallback chain
    - Rate limiting under load

7.3 BENCHMARKS
    - Pipeline latency per stage
    - LLM cost per request
    - Cache hit rates

================================================================================
IMPLEMENTATION PRIORITY MATRIX
================================================================================

P0 (Critical - Blockers):
[ ] Multi-provider LLM router (XAI, Mistral, Moonshot, DeepSeek)
[ ] Connect Discover page to real pipeline
[ ] Full TRIZ contradiction matrix (39x39)
[ ] Prior Art Search Engine implementation

P1 (High - Core functionality):
[ ] Structural analogy discovery (graph-based)
[ ] LLM-powered C4 fingerprinting
[ ] LLM-powered MP rotation
[ ] Pipeline error handling & resilience

P2 (Medium - Enhancements):
[ ] 76 TRIZ Standard Solutions
[ ] Federated Discovery (real peers or remove)
[ ] Plugin Registry (real plugins or remove)
[ ] Auto-Experiment Design (LLM-powered)
[ ] Knowledge Graph seeding

P3 (Low - Polish):
[ ] ARIZ-85C implementation
[ ] Advanced caching strategies
[ ] Performance benchmarks
[ ] Documentation

================================================================================
ESTIMATED TIMELINE
================================================================================

Week 1: Phase 1 (LLM Infrastructure) + Phase 2 (TRIZ)
Week 2: Phase 3 (Analogy) + Phase 4 (Prior Art)
Week 3: Phase 5 (Pipeline) + Phase 6 (Secondary)
Week 4: Phase 7 (Testing) + Bug fixes

Total: 4 weeks for full backend completion
Minimum viable: 2 weeks (P0 items only)
