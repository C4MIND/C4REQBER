"""
GitHub Code Search Client.
License: Public repositories (MIT/Apache/AGPL)
"""

from __future__ import annotations

import logging
import os
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.github")


class GitHubSearchClient:
    """
    GitHub Code Search Client.

    License: Public repositories only
    API: api.github.com (optional token for higher rate limits)
    Rate Limit: 60 req/hr (unauth), 5000 req/hr (auth)
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = "") -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        if not self.token:
            logger.info(
                "GITHUB_TOKEN not set. Rate limited to 60 req/hr. "
                "Get token at https://github.com/settings/tokens"
            )
        self._client: Any = None
        if HAS_HTTPX:
            headers = {"Accept": "application/vnd.github.v3+json"}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            self._client = httpx.AsyncClient(timeout=30.0, headers=headers)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> GitHubSearchClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def search_code(self, query: str, max_results: int = 50) -> list[dict]:
        """
        Search GitHub code.

        Args:
            query: Search query (supports GitHub search syntax)
            max_results: Maximum number of results

        Returns:
            List of code result dictionaries with keys:
            - code_id, name, path, repository, url, html_url, score
        """
        if not HAS_HTTPX:
            logger.warning("httpx not installed. Install: pip install httpx")
            return []

        url = f"{self.BASE_URL}/search/code"
        params = {"q": query, "per_page": min(max_results, 100)}

        try:
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                repo = item.get("repository", {})
                results.append(
                    {
                        "code_id": str(item.get("sha", "")),
                        "name": item.get("name", ""),
                        "path": item.get("path", ""),
                        "repository": repo.get("full_name", ""),
                        "url": item.get("url", ""),
                        "html_url": item.get("html_url", ""),
                        "score": item.get("score", 0.0),
                        "license": repo.get("license", {}).get("spdx_id", ""),
                        "source": "github_code",
                    }
                )
            return results

        except Exception as e:
            logger.warning("GitHub code search error: %s", e)
            return []

    async def search_repos(self, query: str, max_results: int = 50) -> list[dict]:
        """
        Search GitHub repositories.

        Args:
            query: Search query (supports GitHub search syntax)
            max_results: Maximum number of results

        Returns:
            List of repository dictionaries with keys:
            - repo_id, name, full_name, description, url, stars, forks, language
        """
        if not HAS_HTTPX:
            return []

        url = f"{self.BASE_URL}/search/repositories"
        params = {"q": query, "per_page": min(max_results, 100), "sort": "stars"}

        try:
            response = await self._client.get(url, params=params)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append(
                    {
                        "repo_id": str(item.get("id", "")),
                        "name": item.get("name", ""),
                        "full_name": item.get("full_name", ""),
                        "description": item.get("description", "") or "",
                        "url": item.get("html_url", ""),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language", "") or "",
                        "license": (item.get("license") or {}).get("spdx_id", ""),
                        "topics": item.get("topics", []),
                        "source": "github_repo",
                    }
                )
            return results

        except Exception as e:
            logger.warning("GitHub repo search error: %s", e)
            return []

    async def get_readme(self, owner: str, repo: str) -> str:
        """
        Get README content for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            README content (decoded from base64) or empty string
        """
        if not HAS_HTTPX:
            return ""

        import base64

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"

        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            content = data.get("content", "")
            if content:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            return ""

        except Exception as e:
            logger.warning("GitHub get_readme error: %s", e)
            return ""

    async def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get repository info."""
        if not HAS_HTTPX:
            return {}

        url = f"{self.BASE_URL}/repos/{owner}/{repo}"

        try:
            response = await self._client.get(url)  # type: ignore[union-attr]
            response.raise_for_status()
            data = response.json()

            return {
                "repo_id": str(data.get("id", "")),
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description", "") or "",
                "url": data.get("html_url", ""),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language", "") or "",
                "license": (data.get("license") or {}).get("spdx_id", ""),
                "topics": data.get("topics", []),
                "source": "github_repo",
            }

        except Exception as e:
            logger.warning("GitHub get_repo_info error: %s", e)
            return {}
