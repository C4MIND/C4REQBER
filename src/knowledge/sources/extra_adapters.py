from __future__ import annotations


"""Extra source adapters for clients not yet wrapped."""

import logging
from typing import Any

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class CiniiAdapter(BaseSourceAdapter):
    """CiNii — Japanese academic database."""

    @property
    def source_id(self) -> str:
        return "cinii"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.cinii_client import CiNiiClient

            client = CiNiiClient()
            import asyncio

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: client.search(query, limit=limit))
            return [
                {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 0),
                    "abstract": r.get("description", "")[:500],
                    "doi": r.get("doi", ""),
                    "url": r.get("link", ""),
                    "source": "cinii",
                    "source_name": "CiNii",
                    "citation_count": 0,
                    "type": "article",
                }
                for r in results
            ]
        except Exception as e:
            logger.debug("CiNii error: %s", e)
            return []


class GithubAdapter(BaseSourceAdapter):
    """GitHub — code repositories."""

    @property
    def source_id(self) -> str:
        return "github"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.github_client import GitHubSearchClient

            client = GitHubSearchClient()
            results = await client.search_repos(query, max_results=limit)
            return [
                {
                    "title": r.get("full_name", ""),
                    "authors": [r.get("owner", "")],
                    "year": 0,
                    "abstract": r.get("description", "")[:500],
                    "doi": "",
                    "url": r.get("html_url", ""),
                    "source": "github",
                    "source_name": "GitHub",
                    "citation_count": r.get("stargazers_count", 0),
                    "type": "repository",
                }
                for r in results
            ]
        except Exception as e:
            logger.debug("GitHub error: %s", e)
            return []


class DatasetsAdapter(BaseSourceAdapter):
    """Dataset repositories (Kaggle, HuggingFace, etc.)."""

    @property
    def source_id(self) -> str:
        return "datasets"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.dataset_clients import ZenodoClient

            client = ZenodoClient()
            results = await client.search(query, max_results=limit)
            return [
                {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 0),
                    "abstract": r.get("description", "")[:500],
                    "doi": r.get("doi", ""),
                    "url": r.get("url", ""),
                    "source": "datasets",
                    "source_name": "Datasets",
                    "citation_count": 0,
                    "type": "dataset",
                }
                for r in results
            ]
        except Exception as e:
            logger.debug("Datasets error: %s", e)
            return []


class RsciAdapter(BaseSourceAdapter):
    """RSCI — Russian Science Citation Index."""

    @property
    def source_id(self) -> str:
        return "rsci"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.rsci_client import RSCIClient

            client = RSCIClient()
            import asyncio

            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: client.search(query, limit=limit))
            return [
                {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 0),
                    "abstract": r.get("abstract", "")[:500],
                    "doi": r.get("doi", ""),
                    "url": r.get("url", ""),
                    "source": "rsci",
                    "source_name": "RSCI",
                    "citation_count": 0,
                    "type": "article",
                }
                for r in results
            ]
        except Exception as e:
            logger.debug("RSCI error: %s", e)
            return []


class ScimaticAdapter(BaseSourceAdapter):
    """SciMatic — scientific social network."""

    @property
    def source_id(self) -> str:
        return "scimatic"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.scimatic_client import SciMaticClient

            client = SciMaticClient(api_key=self.api_key or "")
            if not client.api_key:
                return [{"error": "SCIMATIC_API_KEY required"}]
            import asyncio

            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, lambda: client.search(query))
            if isinstance(raw, dict) and raw.get("error"):
                return [{"error": str(raw.get("error"))}]
            # SciMatic returns dict, extract papers list
            results = raw.get("papers", []) if isinstance(raw, dict) else raw
            if not isinstance(results, list):
                return []
            return [
                {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 0),
                    "abstract": r.get("abstract", "")[:500],
                    "doi": r.get("doi", ""),
                    "url": r.get("url", ""),
                    "source": "scimatic",
                    "source_name": "SciMatic",
                    "citation_count": 0,
                    "type": "article",
                }
                for r in results[:limit]
            ]
        except Exception as e:
            logger.debug("SciMatic error: %s", e)
            return [{"error": str(e)}]


class ArxivggAdapter(BaseSourceAdapter):
    """arXiv.gg — arXiv mirror with extra features."""

    @property
    def source_id(self) -> str:
        return "arxivgg"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.arxivgg_client import ArxivGGClient

            async with ArxivGGClient() as client:
                results = await client.search(query, max_results=limit)
            return [
                {
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": r.get("year", 0),
                    "abstract": r.get("abstract", "")[:500],
                    "doi": r.get("doi", ""),
                    "url": r.get("url", ""),
                    "source": "arxivgg",
                    "source_name": "arXiv.gg",
                    "citation_count": 0,
                    "type": "preprint",
                }
                for r in results
            ]
        except Exception as e:
            logger.debug("arXiv.gg error: %s", e)
            return [{"error": str(e)}]


class WolframAdapter(BaseSourceAdapter):
    """Wolfram Alpha short-answer adapter."""

    @property
    def source_id(self) -> str:
        return "wolfram"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.sources.wolfram import search_sources

            # Prefer instance key when orchestrator injected it
            if self.api_key:
                import os

                os.environ.setdefault("WOLFRAM_APP_ID", self.api_key)
            results = await search_sources(query, max_results=limit)
            for r in results:
                r.setdefault("type", "web")
                r.setdefault("source", "wolfram")
            return results
        except Exception as e:
            logger.debug("Wolfram error: %s", e)
            return [{"error": str(e)}]


class UniprotAdapter(BaseSourceAdapter):
    """UniProt protein search (no key)."""

    @property
    def source_id(self) -> str:
        return "uniprot"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.sources.uniprot import UniProtClient

            client = UniProtClient()
            raw = await client.search(query, size=min(limit, 25))
            out: list[dict[str, Any]] = []
            for item in raw[:limit]:
                out.append(
                    {
                        "title": item.get("uniProtkbId") or item.get("primaryAccession") or query,
                        "authors": [],
                        "year": None,
                        "abstract": str(item.get("proteinDescription", ""))[:500],
                        "url": f"https://www.uniprot.org/uniprotkb/{item.get('primaryAccession', '')}",
                        "source": "uniprot",
                        "type": "article",
                    }
                )
            return out
        except Exception as e:
            logger.debug("UniProt error: %s", e)
            return [{"error": str(e)}]


class ScholarApiAdapter(BaseSourceAdapter):
    """ScholarAPI paid academic search."""

    @property
    def source_id(self) -> str:
        return "scholarapi"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.scholarapi_client import ScholarAPIClient

            client = ScholarAPIClient(api_key=self.api_key or "")
            raw = await client.search(query, max_results=limit)
            out: list[dict[str, Any]] = []
            for r in raw[:limit]:
                out.append(
                    {
                        "title": r.get("title", ""),
                        "authors": r.get("authors", []),
                        "year": r.get("year"),
                        "abstract": (r.get("abstract") or r.get("snippet") or "")[:500],
                        "url": r.get("url", ""),
                        "doi": r.get("doi", ""),
                        "source": "scholarapi",
                        "type": "article",
                    }
                )
            return out
        except Exception as e:
            logger.debug("ScholarAPI error: %s", e)
            return [{"error": str(e)}]
