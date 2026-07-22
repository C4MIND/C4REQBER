"""Shared flash-mode literature/web context (CLI + MCP)."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.knowledge.config import (
    flash_source_allowlist,
    infer_query_domain,
)


logger = logging.getLogger(__name__)

_SCHOLAR_Q = re.compile(r"scholar\.google\.com/scholar\?q=", re.I)
_EXAMPLE_HOST = re.compile(r"example\.com", re.I)
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)

# Verdicts that may count toward flash "verified" (positive API provenance).
_VERIFIED_VERDICTS = frozenset({"VERIFIED", "PARTIAL"})


def is_checkable_url(url: str | None) -> bool:
    """True if URL is a real http(s) link (not stub / Scholar search synthesis)."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        return False
    if _EXAMPLE_HOST.search(u) or _SCHOLAR_Q.search(u):
        return False
    return True


def is_checkable_paper(paper: dict[str, Any]) -> bool:
    """Has a DOI-shaped id or real URL — candidate for CitationVerifier, not yet verified."""
    doi = (paper.get("doi") or "").strip()
    if doi and doi.lower() not in {"n/a", "none", "null"} and _DOI_RE.match(doi):
        return True
    return is_checkable_url(paper.get("url"))


def is_verifiable_paper(paper: dict[str, Any]) -> bool:
    """Deprecated alias — presence-only. Prefer is_checkable_paper / verified flag."""
    return is_checkable_paper(paper)


def sanitize_paper(paper: dict[str, Any]) -> dict[str, Any]:
    """Drop fake/synthesized URLs; mark checkable (not verified yet)."""
    out = dict(paper)
    url = out.get("url")
    if url and not is_checkable_url(str(url)):
        out["url"] = ""
        out["url_rejected"] = str(url)[:120]
    doi = (out.get("doi") or "").strip()
    if doi and not _DOI_RE.match(doi):
        out["doi"] = ""
        out["doi_rejected"] = doi[:80]
    out["checkable"] = is_checkable_paper(out)
    # Fail-closed until CitationVerifier runs
    out["verified"] = False
    out["verify_verdict"] = "PENDING"
    return out


def format_source_card(paper: dict[str, Any]) -> dict[str, Any]:
    """Stable CLI/MCP citation schema."""
    authors = paper.get("authors") or paper.get("author") or []
    if isinstance(authors, str):
        authors_out: list[str] | str = authors
    elif isinstance(authors, list):
        authors_out = [str(a) for a in authors[:12]]
    else:
        authors_out = []
    return {
        "title": (paper.get("title") or "Untitled").strip(),
        "authors": authors_out,
        "year": paper.get("year") or paper.get("publication_year") or "",
        "doi": (paper.get("doi") or "").strip(),
        "url": (paper.get("url") or "").strip(),
        "source": paper.get("_source") or paper.get("source_engine") or paper.get("source") or "",
        "verified": bool(paper.get("verified")),
        "verify_verdict": paper.get("verify_verdict") or "",
    }


def build_flash_context(
    papers: list[dict[str, Any]],
    *,
    verified_only: bool = False,
) -> str:
    """LLM context with bibliographic fields (never invents URLs)."""
    if verified_only:
        papers = [p for p in papers if p.get("verified")]
    lines: list[str] = []
    for i, p in enumerate(papers, 1):
        card = format_source_card(p)
        authors = card["authors"]
        if isinstance(authors, list):
            authors_s = ", ".join(authors[:5])
        else:
            authors_s = str(authors)
        snippet = (p.get("snippet") or p.get("abstract") or "")[:250]
        flag = "VERIFIED" if p.get("verified") else "UNVERIFIED"
        lines.append(
            f"[{i}] ({flag}) {card['title']}\n"
            f"    authors: {authors_s or 'n/a'}\n"
            f"    year: {card['year'] or 'n/a'}\n"
            f"    doi: {card['doi'] or 'n/a'}\n"
            f"    url: {card['url'] or 'n/a'}\n"
            f"    source: {card['source'] or 'unknown'}\n"
            f"    snippet: {snippet}"
        )
    return "\n".join(lines)


