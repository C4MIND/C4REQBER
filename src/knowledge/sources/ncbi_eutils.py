"""
c4reqber: NCBI E-utilities Client

Access to Gene, GEO, ClinVar, dbGaP via NCBI E-utilities.
License: Free (API key optional, increases rate limits)
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.ncbi")


class NCBIEUtilsClient(BaseP6Client):
    """NCBI E-utilities API client."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: str = "", email: str = "") -> None:
        self.api_key = api_key or os.getenv("NCBI_API_KEY", "")
        self.email = email or os.getenv("NCBI_EMAIL", "c4reqber@localhost")
        super().__init__()

    async def search(
        self,
        db: str,
        term: str,
        retmax: int = 20,
    ) -> list[dict[str, Any]]:
        """Search an NCBI database."""
        params: dict[str, Any] = {
            "db": db,
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "email": self.email,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            data = await self._get("/esearch.fcgi", params=params)
            idlist = data.get("esearchresult", {}).get("idlist", [])
            return [{"uid": uid, "source": f"ncbi_{db}"} for uid in idlist]
        except Exception as e:
            logger.warning("NCBI search error: %s", e)
            return []

    async def summary(self, db: str, id_list: list[str]) -> list[dict[str, Any]]:
        """Fetch summaries for IDs."""
        if not id_list:
            return []
        params: dict[str, Any] = {
            "db": db,
            "id": ",".join(id_list),
            "retmode": "json",
            "email": self.email,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            data = await self._get("/esummary.fcgi", params=params)
            results = []
            for uid, doc in data.get("result", {}).items():
                if uid == "uids":
                    continue
                title = doc.get("title", doc.get("name", ""))
                results.append({"uid": uid, "title": title, "source": f"ncbi_{db}"})
            return results
        except Exception as e:
            logger.warning("NCBI summary error: %s", e)
            return []
