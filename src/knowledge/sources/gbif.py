"""
c4reqber: GBIF API Client

Global Biodiversity Information Facility — 2.5B+ occurrence records.
Open search API; bulk downloads need account.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.gbif")


class GbifClient(BaseP6Client):
    """GBIF REST API client."""

    BASE_URL = "https://api.gbif.org/v1"
    DEFAULT_TIMEOUT = 30.0

    async def search_occurrences(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search species occurrence records."""
        try:
            params: dict[str, Any] = {
                "q": query,
                "limit": min(limit, 300),
            }
            data = await self._get("/occurrence/search", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            for item in data.get("results", []) if isinstance(data, dict) else []:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "gbif_key": item.get("key"),
                    "scientific_name": item.get("scientificName"),
                    "latitude": item.get("decimalLatitude"),
                    "longitude": item.get("decimalLongitude"),
                    "event_date": item.get("eventDate"),
                    "basis_of_record": item.get("basisOfRecord"),
                    "country": item.get("country"),
                    "source": "gbif",
                })
            return results[:limit]
        except Exception as e:
            logger.warning("GBIF search error: %s", e)
            return []

    async def search_species(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search species in GBIF backbone taxonomy."""
        try:
            params: dict[str, Any] = {"q": query, "limit": min(limit, 20)}
            data = await self._get("/species/search", params=params, use_cache=True)
            results: list[dict[str, Any]] = []
            for item in data.get("results", []) if isinstance(data, dict) else []:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "usage_key": item.get("key"),
                    "scientific_name": item.get("scientificName"),
                    "rank": item.get("rank"),
                    "kingdom": item.get("kingdom"),
                    "source": "gbif",
                })
            return results[:limit]
        except Exception as e:
            logger.warning("GBIF species search error: %s", e)
            return []
