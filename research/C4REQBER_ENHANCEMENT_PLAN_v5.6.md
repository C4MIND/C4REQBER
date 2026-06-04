# C4REQBER Enhancement Plan v5.6
## Professional roadmap: from 2 active sources to 20+ verified sources with citation integrity and novelty detection

**Date:** 2026-05-29  
**Author:** C4REQBER Research Agent  
**Scope:** Source integration, rate limit compliance, citation verification, novelty detection  
**Impact:** Dissertation confidence ↑ 0.89 → 0.95+, real citation coverage ↑ 10 → 40+ sources, hallucination rate ↓ 40% → <5%

---

## 1. Executive Summary

C4REQBER currently generates dissertations with **real OpenAlex citations** (38 citations in discovery_06), but the underlying source layer is severely underutilized:

- **65 source adapters** exist in `src/knowledge/sources/`
- **Only 2–5 sources** are actively used in the production pipeline
- **Rate limits are outdated** — CrossRef changed limits in Dec 2025, Europe PMC is 1 RPS not 5
- **No citation verification** — references section exists but claims are not checked against sources
- **No novelty detection** — no objective metric for how "new" a proposed solution is
- **USPTO is broken** — PatentsView v1 returns 301 redirect
- **Pipeline uses legacy `PriorArtSearchEngine`** instead of the modern `MultiSourceSearcher`

This plan fixes all of the above in **4 phases over 2 weeks**, with **$0 incremental API cost** (all new sources are free).

---

## 2. Current State Audit

### 2.1 Source Adapter Inventory (65 total)

| Category | Count | Working | Used in Pipeline | Notes |
|----------|-------|---------|------------------|-------|
| **Tier 1 — Free, no key** | 22 | 18 | 2 | OpenAlex, CrossRef, arXiv, PubMed, Europe PMC, DBLP, DataCite, Zenodo, Figshare, DOAJ, INSPIRE-HEP, etc. |
| **Tier 2 — Free with key** | 8 | 4 | 1 | Brave (key ✅), CORE, BASE, Unpaywall, Lens.org, OA.mg (keys ❌) |
| **Tier 3 — Specialized / P6** | 25 | 15 | 0 | NCBI, PubChem, ChEMBL, Materials Project, ClinicalTrials, GBIF, OpenReview, etc. |
| **Tier 4 — Web / Social** | 6 | 4 | 0 | GitHub, SciMatic, arXiv.gg, RSCI, CyberLeninka, Math-Net.Ru |
| **Tier 5 — Broken / Deprecated** | 4 | 0 | 0 | USPTO PatentsView (301), Semantic Scholar (IP ban, no key) |

### 2.2 API Key Inventory

| Key | In `.env` | Used By | Status |
|-----|-----------|---------|--------|
| `BRAVE_API_KEY` | ✅ | Brave Search | Active |
| `DEEPSEEK_API_KEY` | ✅ | LLM synthesis | Active |
| `XAI_API_KEY` | ✅ | LLM mp_rotation | Active |
| `MISTRAL_API_KEY` | ✅ | LLM fallback | Active |
| `OPENROUTER_API_KEY` | ✅ | LLM fallback | Disabled (negative balance) |
| `SCHOLARA_API_KEY` | ✅ | Unknown | Legacy? |
| `SCIMATIC_API_KEY` | ✅ | SciMatic | SciMatic adapter needs_key=False, key unused |
| `CORE_API_KEY` | ❌ | CORE | **Missing — needed for OA full-text** |
| `UNPAYWALL_EMAIL` | ❌ | Unpaywall | **Missing — needed for OA PDF links** |
| `NCBI_API_KEY` | ❌ | NCBI E-utilities | **Missing — boosts PubMed from 3 to 10 RPS** |
| `MATERIALS_PROJECT_API_KEY` | ❌ | Materials Project | Missing |
| `HARVARD_DATAVERSE_API_KEY` | ❌ | Harvard Dataverse | Missing |
| `KAGGLE_USERNAME`/`KEY` | ❌ | Kaggle | Missing |
| `OPENFDA_API_KEY` | ❌ | OpenFDA | Missing |
| `NASA_EARTHDATA_TOKEN` | ❌ | NASA Earthdata | Missing |

### 2.3 Pipeline Architecture Gap

```
API Layer:        MultiSourceSearcher (50+ sources, dedup, cross-validation)
                      ↓  NOT USED BY PIPELINE
Pipeline Layer:   PriorArtSearchEngine (5 sources, no dedup)
                      ↓
Synthesis:        Step 08 — receives 10 sources max
```

