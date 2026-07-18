"""
C4REQBER: Citation Verifier

Prevents AI-generated citation hallucinations by verifying every [N] citation
against CrossRef (DOI) and OpenAlex (title). Inspired by NousResearch/hermes-agent.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

import httpx

from src.knowledge.contact_email import contact_email


logger = logging.getLogger("c4reqber.citation_verifier")

# Minimum normalized title similarity for OpenAlex "match" (not first hit).
_OPENALEX_TITLE_SIM_THRESHOLD = 0.82


@dataclass
class CitationCheck:
    """Result of verifying a single citation."""

    citation_id: str  # e.g. "[3]"
    title: str
    doi: str | None
    verdict: str  # VERIFIED, PARTIAL, UNVERIFIED, HALLUCINATED, ERROR
    found_in: list[str] = field(default_factory=list)
    crossref_match: bool = False
    openalex_match: bool = False
    openalex_score: float = 0.0
    check_error: str | None = None


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation/diacritics for fuzzy title compare."""
    if not title:
        return ""
    text = unicodedata.normalize("NFKD", title)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio on normalized titles in [0, 1]."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


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
            citations.append(
                {
                    "id": f"[{m.group(1)}]",
                    "context": context,
                }
            )
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
        openalex_score = 0.0
        errors: list[str] = []

        if doi:
            cr = await self._check_crossref(doi)
            if cr.get("error"):
                errors.append(f"crossref:{cr['error']}")
            crossref_ok = bool(cr.get("ok"))
            if crossref_ok:
                found_in.append("CrossRef")

        if title:
            oa = await self._check_openalex(title)
            if oa.get("error"):
                errors.append(f"openalex:{oa['error']}")
            openalex_ok = bool(oa.get("ok"))
            openalex_score = float(oa.get("score") or 0.0)
            if openalex_ok:
                found_in.append("OpenAlex")

        # Verdict logic — VERIFIED requires DOI CrossRef + title-matched OpenAlex
        check_error = "; ".join(errors) if errors else None
        if crossref_ok and openalex_ok:
            verdict = "VERIFIED"
        elif crossref_ok or openalex_ok:
            verdict = "PARTIAL"
        elif check_error and not (title or doi):
            verdict = "ERROR"
        elif title or doi:
            verdict = "UNVERIFIED"
        else:
            verdict = "HALLUCINATED"

        if check_error and verdict in {"UNVERIFIED", "HALLUCINATED"} and (title or doi):
            # Transport failure ≠ "not in literature"
            verdict = "ERROR"

        return CitationCheck(
            citation_id=cit_id,
            title=title or "",
            doi=doi,
            verdict=verdict,
            found_in=found_in,
            crossref_match=crossref_ok,
            openalex_match=openalex_ok,
            openalex_score=openalex_score,
            check_error=check_error,
        )

    @staticmethod
    def _guess_source(context: str, sources: list[dict[str, Any]]) -> tuple[str, str | None]:
        """Try to match citation context to a known source by title proximity."""
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

    async def _check_crossref(self, doi: str) -> dict[str, Any]:
        """Resolve DOI via CrossRef. Returns {ok, error?}."""
        try:
            url = f"{self.CROSSREF_BASE}/{doi}"
            resp = await self._client.get(url, params={"mailto": contact_email()})
            if resp.status_code == 200:
                data = resp.json()
                item = data.get("message", {})
                return {"ok": bool(item.get("title"))}
            return {"ok": False, "error": f"http_{resp.status_code}"}
        except Exception as exc:
            logger.debug("CrossRef check failed: %s", exc, exc_info=True)
            return {"ok": False, "error": type(exc).__name__}

    async def _check_openalex(self, title: str) -> dict[str, Any]:
        """Search title via OpenAlex; match only if similarity ≥ threshold."""
        try:
            url = f"{self.OPENALEX_BASE}"
            resp = await self._client.get(
                url,
                params={
                    "search": title,
                    "per_page": 5,
                    "mailto": contact_email(),
                },
            )
            if resp.status_code != 200:
                return {"ok": False, "score": 0.0, "error": f"http_{resp.status_code}"}
            data = resp.json()
            results = data.get("results") or []
            best_score = 0.0
            best_title = ""
            for item in results:
                hit_title = item.get("display_name") or item.get("title") or ""
                score = title_similarity(title, hit_title)
                if score > best_score:
                    best_score = score
                    best_title = hit_title
            matched = best_score >= _OPENALEX_TITLE_SIM_THRESHOLD
            return {
                "ok": matched,
                "score": round(best_score, 4),
                "matched_title": best_title if matched else "",
            }
        except Exception as exc:
            logger.debug("OpenAlex check failed: %s", exc, exc_info=True)
            return {"ok": False, "score": 0.0, "error": type(exc).__name__}

    async def close(self) -> None:
        await self._client.aclose()
