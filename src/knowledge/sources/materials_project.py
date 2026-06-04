"""
c4reqber: Materials Project Client

Access to DFT-calculated materials properties.
License: Free API key required
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.materials")


class MaterialsProjectClient(BaseP6Client):
    """Materials Project REST API client."""

    BASE_URL = "https://api.materialsproject.org"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("MATERIALS_PROJECT_API_KEY", "")
        headers = {"X-API-KEY": self.api_key} if self.api_key else {}
        super().__init__(headers=headers)

    async def search_materials(self, elements: list[str], limit: int = 20) -> list[dict[str, Any]]:
        """Search materials by constituent elements."""
        if not self.api_key:
            logger.warning("MATERIALS_PROJECT_API_KEY not set")
            return []
        try:
            data = await self._get("/materials/core/", params={"elements": ",".join(elements), "limit": limit})
            materials = []
            for item in data.get("data", []):
                materials.append({
                    "material_id": item.get("material_id"),
                    "formula": item.get("formula_pretty", ""),
                    "source": "materials_project",
                })
            return materials
        except Exception as e:
            logger.warning("Materials Project search error: %s", e)
            return []

    async def get_properties(self, material_id: str) -> dict[str, Any]:
        """Get properties for a material."""
        if not self.api_key:
            return {}
        try:
            data = await self._get(f"/materials/core/{material_id}")
            return data.get("data", {})
        except Exception as e:
            logger.warning("Materials Project properties error: %s", e)
            return {}
