"""Phase 2: Knowledge Acquisition — MultiSourceSearcher, citation chasing, paper fallback."""
from __future__ import annotations

import logging


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase2")


async def run_knowledge_acquisition(problem: str, domain: str, thresholds: dict, results: dict, errors: list) -> tuple:
    """Run knowledge acquisition."""
    import asyncio

    from src.api.v8_routers.discovery.search import search_knowledge

    papers_found = 0
    sources_used = 0
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher
        multi = MultiSourceSearcher(sources={'semantic_scholar', 'openalex', 'crossref', 'arxiv', 'pubmed', 'europe_pmc'})
        search_result = await asyncio.wait_for(multi.search_all(problem, domain), timeout=30.0)
        papers = search_result.get("papers", [])
        papers_found = search_result.get("total_papers", 0)
        sources_used = search_result.get("sources_used", 0)
        if papers_found < thresholds["min_papers_for_discovery"]:
            abort_reasons = results.setdefault("_abort_reasons", [])
            abort_reasons.append(f"INSUFFICIENT_DATA: Found only {papers_found} papers. Minimum {thresholds['min_papers_for_discovery']} required. Sources used: {sources_used}.")
        results["papers_found"] = len(papers)
        results["papers"] = papers[:5]
    except (ImportError, Exception):
        try:
            papers = await search_knowledge(problem)
            papers_found = len(papers)
            sources_used = 0
            results["papers_found"] = len(papers)
            results["papers"] = papers[:5]
        except Exception as e2:
            results["papers_found"] = 0
            results["papers"] = []
            errors.append(f"knowledge: {str(e2)}")
            papers = []
    citation_chase_result: dict[str, object] = {}
    try:
        from src.knowledge.citation_chaser import CitationChaser
        chaser = CitationChaser(max_depth=thresholds["recursive_search_depth"])
        chase_result = await chaser.chase(papers[:20], problem)
        expanded_papers = chase_result.get("all_papers", papers)
        citation_velocity = chase_result.get("citation_velocity", 0.0)
        seminal_papers = chase_result.get("seminal_papers", [])
        citation_timeline = chase_result.get("paradigm_timeline", [])
        papers = expanded_papers
        citation_chase_result = {"expanded_count": chase_result.get("total_unique_papers", 0), "citation_velocity": citation_velocity, "seminal_papers": seminal_papers, "is_field_growing": chase_result.get("is_field_growing", False), "first_publication_year": chase_result.get("first_publication_year"), "timeline": citation_timeline}
    except ImportError:
        pass
    results["_papers_list"] = papers
    results["_papers_found"] = papers_found
    results["_sources_used"] = sources_used
    results["_citation_chase_result"] = citation_chase_result
    return papers, papers_found, sources_used, citation_chase_result
