"""
c4reqber: re3data Client

Search re3data.org — the Registry of Research Data Repositories.
License: Free academic use (CC0)
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client

logger = logging.getLogger("c4reqber.knowledge.re3data")


class Re3dataClient(BaseP6Client):
    """re3data.org API client.

    API docs: https://www.re3data.org/api/doc
    """

    BASE_URL = "https://www.re3data.org/api/beta"
    DEFAULT_TIMEOUT = 30.0

    async def search_repositories(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search research data repositories.

        Args:
            query: Keyword (e.g. "genomics", "crystallography", "social science").
            limit: Max results.
        """
        try:
            data = await self._get(
                "/repositories",
                params={"query": query},
                use_cache=True,
            )
            # re3data returns XML by default; with Accept: application/json we get JSON
            repos = data.get("re3data", {}).get("repository", []) if isinstance(data, dict) else []
            if isinstance(repos, dict):
                repos = [repos]
            results: list[dict[str, Any]] = []
            for item in repos[:limit]:
                if not isinstance(item, dict):
                    continue
                results.append({
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "link": item.get("link", {}).get("href", "") if isinstance(item.get("link"), dict) else "",
                    "type": item.get("type", ""),
                    "subjects": item.get("subjects", []),
                    "source": "re3data",
                })
            return results
        except Exception as e:
            logger.warning("re3data search error: %s", e)
            return []

    async def get_repository(self, repo_id: str) -> dict[str, Any]:
        """Fetch detailed metadata for a repository.

        Args:
            repo_id: re3data repository ID.
        """
        try:
            data = await self._get(f"/repositories/{repo_id}", use_cache=True)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("re3data repository error: %s", e)
            return {}
