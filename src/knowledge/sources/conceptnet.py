"""
c4reqber: ConceptNet Client

General-purpose semantic network from crowdsourced resources.
Open API: 3600 req/hour.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.conceptnet")


class ConceptNetClient(BaseP6Client):
    """ConceptNet JSON-LD API client."""

    BASE_URL = "http://api.conceptnet.io"
    DEFAULT_TIMEOUT = 30.0

    async def search_concepts(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search concepts by label."""
        try:
            params: dict[str, Any] = {"limit": min(limit, 100)}
            data = await self._get(f"/c/en/{query}", params=params, use_cache=True)
            edges = data.get("edges", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in edges[:limit]:
                if not isinstance(item, dict):
                    continue
                start = item.get("start", {})
                end = item.get("end", {})
                results.append({
                    "relation": item.get("rel", {}).get("label"),
                    "start_label": start.get("label"),
                    "start_language": start.get("language"),
                    "end_label": end.get("label"),
                    "end_language": end.get("language"),
                    "weight": item.get("weight"),
                    "dataset": item.get("dataset"),
                    "source": "conceptnet",
                })
            return results
        except Exception as e:
            logger.warning("ConceptNet search error: %s", e)
            return []

    async def query_relations(
        self, concept: str, rel: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Query edges for a concept, optionally filtered by relation."""
        try:
            path = f"/query?node=/c/en/{concept}"
            if rel:
                path += f"&rel=/r/{rel}"
            data = await self._get(path, params={"limit": min(limit, 100)}, use_cache=True)
            edges = data.get("edges", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in edges[:limit]:
                if not isinstance(item, dict):
                    continue
                start = item.get("start", {})
                end = item.get("end", {})
                results.append({
                    "relation": item.get("rel", {}).get("label"),
                    "start_label": start.get("label"),
                    "end_label": end.get("label"),
                    "weight": item.get("weight"),
                    "source": "conceptnet",
                })
            return results
        except Exception as e:
            logger.warning("ConceptNet query error: %s", e)
            return []
