"""
c4reqber: ChEMBL Client

Access to bioactive molecules, SAR data, drug targets.
License: Free, no API key required
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.chembl")


class ChEMBLClient(BaseP6Client):
    """ChEMBL REST API client."""

    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    async def search_molecule(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search molecules by name or SMILES."""
        try:
            data = await self._get("/molecule", params={"q": query, "format": "json", "limit": limit})
            molecules = []
            for mol in data.get("molecules", []):
                molecules.append({
                    "chembl_id": mol.get("molecule_chembl_id"),
                    "name": mol.get("pref_name", ""),
                    "source": "chembl",
                })
            return molecules
        except Exception as e:
            logger.warning("ChEMBL search error: %s", e)
            return []

    async def get_bioactivities(self, chembl_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get bioactivity data for a molecule."""
        try:
            data = await self._get(
                "/activity",
                params={"molecule_chembl_id": chembl_id, "format": "json", "limit": limit},
            )
            return data.get("activities", [])
        except Exception as e:
            logger.warning("ChEMBL bioactivity error: %s", e)
            return []