async def annotate_verified(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run CitationVerifier on checkable papers; set verified only on API match.

    Fail-closed: network/ERROR/UNVERIFIED/HALLUCINATED → verified=False.
    """
    if not papers:
        return papers

    from src.knowledge.citation_verifier import CitationVerifier

    verifier = CitationVerifier()
    try:
        checks = await verifier.verify_paper_dicts(papers)
    except Exception as exc:
        logger.warning("flash CitationVerifier failed (fail-closed): %s", exc)
        for p in papers:
            p["verified"] = False
            p["verify_verdict"] = "ERROR"
        return papers
    finally:
        try:
            await verifier.close()
        except Exception:
            pass

    for paper, check in zip(papers, checks, strict=False):
        verdict = check.verdict
        paper["verify_verdict"] = verdict
        paper["verified"] = verdict in _VERIFIED_VERDICTS
        if check.found_in:
            paper["verified_in"] = list(check.found_in)
        if check.openalex_score:
            paper["openalex_score"] = check.openalex_score
    return papers


async def gather_flash_sources(
    question: str,
    *,
    deep: bool = False,
    include_web: bool = True,
    domain: str | None = None,
    verify: bool = True,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    """Search MultiSourceSearcher for flash context.

    Returns (papers, context_block, search_meta).
    Never invents example.com URLs.
    Context for LLM uses verified papers only when any exist.
    """
    from src.knowledge.orchestrator import MultiSourceSearcher

    inferred = domain or infer_query_domain(question)
    allow = flash_source_allowlist(inferred, include_web=include_web)
    searcher = MultiSourceSearcher(sources=allow)
    meta: dict[str, Any] = {
        "domain": inferred,
        "allowlist": sorted(allow),
        "sources_used": [],
        "errors": {},
        "tavily": "off",
        "found": 0,
        "checkable": 0,
        "verified": 0,
    }
    try:
        result = await searcher.search_all(question, domain=inferred, include_web=include_web)
    except Exception as exc:
        logger.warning("flash sources search failed: %s", exc)
        meta["errors"]["search_all"] = str(exc)
        return [], "", meta

    stats = result.get("source_stats") or {}
    used: list[str] = list(result.get("sources_used") or [])
    errors: dict[str, str] = {}
    for src_id, st in stats.items():
        if isinstance(st, dict):
            if st.get("ok") is False and st.get("error"):
                errors[src_id] = str(st["error"])[:200]
            elif st.get("papers"):
                if src_id not in used:
                    used.append(src_id)
    meta["sources_used"] = used
    meta["errors"] = errors
    if "tavily" in searcher._active_sources:  # noqa: SLF001 — intentional meta probe
        meta["tavily"] = "on"
    elif "tavily" in allow:
        meta["tavily"] = "no_key"
    else:
        meta["tavily"] = "off"

    limit = 5 if deep else 3
    raw = result.get("papers", [])[:limit]
    papers = [sanitize_paper(p) for p in raw]
    meta["found"] = len(papers)
    meta["checkable"] = sum(1 for p in papers if p.get("checkable"))

    if verify and papers:
        papers = await annotate_verified(papers)

    meta["verified"] = sum(1 for p in papers if p.get("verified"))
    # Grounding context: verified-only when any passed; else empty (honest)
    context = build_flash_context(papers, verified_only=True)
    if not context.strip() and papers:
        # No verified — do not feed unverified as citable [N] sources
        context = (
            "(No CitationVerifier-confirmed sources. "
            f"{len(papers)} raw hits were found but remain unverified — "
            "do not invent DOI/URL or claim a specific paper was confirmed.)"
        )
    return papers, context, meta
