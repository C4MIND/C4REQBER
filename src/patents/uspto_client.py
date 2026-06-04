"""
C4REQBER: USPTO Patent Search Client

Uses ``patent_client`` (MIT) for live USPTO database access.
Replaces the deprecated PatentsView v1 API which now returns 301 redirects.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger("c4reqber.patents.uspto")


@dataclass
class Patent:
    """Patent data from USPTO."""

    patent_id: str
    title: str
    abstract: str
    assignee: str
    inventors: list[str]
    filing_date: str
    grant_date: str | None
    claims_count: int
    citations: list[str]
    classification: str
    url: str = ""


class PatentSearchClient:
    """Django-style ORM wrapper around USPTO live databases via patent_client."""

    def __init__(self) -> None:
        self._client = None
        try:
            from patent_client import Patent
            self._client = Patent
        except Exception as exc:
            logger.warning("patent_client unavailable: %s", exc)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search USPTO patents by title/abstract keywords."""
        if self._client is None:
            logger.warning("patent_client not installed — skipping USPTO search")
            return []

        try:
            # patent_client uses Django-style ORM queries
            qs = self._client.objects.filter(
                title__contains=query,
                issue_date__gt="2010-01-01",
            ).values(
                "publication_number",
                "title",
                "abstract",
                "description",
                "inventors",
                "filing_date",
                "issue_date",
            )[:limit]

            results = list(qs)
            return [
                {
                    "patent_id": r.get("publication_number", ""),
                    "title": r.get("title", ""),
                    "abstract": r.get("abstract", "") or r.get("description", "")[:500],
                    "assignee": "",
                    "inventors": r.get("inventors", []) if isinstance(r.get("inventors"), list) else [],
                    "filing_date": r.get("filing_date", ""),
                    "grant_date": r.get("issue_date", ""),
                    "claims_count": 0,
                    "citations": [],
                    "classification": "",
                    "url": f"https://patents.google.com/?q={r.get('publication_number', '')}",
                }
                for r in results
            ]
        except Exception as exc:
            logger.warning("USPTO search failed: %s", exc)
            return []


class USPTOClient:
    """Thin wrapper for backward compatibility."""

    def __init__(self) -> None:
        self._searcher = PatentSearchClient()

    def search_patents(self, query: str, limit: int = 10) -> list[Patent]:
        """Return Patent dataclass objects."""
        raw = self._searcher.search(query, limit)
        return [
            Patent(
                patent_id=r["patent_id"],
                title=r["title"],
                abstract=r["abstract"],
                assignee=r["assignee"],
                inventors=r["inventors"],
                filing_date=r["filing_date"],
                grant_date=r["grant_date"],
                claims_count=r["claims_count"],
                citations=r["citations"],
                classification=r["classification"],
                url=r["url"],
            )
            for r in raw
        ]


def get_patent_client() -> PatentSearchClient:
    """Factory for patent search client."""
    return PatentSearchClient()
