"""
TURBO-CDI: Patent Search Integration
White space analysis and patent landscape

NOTE: This is a DEMO implementation with mock data.
For production use, integrate with:
- USPTO Open Data API (https://developer.uspto.gov/)
- EPO Open Patent Services (https://www.epo.org/searching-for-patents/)
- Google Patents Public Datasets (BigQuery)

USPTO API is free and doesn't require API key for basic usage.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Patent:
    """Patent data."""

    patent_id: str
    title: str
    abstract: str
    assignee: str
    inventors: List[str]
    filing_date: str
    grant_date: Optional[str]
    claims_count: int
    citations: List[str]
    classification: str


class PatentSearchClient:
    """
    Patent search client (USPTO, EPO, WIPO).

    CURRENT STATUS: Demo mode with mock data.
    To enable real search, set PATENT_API_PROVIDER environment variable.
    """

    # Demo patents for common queries
    DEMO_PATENTS: Dict[str, List[Patent]] = {
        "battery": [
            Patent(
                patent_id="US10,123,456",
                title="Advanced Battery Management System",
                abstract="A system for managing battery charging cycles...",
                assignee="Tesla Inc",
                inventors=["J. Doe", "A. Smith"],
                filing_date="2020-03-15",
                grant_date="2021-08-20",
                claims_count=12,
                citations=["US9,123,456", "US8,123,456"],
                classification="H01M10/44",
            ),
            Patent(
                patent_id="US10,234,567",
                title="Solid-State Battery Architecture",
                abstract="Novel solid-state battery with improved conductivity...",
                assignee="QuantumScape",
                inventors=["B. Johnson"],
                filing_date="2019-11-20",
                grant_date="2021-05-15",
                claims_count=18,
                citations=["US9,234,567"],
                classification="H01M10/0562",
            ),
        ],
        "solar": [
            Patent(
                patent_id="US10,987,654",
                title="High-Efficiency Perovskite Solar Cell",
                abstract="Novel perovskite composition for improved efficiency...",
                assignee="Oxford PV",
                inventors=["C. Smith", "D. Lee"],
                filing_date="2020-01-10",
                grant_date="2021-06-15",
                claims_count=15,
                citations=["US9,876,543"],
                classification="H01L31/00",
            ),
        ],
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PATENT_API_KEY")
        self.provider = os.getenv("PATENT_API_PROVIDER", "demo")

    def search_patents(
        self,
        query: str,
        limit: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Patent]:
        """
        Search for patents.

        CURRENTLY: Returns demo data. Set PATENT_API_PROVIDER=uspto for real search.
        """
        if self.provider == "demo":
            return self._demo_search(query, limit)
        elif self.provider == "uspto":
            return self._search_uspto(query, limit, date_from, date_to)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _demo_search(self, query: str, limit: int) -> List[Patent]:
        """Demo search with keyword matching."""
        query_lower = query.lower()

        # Match against demo data
        for keyword, patents in self.DEMO_PATENTS.items():
            if keyword in query_lower:
                return patents[:limit]

        # Default demo data
        return self.DEMO_PATENTS["battery"][:limit]

    def _search_uspto(
        self,
        query: str,
        limit: int,
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> List[Patent]:
        """
        Search USPTO Patent Public Search API.
        NOTE: Requires implementation. See https://developer.uspto.gov/
        """
        raise NotImplementedError(
            "USPTO API integration not yet implemented. "
            "Use PATENT_API_PROVIDER=demo for mock data, or contribute at "
            "https://github.com/your-org/turbo-cdi"
        )

    def analyze_white_space(
        self, technology_area: str, existing_patents: List[Patent]
    ) -> Dict[str, Any]:
        """
        Analyze white space (unpatented areas).

        Args:
            technology_area: Technology domain
            existing_patents: List of existing patents

        Returns:
            White space analysis
        """
        # Analyze patent claims and classifications
        classifications = {}
        for p in existing_patents:
            cls = p.classification
            classifications[cls] = classifications.get(cls, 0) + 1

        # Identify gaps
        # In production, use NLP on claims to identify technology gaps
        gaps = [
            f"Limited patents in {technology_area} thermal management",
            f"Few patents combining {technology_area} with AI optimization",
        ]

        return {
            "technology_area": technology_area,
            "patent_count": len(existing_patents),
            "classifications": classifications,
            "white_space_areas": gaps,
            "recommendation": "Focus on thermal management + AI integration",
        }


# Singleton
_client: Optional[PatentSearchClient] = None


def get_patent_client() -> PatentSearchClient:
    """Get singleton patent client."""
    global _client
    if _client is None:
        _client = PatentSearchClient()
    return _client
