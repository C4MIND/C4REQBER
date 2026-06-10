from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from collections import Counter
from typing import Any, cast

from .cache import SearchCache
from .config import DOMAIN_KEYWORDS, SOURCE_REGISTRY, _norm_title
from .sources.arxiv import ArxivAdapter
from .sources.base import BaseSourceAdapter
from .sources.base_search import BaseSearchAdapter
from .sources.bibsonomy import BibsonomyAdapter
from .sources.brave import BraveAdapter
from .sources.core import CoreAdapter
from .sources.crossref import CrossrefAdapter
from .sources.datacite import DataciteAdapter
from .sources.dblp import DblpAdapter
from .sources.doaj import DoajAdapter
from .sources.europe_pmc import EuropePmcAdapter
from .sources.exa import ExaAdapter
from .sources.extra_adapters import (
    ArxivggAdapter,
    CiniiAdapter,
    DatasetsAdapter,
    GithubAdapter,
    RsciAdapter,
    ScimaticAdapter,
)
from .sources.figshare import FigshareAdapter
from .sources.inspire_hep import InspireHepAdapter
from .sources.lens_org import LensOrgAdapter
from .sources.oa_mg import OaMgAdapter
from .sources.openalex import OpenAlexAdapter
from .sources.p6_adapters import (
    AflowAdapter,
    AllenBrainAdapter,
    CernOpenDataAdapter,
    ChemblAdapter,
    ClinicalTrialsAdapter,
    ConceptNetAdapter,
    CyberLeninkaAdapter,
    GbifAdapter,
    HarvardDataverseAdapter,
    HuggingFaceDatasetsAdapter,
    KaggleAdapter,
    MaterialsProjectAdapter,
    MathNetRuAdapter,
    NasaEarthdataAdapter,
    NcbiEutilsAdapter,
    NoaaAdapter,
    OeisAdapter,
    OpenFdaAdapter,
    OpenReviewAdapter,
    OrcidAdapter,
    PubchemAdapter,
    Re3dataAdapter,
    StringDbAdapter,
    UciMlAdapter,
    UsgsAdapter,
    UsptoPatentsviewAdapter,
)
from .sources.pubmed import PubmedAdapter
from .sources.semantic_scholar import SemanticScholarAdapter
from .sources.tavily import TavilyAdapter
from .sources.unpaywall import UnpaywallAdapter
from .sources.zenodo import ZenodoAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class _CircuitBreaker:
    """Per-source circuit breaker to prevent ban escalation."""

    def __init__(self, threshold: int = 3, timeout: float = 300.0) -> None:
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure: float | None = None

    def can_call(self) -> bool:
        if self.failures < self.threshold:
            return True
        if self.last_failure is None:
            return True
        if time.monotonic() - self.last_failure > self.timeout:
            self.failures = 0
            return True
        return False

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure = time.monotonic()

    def record_success(self) -> None:
        if self.failures > 0:
            self.failures = max(0, self.failures - 1)


