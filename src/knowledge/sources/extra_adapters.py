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
            client = SciMaticClient()
            import asyncio
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, lambda: client.search(query))
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
            return []


class ArxivggAdapter(BaseSourceAdapter):
    """arXiv.gg — arXiv mirror with extra features."""

    @property
    def source_id(self) -> str:
        return "arxivgg"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from src.knowledge.arxivgg_client import ArxivGGClient
            client = ArxivGGClient()
            # ArxivGGClient.search is async — call directly
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
            return []
