"""
c4reqber: AFLOW Client

Access to the AFLOW LIBRARY of DFT-calculated materials.
License: Free academic use
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.aflow")


class AflowClient(BaseP6Client):
    """AFLOW LIBRARY REST API client."""

    BASE_URL = "https://aflowlib.duke.edu/search/API"
    DEFAULT_TIMEOUT = 60.0

    async def search_materials(
        self,
        query: str,
        catalog: str = "icsd",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search materials by keyword (element, formula, etc.).

        Args:
            query: Search term (e.g. "SiO2", "Fe", "perovskite").
            catalog: Data catalog (icsd, lib1, lib2, lib3).
            limit: Max results to return.
        """
        try:
            # AFLOW uses a query-string DSL: ?$paging(0,20)&species(Al,O)
            params = {
                "$paging": f"(0,{limit})",
                "format": "json",
            }
            # Simple heuristic: if query looks like elements, use species filter
            clean = query.strip().replace(" ", "").replace(",", "")
            if all(c.isalpha() for c in clean):
                params["species"] = f"({clean})"
            else:
                params["$search"] = query

            data: Any = await self._get("/", params=params, use_cache=True)
            entries = data if isinstance(data, list) else data.get("entries", [])
            results: list[dict[str, Any]] = []
            for item in entries[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "auid": item.get("auid", ""),
                    "aurl": item.get("aurl", ""),
                    "species": item.get("species", ""),
                    "catalog": catalog,
                    "source": "aflow",
                })
            return results
        except Exception as e:
            logger.warning("AFLOW search error: %s", e)
            return []

    async def get_properties(self, aurl: str) -> dict[str, Any]:
        """Fetch properties for a material by its AFLOW URL.

        Args:
            aurl: AFLOW URL (e.g. 'aflowlib.duke.edu:AFLOWDATA/ICSD_WEB...').
        """
        try:
            data = await self._get(f"/{aurl}", params={"format": "json"}, use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("AFLOW properties error: %s", e)
            return {}
