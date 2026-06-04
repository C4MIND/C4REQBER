"""
C4REQBER: Citation Verifier

Prevents AI-generated citation hallucinations by verifying every [N] citation
against CrossRef (DOI) and OpenAlex (title). Inspired by NousResearch/hermes-agent.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import httpx


logger = logging.getLogger("c4reqber.citation_verifier")


@dataclass
class CitationCheck:
    """Result of verifying a single citation."""

    citation_id: str  # e.g. "[3]"
    title: str
    doi: str | None
    verdict: str  # VERIFIED, PARTIAL, UNVERIFIED, HALLUCINATED
    found_in: list[str] = field(default_factory=list)
    crossref_match: bool = False
    openalex_match: bool = False


class CitationVerifier:
    """Verify citations in dissertation text against real APIs."""

    CROSSREF_BASE = "https://api.crossref.org/works"
    OPENALEX_BASE = "https://api.openalex.org/works"
    TIMEOUT = 10.0

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=self.TIMEOUT)

    async def verify(
        self,
        dissertation_text: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> list[CitationCheck]:
        """Extract and verify all [N] citations in the text."""
        citations = self._extract_citations(dissertation_text)
        if not citations:
            return []

        tasks = [self._verify_single(cit, sources or []) for cit in citations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, CitationCheck)]

    # ── Extraction ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_citations(text: str) -> list[dict[str, str]]:
        """Find all [N] markers and nearby context."""
        pattern = re.compile(r"\[(\d+)\]")
        citations: list[dict[str, str]] = []
        for m in pattern.finditer(text):
            start = max(m.start() - 200, 0)
            end = min(m.end() + 200, len(text))
            context = text[start:end]
            citations.append({
                "id": f"[{m.group(1)}]",
                "context": context,
            })
        return citations

    # Common patterns in LLM-hallucinated citations
    _SUSPICIOUS_PATTERNS: tuple[str, ...] = (
        "recursive harmonic",
        "pantheon theory",
        "echoverse",
        "uch-hstr",
        "cha-ai",
        "ξnet",
        "hyperbolic string",
        "dimensional synthesis",
        "glyphic encoding",
    )

    async def _verify_single(
        self,
        citation: dict[str, str],
        sources: list[dict[str, Any]],
    ) -> CitationCheck:
        """Verify one citation against CrossRef + OpenAlex."""
        cit_id = citation["id"]
        context = citation["context"]

        # Try to find matching source from the sources list
        title, doi = self._guess_source(context, sources)

        # Heuristic: flag suspicious made-up titles even before API calls
        lower_title = (title or "").lower()
        if any(p in lower_title for p in self._SUSPICIOUS_PATTERNS):
            return CitationCheck(
                citation_id=cit_id,
                title=title or "",
                doi=doi,
                verdict="HALLUCINATED",
                found_in=[],
                crossref_match=False,
                openalex_match=False,
            )

        found_in: list[str] = []
        crossref_ok = False
        openalex_ok = False

        if doi:
            crossref_ok = await self._check_crossref(doi)
            if crossref_ok:
                found_in.append("CrossRef")

        if title:
            openalex_ok = await self._check_openalex(title)
            if openalex_ok:
                found_in.append("OpenAlex")

        # Verdict logic
        if crossref_ok and openalex_ok:
            verdict = "VERIFIED"
        elif crossref_ok or openalex_ok:
            verdict = "PARTIAL"
        elif title or doi:
            verdict = "UNVERIFIED"
        else:
            verdict = "HALLUCINATED"

        return CitationCheck(
            citation_id=cit_id,
            title=title or "",
            doi=doi,
            verdict=verdict,
            found_in=found_in,
            crossref_match=crossref_ok,
            openalex_match=openalex_ok,
        )

    @staticmethod
    def _guess_source(context: str, sources: list[dict[str, Any]]) -> tuple[str, str | None]:
        """Try to match citation context to a known source by title proximity."""
        # Very simple heuristic: look for a title in the References section
        # that appears near the citation marker
        best_title = ""
        best_doi = None
        for src in sources:
            title = src.get("title", "")
            if title and title.lower() in context.lower():
                best_title = title
                best_doi = src.get("doi") or None
                break
        return best_title, best_doi

    # ── External checks ──────────────────────────────────────────────────

    async def _check_crossref(self, doi: str) -> bool:
        """Resolve DOI via CrossRef."""
        try:
            url = f"{self.CROSSREF_BASE}/{doi}"
            resp = await self._client.get(url, params={"mailto": "c44tcdi@example.com"})
            if resp.status_code == 200:
                data = resp.json()
                item = data.get("message", {})
                return bool(item.get("title"))
        except Exception:
            pass
        return False

    async def _check_openalex(self, title: str) -> bool:
        """Search title via OpenAlex."""
        try:
            url = f"{self.OPENALEX_BASE}"
            resp = await self._client.get(
                url,
                params={
                    "search": title,
                    "per_page": 1,
                    "mailto": "c44tcdi@example.com",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return bool(results[0].get("title"))
        except Exception:
            pass
        return False

    async def close(self) -> None:
        await self._client.aclose()
