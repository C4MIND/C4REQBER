"""
c4reqber: DrugBank Client (Stub / Paid API)

DrugBank provides comprehensive drug and drug target data.
License: Paid subscription only — this module acts as a stub/shim
         that becomes functional when a user provides an API key.
Docs: https://docs.drugbank.com/guides/getting_started/
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.drugbank")


class DrugBankClient(BaseP6Client):
    """DrugBank API client — stub until paid key is provided.

    When DRUGBANK_API_KEY is empty, all methods return empty results
    with a warning log.  When a key is set, the client makes real calls.
    """

    BASE_URL = "https://api.drugbank.com/v1"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("DRUGBANK_API_KEY", "")
        if self.api_key:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            super().__init__(headers=headers)
        else:
            super().__init__()

    @property
    def available(self) -> bool:
        """True when a valid API key is configured."""
        return bool(self.api_key) and super().available

    def _require_key(self) -> bool:
        if not self.api_key:
            logger.warning(
                "DrugBank API key not set. "
                "Subscribe at https://docs.drugbank.com/guides/getting_started/"
            )
            return False
        return True

    async def search_drugs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search drugs by name."""
        if not self._require_key():
            return []
        try:
            data = await self._get("/drugs", params={"q": query, "per_page": limit})
            return data.get("drugs", [])
        except Exception as e:
            logger.warning("DrugBank search error: %s", e)
            return []

    async def get_drug(self, drugbank_id: str) -> dict[str, Any]:
        """Get detailed drug info by DrugBank ID (e.g., DB00001)."""
        if not self._require_key():
            return {}
        try:
            return await self._get(f"/drugs/{drugbank_id}")
        except Exception as e:
            logger.warning("DrugBank get drug error: %s", e)
            return {}

    async def get_targets(self, drugbank_id: str) -> list[dict[str, Any]]:
        """Get drug targets for a specific drug."""
        if not self._require_key():
            return []
        try:
            data = await self._get(f"/drugs/{drugbank_id}/targets")
            return data.get("targets", [])
        except Exception as e:
            logger.warning("DrugBank targets error: %s", e)
            return []

    async def search_by_structure(self, smiles: str) -> list[dict[str, Any]]:
        """Search drugs by SMILES string (structure search)."""
        if not self._require_key():
            return []
        try:
            data = await self._get("/structures", params={"smiles": smiles, "search_type": "exact"})
            return data.get("drugs", [])
        except Exception as e:
            logger.warning("DrugBank structure search error: %s", e)
            return []
