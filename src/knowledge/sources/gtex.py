"""
c4reqber: GTEx Portal Client

Access to genotype-tissue expression data, eQTLs, gene expression.
License: Open access, no API key required
Docs: https://gtexportal.org/api/v2/redoc
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.gtex")


class GTExClient(BaseP6Client):
    """GTEx Portal REST API v2 client."""

    BASE_URL = "https://gtexportal.org/api/v2"

    async def search_gene(
        self,
        gene_symbol: str,
        page: int = 0,
        items_per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """Search genes by symbol (e.g., "BRCA1", "TP53")."""
        try:
            data = await self._get(
                "/reference/gene",
                params={"geneId": gene_symbol, "page": page, "itemsPerPage": items_per_page, "format": "json"},
            )
            return data.get("data", [])
        except Exception as e:
            logger.warning("GTEx gene search error: %s", e)
            return []

    async def get_expression(
        self,
        gene_id: str,
        tissue_site_detail_id: str = "",
    ) -> list[dict[str, Any]]:
        """Get median gene expression by tissue."""
        params: dict[str, Any] = {"gencodeId": gene_id, "format": "json"}
        if tissue_site_detail_id:
            params["tissueSiteDetailId"] = tissue_site_detail_id
        try:
            data = await self._get("/expression/medianGeneExpression", params=params)
            return data.get("data", [])
        except Exception as e:
            logger.warning("GTEx expression error: %s", e)
            return []

    async def get_eqtl(
        self,
        gene_id: str,
        tissue_site_detail_id: str,
        variant_id: str = "",
    ) -> list[dict[str, Any]]:
        """Fetch eQTL data for a gene in a tissue."""
        params: dict[str, Any] = {
            "gencodeId": gene_id,
            "tissueSiteDetailId": tissue_site_detail_id,
            "format": "json",
        }
        if variant_id:
            params["variantId"] = variant_id
        try:
            data = await self._get("/association/dyneqtl", params=params)
            return data.get("data", [])
        except Exception as e:
            logger.warning("GTEx eQTL error: %s", e)
            return []

    async def list_tissues(self) -> list[dict[str, Any]]:
        """List available tissues."""
        try:
            data = await self._get("/dataset/tissueSiteDetail")
            return data.get("data", [])
        except Exception as e:
            logger.warning("GTEx tissues error: %s", e)
            return []
