"""
c4reqber: OpenFDA API Client

FDA adverse events (FAERS), drug labels, recalls.
Optional API key raises rate limits.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.openfda")


class OpenFdaClient(BaseP6Client):
    """OpenFDA API client."""

    BASE_URL = "https://api.fda.gov"
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("OPENFDA_API_KEY", "")
        super().__init__()

    async def search_adverse_events(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search FAERS adverse event reports."""
        try:
            params: dict[str, Any] = {"search": query, "limit": min(limit, 100)}
            if self.api_key:
                params["api_key"] = self.api_key
            data = await self._get("/drug/event.json", params=params, use_cache=True)
            results = data.get("results", []) if isinstance(data, dict) else []
            out: list[dict[str, Any]] = []
            for item in results[:limit]:
                if not isinstance(item, dict):
                    continue
                patient = item.get("patient", {})
                drugs = patient.get("drug", [])
                reactions = patient.get("reaction", [])
                out.append({
                    "safetyreportid": item.get("safetyreportid"),
                    "receiptdate": item.get("receiptdate"),
                    "drugs": [d.get("medicinalproduct") for d in drugs[:3]],
                    "reactions": [r.get("reactionmeddrapt") for r in reactions[:3]],
                    "source": "openfda",
                })
            return out
        except Exception as e:
            logger.warning("OpenFDA search error: %s", e)
            return []

    async def search_drug_labels(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search drug labels (SPL)."""
        try:
            params: dict[str, Any] = {"search": query, "limit": min(limit, 100)}
            if self.api_key:
                params["api_key"] = self.api_key
            data = await self._get("/drug/label.json", params=params, use_cache=True)
            results = data.get("results", []) if isinstance(data, dict) else []
            out: list[dict[str, Any]] = []
            for item in results[:limit]:
                if not isinstance(item, dict):
                    continue
                out.append({
                    "set_id": item.get("set_id"),
                    "brand_name": item.get("openfda", {}).get("brand_name", []),
                    "generic_name": item.get("openfda", {}).get("generic_name", []),
                    "manufacturer": item.get("openfda", {}).get("manufacturer_name", []),
                    "source": "openfda",
                })
            return out
        except Exception as e:
            logger.warning("OpenFDA label search error: %s", e)
            return []
