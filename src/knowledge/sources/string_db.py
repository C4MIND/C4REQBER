"""
c4reqber: STRING DB Client

Protein-protein interaction networks covering 14,000+ organisms.
No API key required; caller_identity recommended.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.string_db")


class StringDbClient(BaseP6Client):
    """STRING API client for PPI networks and enrichment."""

    BASE_URL = "https://string-db.org/api"
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, caller_identity: str = "c4reqber") -> None:
        self.caller_identity = caller_identity
        super().__init__()

    async def search_proteins(
        self, query: str, species: int = 9606, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Map gene/protein names to STRING identifiers."""
        try:
            params = {
                "identifiers": query.replace(",", "%0d").replace(" ", "%0d"),
                "species": species,
                "echo_query": 1,
                "caller_identity": self.caller_identity,
            }
            data: Any = await self._get("/json/get_string_ids", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            for item in data if isinstance(data, list) else []:
                if isinstance(item, dict):
                    results.append({
                        "string_id": item.get("stringId"),
                        "preferred_name": item.get("preferredName"),
                        "ncbi_taxon": item.get("ncbiTaxonId"),
                        "annotation": item.get("annotation"),
                        "query": item.get("queryItem"),
                        "source": "string_db",
                    })
            return results[:limit]
        except Exception as e:
            logger.warning("STRING search error: %s", e)
            return []

    async def get_network(
        self, identifiers: list[str], species: int = 9606, required_score: int = 400
    ) -> list[dict[str, Any]]:
        """Retrieve PPI network for given identifiers."""
        try:
            params = {
                "identifiers": "%0d".join(identifiers),
                "species": species,
                "required_score": required_score,
                "caller_identity": self.caller_identity,
            }
            data: Any = await self._get("/json/network", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            for item in data if isinstance(data, list) else []:
                if isinstance(item, dict):
                    results.append({
                        "protein_a": item.get("preferredName_A"),
                        "protein_b": item.get("preferredName_B"),
                        "combined_score": item.get("score"),
                        "experimental": item.get("escore"),
                        "database": item.get("dscore"),
                        "textmining": item.get("tscore"),
                        "source": "string_db",
                    })
            return results
        except Exception as e:
            logger.warning("STRING network error: %s", e)
            return []