**Problem:** `PipelineExecutor` initializes `PriorArtSearchEngine()` (line 131, `src/agents/pipeline.py`), but `multi_searcher` is left as `None`. The modern `MultiSourceSearcher` with 50+ sources, deduplication, and cross-validation is **only accessible via API v8 endpoints**, not the dissertation generation pipeline.

### 2.4 Rate Limit Compliance Issues

| Source | Registry Value | Actual Limit (verified 2026-05) | Risk |
|--------|---------------|--------------------------------|------|
| **CrossRef** | 50 RPS | **3 RPS** polite pool (Dec 2025 change) | 🔴 **High** — will be banned |
| **Europe PMC** | 5 RPS | **1 RPS** free tier | 🔴 **High** — will be banned |
| **arXiv** | 1 RPS | **0.33 RPS** (1 per 3 sec) | 🟡 Medium |
| **OpenAlex** | 10 RPS | 10 RPS with key, generous without | 🟢 OK |
| **PubMed** | 3 RPS | 3 RPS no key, 10 RPS with key | 🟢 OK |
| **DBLP** | 2 RPS | Unknown, servers unstable | 🟡 Medium |
| **Semantic Scholar** | 0.33 RPS | 100/5min no key, 5000/5min with key | 🟡 Awaiting key |

---

## 3. Phase 1: Pipeline Integration & Rate Limit Fix (Days 1–3)

### 3.1 Unify Pipeline Source Layer

**Goal:** Replace `PriorArtSearchEngine` with `MultiSourceSearcher` in the pipeline.

**Implementation:**
1. In `src/agents/pipeline.py` line 131, replace:
   ```python
   # OLD
   self.prior_art = PriorArtSearchEngine()
   self.multi_searcher = None
   
   # NEW
   from src.knowledge.orchestrator import MultiSourceSearcher
   self.prior_art = MultiSourceSearcher(
       sources={
           "openalex", "crossref", "pubmed", "europe_pmc",
           "dblp", "datacite", "zenodo", "figshare", "doaj",
           "inspire_hep", "arxiv",  # arxiv as fallback
       },
       max_concurrent=8,
       cache_enabled=True,
       cache_ttl=300.0,
   )
   ```

2. Update `PriorArtStep` (`step_02_prior_art.py`) to use `MultiSourceSearcher.search_all()`:
   ```python
   result = await self._prior_art.search_all(
       problem,
       max_per_source=10,
       include_web=False,
   )
   # Extract top 10 from result["papers"]
   ```

3. Delete or deprecate `PriorArtSearchEngine` — all its logic is superseded by `MultiSourceSearcher`.

**Impact:** Pipeline goes from 2 active sources to 10+ sources per query.

### 3.2 Fix Rate Limits in `SOURCE_REGISTRY`

File: `src/knowledge/config.py`

| Source | Current | New | Reason |
|--------|---------|-----|--------|
| `crossref` | `rate_limit: 50.0` | `rate_limit: 3.0` | Dec 2025 polite pool limit |
| `europe_pmc` | `rate_limit: 5.0` | `rate_limit: 1.0` | Free tier hard limit |
| `arxiv` | `rate_limit: 1.0` | `rate_limit: 0.33` | 1 per 3 seconds official |
| `semantic_scholar` | `rate_limit: 0.33` | `rate_limit: 0.33` | Correct (100/300s) |

Add `mailto` parameter to all CrossRef requests for polite pool access:
```python
# In crossref.py
params["mailto"] = "c44tcdi@example.com"
```

### 3.3 Add `tenacity` Retry Layer

Install: `pip install tenacity`

Wrap all `_get_with_retry()` and direct `httpx` calls with exponential backoff:
```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=1, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError)),
    reraise=True,
)
async def _fetch(self, url, params=None):
    ...
```

**Priority adapters to wrap:**
- `openalex.py` — primary source
- `crossref.py` — rate limit sensitive
- `europe_pmc.py` — rate limit sensitive
- `pubmed.py` — NCBI intermittently unstable
- `dblp.py` — servers unstable

### 3.4 Add Circuit Breaker

Per-source circuit breaker in `MultiSourceSearcher`:
```python
class CircuitBreaker:
    def __init__(self, threshold=3, timeout=300):
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = None

    def can_call(self):
        if self.failures < self.threshold:
            return True
        if time.time() - self.last_failure > self.timeout:
            self.failures = 0
            return True
        return False
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
```

If a source fails 3 times in a row (429, 5xx, timeout), skip it for 5 minutes. Prevents ban escalation and speeds up pipeline.

