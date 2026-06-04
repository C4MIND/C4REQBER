"""
c4reqber: PubChem Client

Access to chemical structures, bioactivity, properties.
License: Free, no API key required
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.pubchem")


class PubChemClient(BaseP6Client):
    """PubChem PUG-REST API client."""

    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    async def search_compound(self, name: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search compounds by name."""
        try:
            data = await self._get(f"/compound/name/{name}/JSON")
            compounds = []
            for pc in data.get("PC_Compounds", [])[:max_results]:
                cid = None
                for id_info in pc.get("id", {}).get("id", []):
                    if "cid" in id_info:
                        cid = id_info["cid"]
                compounds.append({"cid": cid, "source": "pubchem"})
            return compounds
        except Exception as e:
            logger.warning("PubChem search error: %s", e)
            return []

    async def get_properties(self, cid: int, properties: list[str] | None = None) -> dict[str, Any]:
        """Get properties for a compound."""
        props = ",".join(properties or ["MolecularFormula", "MolecularWeight", "CanonicalSMILES"])
        try:
            data = await self._get(f"/compound/cid/{cid}/property/{props}/JSON")
            return data.get("PropertyTable", {}).get("Properties", [{}])[0]
        except Exception as e:
            logger.warning("PubChem properties error: %s", e)
            return {}
