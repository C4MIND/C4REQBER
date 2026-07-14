"""
c4reqber: UniProt Client

Access to protein sequences, functions, GO annotations, structures.
License: Open access, no API key required
Docs: https://www.uniprot.org/help/programmatic_access
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.uniprot")


class UniProtClient(BaseP6Client):
    """UniProt REST API client."""

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    def __init__(self) -> None:
        super().__init__(headers={"Accept": "application/json"})

    async def search(
        self,
        query: str,
        fields: list[str] | None = None,
        size: int = 25,
    ) -> list[dict[str, Any]]:
        """Search UniProt entries."""
        params: dict[str, Any] = {"query": query, "size": size, "format": "json"}
        if fields:
            params["fields"] = ",".join(fields)
        try:
            data = await self._get("/search", params=params)
            return data.get("results", [])
        except Exception as e:
            logger.warning("UniProt search error: %s", e)
            return []

    async def get_entry(self, accession: str) -> dict[str, Any]:
        """Fetch a single UniProt entry by accession (e.g., P04637)."""
        try:
            return await self._get(f"/{accession}", params={"format": "json"})
        except Exception as e:
            logger.warning("UniProt entry error: %s", e)
            return {}

    async def get_sequence(self, accession: str) -> str:
        """Fetch FASTA sequence for a protein."""
        if not self.available:
            return ""
        url = f"{self.BASE_URL}/{accession}.fasta"
        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning("UniProt sequence error: %s", e)
            return ""

    async def map_ids(
        self,
        ids: list[str],
        from_db: str = "UniProtKB_AC-ID",
        to_db: str = "GeneID",
    ) -> dict[str, Any]:
        """Map IDs between databases using UniProt ID mapping service."""
        if not self.available:
            return {}
        try:
            job = await self._post(
                "",
                data={"ids": ",".join(ids), "from": from_db, "to": to_db},
            )
            job_id = job.get("jobId")
            if not job_id:
                return {}

            # Poll for results
            status_url = f"https://rest.uniprot.org/idmapping/status/{job_id}"
            for _ in range(30):
                status_resp = await self._client.get(status_url)  # type: ignore[union-attr]
                status_data = status_resp.json()
                if status_data.get("jobStatus") == "FINISHED":
                    result_url = f"https://rest.uniprot.org/idmapping/results/{job_id}"
                    result_resp = await self._client.get(result_url)  # type: ignore[union-attr]
                    return result_resp.json()
                await asyncio.sleep(1.0)
            return {"error": "timeout", "jobId": job_id}
        except Exception as e:
            logger.warning("UniProt ID mapping error: %s", e)
            return {}