---

## 4. Phase 2: Source Expansion & Key Acquisition (Days 4–6)

### 4.1 Activate Key-Required Sources (Free Keys)

| Source | Key Name | Where to Get | Time | Value |
|--------|----------|--------------|------|-------|
| **CORE** | `CORE_API_KEY` | [core.ac.uk/services/api](https://core.ac.uk/services/api) | 5 min | 10M+ OA full-texts |
| **Unpaywall** | `UNPAYWALL_EMAIL` | [unpaywall.org/products/api](https://unpaywall.org/products/api) | 2 min | 40M+ OA PDF links |
| **NCBI** | `NCBI_API_KEY` | [ncbi.nlm.nih.gov/account](https://ncbi.nlm.nih.gov/account) | 5 min | Boost PubMed to 10 RPS |
| **OpenAlex** | `OPENALEX_API_KEY` | [openalex.org/settings/api](https://openalex.org/settings/api) | 2 min | 100K req/day, priority pool |

**Action:** Add these keys to `.env` and enable sources in `SOURCE_REGISTRY`:
```python
"core": {"enabled": True, ...},
"unpaywall": {"enabled": True, ...},
"ncbi_eutils": {"enabled": True, ...},
```

### 4.2 Integrate `pyalex` for OpenAlex

Replace custom `OpenAlexAdapter` with `pyalex` (MIT license, production-grade):

```bash
pip install pyalex
```

```python
from pyalex import Works

class OpenAlexAdapter(BaseSourceAdapter):
    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        works = Works().search(query).sort("cited_by_count", desc=True).get(limit)
        return [
            {
                "id": w.get("doi", w.get("id", "")),
                "title": w.get("title", ""),
                "authors": [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])],
                "year": w.get("publication_year", 0),
                "abstract": w.get("abstract", ""),  # pyalex reconstructs inverted index
                "doi": w.get("doi", ""),
                "url": f"https://doi.org/{w['doi']}" if w.get("doi") else w.get("id", ""),
                "citation_count": w.get("cited_by_count", 0),
                "source": "openalex",
            }
            for w in works
        ]
```

**Benefits:**
- Automatic abstract reconstruction from inverted index
- Built-in pagination
- Semantic similarity: `Works().similar("text").get()`
- Typed Pydantic responses
- Handles rate limit headers

### 4.3 Fix USPTO with `patent_client`

Replace broken `UsptoPatentsviewClient` / `PatentSearchClient`:

```bash
pip install patent_client
```

```python
from patent_client import Patent

async def search_patents(query: str, limit: int = 10) -> list[dict[str, Any]]:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: list(Patent.objects.filter(
            title=query,
            issue_date__gt="2010-01-01",
        ).values("publication_number", "title", "abstract", "description")[:limit])
    )
    return [
        {
            "id": r["publication_number"],
            "title": r["title"],
            "abstract": r.get("abstract", ""),
            "url": f"https://patents.google.com/?q={r['publication_number']}",
            "source": "uspto",
        }
        for r in result
    ]
```

**Update `SOURCE_REGISTRY`:** Change `uspto_patentsview` URL from `https://api.patentsview.org` to note that `patent_client` uses live USPTO databases.

### 4.4 Add Domain-Aware Source Selection

Currently the pipeline queries the same sources regardless of domain. Add domain-to-source mapping:

```python
DOMAIN_SOURCES = {
    "medicine": {"pubmed", "europe_pmc", "clinicaltrials", "openfda"},
    "biology": {"pubmed", "europe_pmc", "ncbi_eutils", "pubchem", "string_db", "gbif"},
    "computer_science": {"dblp", "openreview", "arxiv", "openalex"},
    "physics": {"inspire_hep", "arxiv", "openalex"},
    "chemistry": {"pubchem", "chembl", "openalex"},
    "materials_science": {"materials_project", "aflow", "openalex"},
    "neuroscience": {"pubmed", "allen_brain", "openalex"},
    "mathematics": {"mathnet_ru", "arxiv", "openalex", "oeis"},
    "general": {"openalex", "crossref", "pubmed", "dblp", "datacite"},
}
```

In `MultiSourceSearcher.__init__`, if `domain` is provided, prioritize domain-specific sources.

---

## 5. Phase 3: Citation Verification & Quality (Days 7–9)

### 5.1 Implement `CitationVerifier`

New module: `src/knowledge/citation_verifier.py`

**Algorithm:**
1. Extract all `[N]` citations from synthesis output
2. For each citation, extract title/DOI from the References section
3. Verify against 2+ independent sources:
   - CrossRef DOI lookup (`https://api.crossref.org/works/{doi}`)
   - OpenAlex title search
   - Semantic Scholar title search (when key arrives)
4. Assign verdict:

| Verdict | Condition |
|---------|-----------|
| `VERIFIED` | Found in ≥2 sources, metadata matches |
| `PARTIAL` | Found in 1 source, or metadata mismatch |
| `UNVERIFIED` | Not found in any source |
| `HALLUCINATED` | DOI doesn't resolve, title not found |

5. Replace unverifiable citations with `(proposed)` marker or remove `[N]` tag
6. Inject verification report into pipeline state

```python
class CitationVerifier:
    async def verify(self, dissertation_text: str, sources: list[dict]) -> VerificationReport:
        citations = self._extract_citations(dissertation_text)
        results = []
        for cit in citations:
            verified, verdict, found_in = await self._verify_single(cit)
            results.append({"citation": cit, "verdict": verdict, "sources": found_in})
        return VerificationReport(results)
```

**Integration point:** After synthesis (step s8), before returning result to user.

### 5.2 BibTeX Generation

```python
import requests

def doi_to_bibtex(doi: str) -> str | None:
    resp = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"},
        timeout=10,
        allow_redirects=True,
    )
    return resp.text if resp.status_code == 200 else None
```

Add to synthesis system prompt: "Generate BibTeX entries for all verified citations and append them to the References section."

---

## 6. Phase 4: Novelty Detection & Confidence v3 (Days 10–12)

### 6.1 Implement `NoveltyScorer`

New module: `src/knowledge/novelty_scorer.py`

**Algorithm (from SemNovel research, 50 lines):**
```python
from sentence_transformers import SentenceTransformer
import numpy as np

class NovelyScorer:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def score(self, proposed_text: str, prior_art: list[dict]) -> float:
        if not prior_art:
            return 1.0  # Completely novel if no prior art
        
        prior_embeddings = self.model.encode([
            f"{p.get('title', '')} {p.get('abstract', '')}" 
            for p in prior_art
        ])
        proposed_embedding = self.model.encode([proposed_text])[0]
        
        similarities = np.dot(prior_embeddings, proposed_embedding) / (
            np.linalg.norm(prior_embeddings, axis=1) * np.linalg.norm(proposed_embedding)
        )
        max_sim = float(np.max(similarities))
        novelty = 1.0 - max_sim
        return novelty  # 0.0 = identical to prior, 1.0 = completely novel
```

**Confidence v3 formula:**
```python
novelty_boost = novelty_score * 0.10  # +0.10 if completely novel
confidence_v3 = min(
    base_confidence + perspective_boost + quality_boost + source_boost + novelty_boost,
    0.95
)
```

**Integration:**
- If `novelty_score < 0.3`: trigger O₂ meta-reflection with warning "High similarity to prior art"
- If `novelty_score > 0.7`: boost confidence, add "Novelty confirmed" to observer insights

### 6.2 Add Fact-Check Loop

For each claim in the dissertation that cites a source:
1. Extract the claim text (sentence containing `[N]`)
2. Retrieve the cited source's abstract
3. Use NLI (Natural Language Inference) to check if abstract entails, contradicts, or is neutral to the claim
4. Flag contradictions as `MISREPRESENTED`

**Library:** `longtracer` (`pip install longtracer`) or local NLI with `facebook/bart-large-mnli` via transformers.

---

## 7. Key Acquisition Checklist

| Key | Source | URL | Time | Cost | Priority |
|-----|--------|-----|------|------|----------|
| `OPENALEX_API_KEY` | OpenAlex | [openalex.org/settings/api](https://openalex.org/settings/api) | 2 min | Free | 🔴 Critical |
| `CORE_API_KEY` | CORE | [core.ac.uk/services/api](https://core.ac.uk/services/api) | 5 min | Free | 🟡 High |
| `UNPAYWALL_EMAIL` | Unpaywall | [unpaywall.org/products/api](https://unpaywall.org/products/api) | 2 min | Free | 🟡 High |
| `NCBI_API_KEY` | NCBI | [ncbi.nlm.nih.gov/account](https://ncbi.nlm.nih.gov/account) | 5 min | Free | 🟡 High |
| `SEMANTIC_SCHOLAR_API_KEY` | S2 | [semanticscholar.org/product/api](https://semanticscholar.org/product/api) | 2 min | Free | 🟢 Medium (awaiting approval) |

**Note:** You already have `BRAVE_API_KEY` and all LLM keys. The 4 keys above are the only missing ones for full Tier-1+Tier-2 coverage.

---

## 8. Expected Outcomes

### 8.1 Source Coverage

| Metric | v5.5 (Current) | v5.6 (Target) |
|--------|---------------|---------------|
| Active sources in pipeline | 2 (OpenAlex, PubMed) | 12–15 |
| Max citations per dissertation | ~40 | ~60 |
| Source diversity (domains) | General only | Domain-adaptive |
| OA PDF links | 0 | 10–20 via Unpaywall/CORE |
| Patent coverage | Broken | Working via `patent_client` |

### 8.2 Quality Metrics

| Metric | v5.5 (Current) | v5.6 (Target) |
|--------|---------------|---------------|
| Citation hallucination rate | ~40% (unverified) | <5% (verified) |
| Confidence score range | 0.89–0.92 | 0.92–0.96 |
| Novelty detection | None | Objective 0–1 score |
| Rate limit bans | arXiv, S2 | None (compliant + circuit breaker) |
| Pipeline resilience | Graceful degradation | Proactive source rotation |

### 8.3 Cost

| Item | Cost |
|------|------|
| API keys | $0 |
| `pyalex`, `patent_client`, `tenacity`, `sentence-transformers` | $0 (OSS) |
| DeepSeek synthesis | ~$0.10/dissertation (unchanged) |
| **Total incremental** | **$0** |

---

## 9. Implementation Order

### Week 1
- **Day 1:** Fix rate limits in `SOURCE_REGISTRY`, add `tenacity` retry, add circuit breaker
- **Day 2:** Replace `PriorArtSearchEngine` with `MultiSourceSearcher` in pipeline
- **Day 3:** Integrate `pyalex` for OpenAlex, test end-to-end
- **Day 4:** Acquire `OPENALEX_API_KEY`, `CORE_API_KEY`, `UNPAYWALL_EMAIL`, `NCBI_API_KEY`
- **Day 5:** Fix USPTO with `patent_client`, add domain-aware source selection
- **Day 6:** Activate all Tier-1 + Tier-2 sources, run full pipeline test

### Week 2
- **Day 7:** Implement `CitationVerifier` module
- **Day 8:** Integrate citation verification into synthesis step
- **Day 9:** Add BibTeX generation, test with real DOIs
- **Day 10:** Implement `NoveltyScorer` with embeddings
- **Day 11:** Integrate novelty into confidence v3 formula
- **Day 12:** Full integration test, generate 5 dissertations, measure metrics

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| DBLP instability | Circuit breaker + fallback to OpenAlex for CS queries |
| Europe PMC 1 RPS bottleneck | Query in parallel with PubMed (same content, different API) |
| CrossRef polite pool still too slow | Cache aggressively; 300s TTL is fine for metadata |
| Embedding model too slow | `all-MiniLM-L6-v2` runs on CPU in <100ms for 10 papers |
| `pyalex` introduces new dependency | MIT license, single PyPI package, 0 transitive issues |
| Too many sources slow pipeline | `max_concurrent=8`, circuit breaker, 15s timeout per source |

---

## 11. Files to Modify

| File | Change |
|------|--------|
| `src/agents/pipeline.py` | Replace `PriorArtSearchEngine` with `MultiSourceSearcher` |
| `src/agents/pipeline/steps/step_02_prior_art.py` | Use `search_all()` instead of `search()` |
| `src/knowledge/config.py` | Fix rate limits for CrossRef, Europe PMC, arXiv |
| `src/knowledge/sources/openalex.py` | Rewrite with `pyalex` |
| `src/knowledge/orchestrator.py` | Add circuit breaker, domain-aware source selection |
| `src/knowledge/sources/crossref.py` | Add `mailto` parameter for polite pool |
| `src/integrations/prior_art.py` | Deprecate or delete |
| `src/patents/client.py` | Replace with `patent_client` wrapper |
| `src/knowledge/citation_verifier.py` | **New** |
| `src/knowledge/novelty_scorer.py` | **New** |
| `src/agents/pipeline/steps/step_08_synthesis.py` | Add verification + novelty to confidence calc |
| `.env.example` | Add `OPENALEX_API_KEY`, `CORE_API_KEY`, `UNPAYWALL_EMAIL`, `NCBI_API_KEY` |
| `pyproject.toml` | Add `pyalex`, `patent_client`, `tenacity`, `sentence-transformers` |

---

*Plan version: 5.6.0-draft-1*  
*Next action: Await approval to begin Day 1 implementation.*
