"""
c4reqber: ClinicalTrials.gov API v2 Client

Registry of 460,000+ clinical trials. Open read access, no API key.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.clinicaltrials")


class ClinicalTrialsClient(BaseP6Client):
    """ClinicalTrials.gov API v2 client."""

    BASE_URL = "https://clinicaltrials.gov/api/v2"
    DEFAULT_TIMEOUT = 30.0

    async def search_studies(
        self, query: str, condition: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search clinical studies by query and optional condition."""
        try:
            params: dict[str, Any] = {
                "pageSize": min(limit, 100),
                "query.term": query,
            }
            if condition:
                params["query.cond"] = condition
            data = await self._get("/studies", params=params, use_cache=True)
            studies = data.get("studies", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in studies[:limit]:
                if not isinstance(item, dict):
                    continue
                proto = item.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status = proto.get("statusModule", {})
                results.append({
                    "nct_id": ident.get("nctId"),
                    "title": ident.get("briefTitle"),
                    "status": status.get("overallStatus"),
                    "phase": proto.get("designModule", {}).get("phases", []),
                    "conditions": proto.get("conditionsModule", {}).get("conditions", []),
                    "source": "clinicaltrials",
                })
            return results
        except Exception as e:
            logger.warning("ClinicalTrials search error: %s", e)
            return []

    async def get_study(self, nct_id: str) -> dict[str, Any]:
        """Fetch full study metadata by NCT ID."""
        try:
            data = await self._get(f"/studies/{nct_id}", use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("ClinicalTrials get_study error: %s", e)
            return {}
