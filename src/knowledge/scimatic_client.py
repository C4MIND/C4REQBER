"""
SciMatic API Client
License: ⚠️ Proprietary — user provides API key
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class SciMaticClient:
    """Client for SciMatic API (optional)."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("SCIMATIC_API_KEY", "")
        self.base_url = "https://scimatic.org/api"

    def search(self, query: str, sources: list[str] | None = None) -> dict[str, Any]:
        """Multi-source search (requires API key).

        Sources: pubmed, scopus, crossref, arxiv, doaj
        """
        if not self.api_key:
            return {"error": "SciMatic API key required", "status": 501}

        if sources is None:
            sources = ["pubmed", "scopus", "crossref", "arxiv", "doaj"]

        try:
            response = httpx.get(
                f"{self.base_url}/search",
                params={"q": query, "sources": ",".join(sources)},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}", "status": e.response.status_code}
        except httpx.RequestError as e:
            return {"error": str(e), "status": 503}

    def export_bibtex(self, paper_ids: list[str]) -> str:
        """Export papers as BibTeX."""
        if not self.api_key:
            return ""

        try:
            response = httpx.post(
                f"{self.base_url}/export/bibtex",
                json={"paper_ids": paper_ids},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, Exception):
            return ""