class MultiSourceSearcher:
    """Unified search engine across 17+ academic APIs."""

    MIN_PAPERS_FOR_RESULT = 50
    MAX_PAPERS_PER_SOURCE = 100
    REQUEST_TIMEOUT = 15.0
    CROSS_VALIDATE_SOURCES = 3

    def __init__(
        self,
        api_keys: dict[str, str] | None = None,
        sources: set[str] | None = None,
        max_concurrent: int = 8,
        cache_enabled: bool = True,
        cache_ttl: float = 300.0,
    ) -> None:
        self._api_keys = api_keys or {}
        self._active_sources: dict[str, BaseSourceAdapter] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_trackers: dict[str, float] = {}
        self._rate_locks: dict[str, asyncio.Lock] = {}
        self._circuit_breakers: dict[str, _CircuitBreaker] = {}
        self._cache = SearchCache(enabled=cache_enabled, ttl=cache_ttl)

        self._build_adapters(sources)

        logger.info(
            "MultiSourceSearcher initialized: %d sources active",
            len(self._active_sources),
        )

    def _build_adapters(self, sources: set[str] | None) -> None:
        adapter_map = cast(dict[str, type[BaseSourceAdapter] | None], {
            # semantic_scholar disabled — free tier rate limit (429) hangs the
            # search pipeline. TODO: re-enable after upgrading to paid tier or
            # adding circuit-breaker with longer cooldown.
            # "semantic_scholar": SemanticScholarAdapter,
            "openalex": OpenAlexAdapter,
            "openalex": OpenAlexAdapter,
            "crossref": CrossrefAdapter,
            "arxiv": ArxivAdapter,
            "pubmed": PubmedAdapter,
            "doaj": DoajAdapter,
            "europe_pmc": EuropePmcAdapter,
            "dblp": DblpAdapter,
            "datacite": DataciteAdapter,
            "zenodo": ZenodoAdapter,
            "figshare": FigshareAdapter,
            "brave": BraveAdapter,
            "core": CoreAdapter,
            "base": BaseSearchAdapter,
            "unpaywall": UnpaywallAdapter,
            "oa_mg": OaMgAdapter,
            "lens_org": LensOrgAdapter,
            "inspire_hep": InspireHepAdapter,
            "tavily": TavilyAdapter,
            "exa": ExaAdapter,
            "cinii": CiniiAdapter,
            "github": GithubAdapter,
            "datasets": DatasetsAdapter,
            "rsci": RsciAdapter,
            "scimatic": ScimaticAdapter,
            "arxivgg": ArxivggAdapter,
            "bibsonomy": BibsonomyAdapter,
            "ncbi_eutils": NcbiEutilsAdapter,
            "pubchem": PubchemAdapter,
            "chembl": ChemblAdapter,
            "materials_project": MaterialsProjectAdapter,
            "kaggle": KaggleAdapter,
            "aflow": AflowAdapter,
            "uci_ml": UciMlAdapter,
            "harvard_dataverse": HarvardDataverseAdapter,
            "re3data": Re3dataAdapter,
            # NEW (2026-05-31 batch)
            "string_db": StringDbAdapter,
            "clinicaltrials": ClinicalTrialsAdapter,
            "gbif": GbifAdapter,
            "allen_brain": AllenBrainAdapter,
            "usgs": UsgsAdapter,
            "cern_opendata": CernOpenDataAdapter,
            "oeis": OeisAdapter,
            "conceptnet": ConceptNetAdapter,
            "uspto_patentsview": UsptoPatentsviewAdapter,
            "huggingface_datasets": HuggingFaceDatasetsAdapter,
            "openreview": OpenReviewAdapter,
            "openfda": OpenFdaAdapter,
            "nasa_earthdata": NasaEarthdataAdapter,
            "noaa": NoaaAdapter,
            "orcid": OrcidAdapter,
            "cyberleninka": CyberLeninkaAdapter,
            "mathnet_ru": MathNetRuAdapter,
        })

        for src_id, cfg in SOURCE_REGISTRY.items():
            if sources is not None and src_id not in sources:
                continue
            if not cfg.get("enabled", True):
                continue
            key: str | None = None
            if cfg.get("needs_key"):
                api_key_env = cfg.get("api_key_env", f"{src_id.upper()}_API_KEY")
                key = os.environ.get(api_key_env) or os.environ.get(api_key_env.upper()) or self._api_keys.get(api_key_env, "")
                if not key:
                    key = self._api_keys.get(api_key_env.upper(), "")
                if not key:
                    logger.debug("Skipping %s: API key required (%s)", src_id, api_key_env)
                    continue
            adapter_cls = adapter_map.get(src_id)
            if adapter_cls is None:
                logger.debug("No adapter for %s", src_id)
                continue
            self._active_sources[src_id] = adapter_cls(api_key=key)

    # ─── Public API ───────────────────────────────────────────────────────

    async def search_all(
        self,
        query: str,
        domain: str = "general",
        max_per_source: int | None = None,
        include_web: bool = False,
    ) -> dict[str, Any]:
        # Domain-aware source boost: prioritize domain-specific sources
        domain_boost = self._domain_sources(domain)
        """Launch ALL active sources in parallel. Semaphore controls concurrency."""
        cache_key = f"search_all:{query}:{domain}:{max_per_source or self.MAX_PAPERS_PER_SOURCE}:web={include_web}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        t0 = time.perf_counter()

        max_per = max_per_source or self.MAX_PAPERS_PER_SOURCE
        keywords = self._extract_query_keywords(query)

        async def search_one(src_id: str) -> tuple[str, list[dict], float]:
            """Search one."""
            t1 = time.perf_counter()
            try:
                papers = await self._search_with_timeout(src_id, query, max_per)
                return (src_id, papers, time.perf_counter() - t1)
            except Exception as e:
                return (src_id, [{"error": str(e)}], time.perf_counter() - t1)

        tasks = [search_one(src_id) for src_id in self._active_sources]
        results = await asyncio.gather(*tasks)

        all_papers: list[dict] = []
        source_stats: dict[str, dict] = {}
        sources_used: list[str] = []

        for src_id, papers, elapsed in results:
            papers = papers or []
            papers = [p for p in papers if "error" not in p]  # Filter error dicts
            for p in papers:
                p.setdefault("_source", src_id)
            all_papers.extend(papers)
            if papers:
                sources_used.append(src_id)
            source_stats[src_id] = {
                "papers": len(papers),
                "time": round(elapsed, 3),
                "ok": not any(isinstance(p, dict) and "error" in p for p in papers),
            }

        unique_papers = self._deduplicate(all_papers)

        if not include_web:
            unique_papers = [p for p in unique_papers if p.get("type") != "web"]

        domain_boost = self._domain_sources(domain)
        for p in unique_papers:
            base_score = self._relevance_score(p, keywords)
            # Slight boost if paper comes from a domain-relevant source
            paper_sources = set(p.get("_sources", p.get("sources", [])))
            if paper_sources & domain_boost:
                base_score = min(base_score + 0.05, 1.0)
            p["relevance_score"] = base_score
            p["domain"] = self._classify_domain(p, keywords)

        for p in unique_papers:
            p["source_count"] = len(p.get("_sources", p.get("sources", [])))
            p["cross_validated"] = p["source_count"] >= self.CROSS_VALIDATE_SOURCES

        unique_papers.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)

        total = time.perf_counter() - t0

        logger.info(
            "MultiSource: %d papers from %d sources in %.1fs",
            len(unique_papers),
            len(sources_used),
            total,
        )

        result = {
            "papers": unique_papers,
            "total_papers": len(unique_papers),
            "total_raw": len(all_papers),
            "sources_used": len(sources_used),
            "source_names": sources_used,
            "source_stats": source_stats,
            "total_time": round(total, 3),
            "relevance_distribution": {
                ">0.8": len([p for p in unique_papers if p.get("relevance_score", 0) > 0.8]),
                ">0.5": len([p for p in unique_papers if p.get("relevance_score", 0) > 0.5]),
                ">0.3": len([p for p in unique_papers if p.get("relevance_score", 0) > 0.3]),
            },
        }

        self._cache.set(cache_key, result)

        # Cache embeddings in ChromaDB vector store for RAG
        try:
            from src.knowledge.chroma_store import ChromaVectorStore
            store = ChromaVectorStore()
            store.add_knowledge(query, unique_papers[:50])
        except Exception:
            logger.warning("ChromaDB embedding cache failed", exc_info=True)

        return result

    async def search_single(self, source: str, query: str) -> list[dict[str, Any]]:
        """Search a single source by name."""
        cache_key = f"search_single:{source}:{query}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        cfg = SOURCE_REGISTRY.get(source)
        if not cfg:
            logger.warning("Unknown source: %s", source)
            return []
        result = await self._search_with_timeout(source, query, self.MAX_PAPERS_PER_SOURCE)
        self._cache.set(cache_key, result)
        return result

    async def get_source_list(self) -> list[dict[str, Any]]:
        """Return all registered source metadata."""
        result: list[dict[str, Any]] = []
        for src_id, cfg in SOURCE_REGISTRY.items():
            result.append({
                "id": src_id,
                "name": cfg["name"],
                "tier": cfg["tier"],
                "coverage": cfg["coverage"],
                "needs_key": cfg["needs_key"],
                "active": src_id in self._active_sources,
            })
        return result

    # ─── Internal: Query Analysis ─────────────────────────────────────────

    def _domain_sources(self, domain: str) -> set[str]:
        """Return source IDs prioritized for a given research domain."""
        from .config import DOMAIN_SOURCES
        return DOMAIN_SOURCES.get(domain, DOMAIN_SOURCES["general"])

    def _extract_query_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query for relevance scoring."""
        import re
        q = query.lower().strip()
        q = re.sub(r"[^\w\s]", " ", q, flags=re.UNICODE)
        words = [w for w in q.split() if len(w) > 2]
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "are",
            "was", "has", "have", "been", "will", "can", "not", "but",
            "its", "also", "which", "their", "they", "were", "when",
        }
        meaningful = [w for w in words if w not in stopwords]
        return meaningful[:20]

    # ─── Internal: Search Orchestration ───────────────────────────────────

    async def _search_with_timeout(
        self, src_id: str, query: str, limit: int,
    ) -> list[dict[str, Any]]:
        cfg = SOURCE_REGISTRY.get(src_id)
        if not cfg or src_id not in self._active_sources:
            return []

        # Circuit breaker check
        cb = self._circuit_breakers.setdefault(src_id, _CircuitBreaker())
        if not cb.can_call():
            logger.debug("Source %s circuit breaker open — skipping", src_id)
            return []

        timeout_val = cfg.get("timeout", self.REQUEST_TIMEOUT)

        try:
            async with self._semaphore:
                await self._rate_limit(src_id, cfg)
                papers = await asyncio.wait_for(
                    self._dispatch_source(src_id, query, limit),
                    timeout=timeout_val,
                )
                cb.record_success()
                return papers
        except TimeoutError:
            logger.debug("Source %s timed out after %ss", src_id, timeout_val)
            cb.record_failure()
            return []
        except Exception as e:
            logger.debug("Source %s error: %s", src_id, e)
            cb.record_failure()
            return []

    async def _rate_limit(self, src_id: str, cfg: dict[str, Any]) -> None:
        rate = cfg.get("rate_limit", 1.0)
        lock = self._rate_locks.setdefault(src_id, asyncio.Lock())
        async with lock:
            last = self._rate_trackers.get(src_id, 0.0)
            now = time.monotonic()
            interval = 1.0 / rate if rate > 0 else 0.0
            wait = last + interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._rate_trackers[src_id] = time.monotonic()

    async def _dispatch_source(
        self, src_id: str, query: str, limit: int,
    ) -> list[dict[str, Any]]:
        adapter = self._active_sources.get(src_id)
        if adapter is None:
            return []
        return await adapter.search(query, limit)

    # ─── Backward-compatible handler wrappers ─────────────────────────────

    async def _search_semantic_scholar(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("semantic_scholar", query, limit)

    async def _search_openalex(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("openalex", query, limit)

    async def _search_crossref(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("crossref", query, limit)

    async def _search_arxiv(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("arxiv", query, limit)

    async def _search_pubmed(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("pubmed", query, limit)

    async def _search_doaj(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("doaj", query, limit)

    async def _search_europe_pmc(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("europe_pmc", query, limit)

    async def _search_dblp(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("dblp", query, limit)

    async def _search_datacite(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("datacite", query, limit)

    async def _search_zenodo(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("zenodo", query, limit)

    async def _search_figshare(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("figshare", query, limit)

    async def _search_core(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("core", query, limit)

    async def _search_base(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("base", query, limit)

    async def _search_unpaywall(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("unpaywall", query, limit)

    async def _search_oa_mg(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("oa_mg", query, limit)

    async def _search_lens_org(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("lens_org", query, limit)

    async def _search_inspire_hep(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("inspire_hep", query, limit)

    async def _search_brave(self, query: str, limit: int) -> list[dict[str, Any]]:
        return await self._dispatch_source("brave", query, limit)

    # ─── Backward-compatible normalizer wrappers ──────────────────────────

    def _normalize_semantic_scholar(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return SemanticScholarAdapter()._normalize(data)

    def _normalize_openalex(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return OpenAlexAdapter()._normalize(data)

    def _normalize_crossref(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return CrossrefAdapter()._normalize(data)

    def _normalize_arxiv_xml(self, xml_text: str) -> list[dict[str, Any]]:
        return ArxivAdapter()._normalize(xml_text)

    def _normalize_pubmed_xml(self, xml_text: str, id_list: list[str]) -> list[dict[str, Any]]:
        return PubmedAdapter()._normalize(xml_text, id_list)

    def _normalize_doaj(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return DoajAdapter()._normalize(data)

    def _normalize_europe_pmc(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return EuropePmcAdapter()._normalize(data)

    def _normalize_dblp(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return DblpAdapter()._normalize(data)

    def _normalize_datacite(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return DataciteAdapter()._normalize(data)

    def _normalize_zenodo(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return ZenodoAdapter()._normalize(data)

    def _normalize_figshare(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return FigshareAdapter()._normalize(data)

    def _normalize_core(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return CoreAdapter()._normalize(data)

    def _normalize_base(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return BaseSearchAdapter()._normalize(data)

    # ─── Deduplication ────────────────────────────────────────────────────

    def _deduplicate(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        for paper in papers:
            key = self._dedup_key(paper)
            if key not in seen:
                paper["sources"] = [paper.get("source_name", paper.get("source", ""))]
                seen[key] = paper
            else:
                existing = seen[key]
                existing_sources: list[str] = existing.get("sources", [])
                new_source = paper.get("source_name", paper.get("source", ""))
                if new_source and new_source not in existing_sources:
                    existing_sources.append(new_source)
                existing["sources"] = existing_sources
                ec = existing.get("citation_count", 0) or 0
                nc = paper.get("citation_count", 0) or 0
                if nc > ec:
                    existing["citation_count"] = nc
                if paper.get("abstract") and not existing.get("abstract"):
                    existing["abstract"] = paper["abstract"]
                if paper.get("doi") and not existing.get("doi"):
                    existing["doi"] = paper["doi"]
                seen[key] = existing
        deduped = list(seen.values())
        # Semantic deduplication: remove near-duplicate papers with different titles/DOIs
        try:
            from src.llm.embeddings import semantic_deduplicate
            deduped = semantic_deduplicate(deduped, threshold=0.85)
        except (ImportError, RuntimeError, ValueError, TypeError) as e:
            logger.warning("Semantic deduplication failed: %s", e)
        return deduped

    def _dedup_key(self, paper: dict[str, Any]) -> str:
        doi = paper.get("doi")
        if doi:
            return f"doi:{doi.lower()}"
        arxiv_id = paper.get("arxiv_id")
        if arxiv_id:
            return f"arxiv:{arxiv_id}"
        pmid = paper.get("pmid")
        if pmid:
            return f"pmid:{pmid}"
        title = paper.get("title", "")
        norm = _norm_title(title)
        if norm:
            return f"title:{hashlib.md5(norm.encode(), usedforsecurity=False).hexdigest()}"
        import json
        stable = json.dumps(paper, sort_keys=True, default=str)
        return f"hash:{hashlib.md5(stable.encode(), usedforsecurity=False).hexdigest()}"

    # ─── Relevance Scoring ────────────────────────────────────────────────

    def _relevance_score(self, paper: dict[str, Any], query_keywords: list[str]) -> float:
        """Score paper relevance 0-1 by keyword overlap in title + abstract."""
        title = (paper.get("title") or "").lower()
        abstract = (paper.get("abstract") or "").lower()
        text = f"{title} {abstract}"
        if not query_keywords:
            return 0.5
        matches = 0
        for kw in query_keywords:
            if kw.lower() in text:
                matches += 1
        score = matches / len(query_keywords) if query_keywords else 0.5
        return score

    # ─── Domain Classification ────────────────────────────────────────────

    def _classify_domain(self, paper: dict[str, Any], query_keywords: list[str]) -> str:
        """Auto-classify paper into research domain based on title + abstract text."""
        title = (paper.get("title") or "").lower()
        abstract = (paper.get("abstract") or "").lower()
        combined = f"{title} {abstract}"

        scores: dict[str, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in combined:
                    score += 1
            if score > 0:
                scores[domain] = score

        if scores:
            return max(scores, key=lambda k: scores[k])

        for kw in query_keywords:
            for domain, keywords in DOMAIN_KEYWORDS.items():
                if kw.lower() in keywords:
                    return domain

        return "general"

    # ─── Cross-Validation ─────────────────────────────────────────────────

    def _cross_validate_score(self, paper: dict[str, Any]) -> float:
        """Paper credibility increases with source diversity."""
        sources = paper.get("sources", [paper.get("source_name", "")])
        unique = len(set(sources))
        return min(1.0, unique / max(self.CROSS_VALIDATE_SOURCES, 1))

    # ─── Summary Builder ──────────────────────────────────────────────────

    def _build_summary(
        self,
        papers: list[dict[str, Any]],
        sources_used: set[str],
        source_counts: dict[str, int],
        errors: dict[str, str],
    ) -> dict[str, Any]:
        scores = [p.get("relevance_score", 0) for p in papers]
        years = []
        for p in papers:
            y = p.get("year", 0)
            try:
                y = int(y)
            except (ValueError, TypeError):
                y = 0
            if y > 0:
                years.append(y)
        domains = Counter(p.get("domain", "general") for p in papers)

        rel_dist: dict[str, int] = {
            ">0.8": sum(1 for s in scores if s > 0.8),
            "0.5-0.8": sum(1 for s in scores if 0.5 < s <= 0.8),
            "0.2-0.5": sum(1 for s in scores if 0.2 < s <= 0.5),
            "<0.2": sum(1 for s in scores if s <= 0.2),
        }

        year_dist: dict[str, Any] = {}
        if years:
            year_dist = {
                "min": min(years),
                "max": max(years),
                "median": sorted(years)[len(years) // 2] if years else 0,
                "top_decade": max(Counter(y // 10 * 10 for y in years).items(), key=lambda x: x[1], default=(0, 0))[0],
            }

        cross_validated = sum(1 for p in papers if self._cross_validate_score(p) > 0.5)

        for p in papers:
            p["cross_validation_score"] = self._cross_validate_score(p)

        return {
            "total_papers": len(papers),
            "sources_used": sorted(sources_used),
            "source_counts": source_counts,
            "errors": errors,
            "papers": papers[:200],
            "relevance_distribution": rel_dist,
            "year_distribution": year_dist,
            "domains": dict(domains.most_common(10)),
            "cross_validated_papers": cross_validated,
            "avg_relevance": round(sum(scores) / len(scores), 3) if scores else 0.0,
        }
