"""BibSonomy adapter — social bookmarking and publication sharing API.

BibSonomy (bibsonomy.org) is a social bookmark and publication management
system from University of Kassel, online since 2006. REST API for publications,
bookmarks, and tags.

API base: https://www.bibsonomy.org/api
Auth: HTTP Basic (username:apikey)
Docs: https://www.bibsonomy.org/help/doc/api.html

Per official docs, the API is Java-based (org.bibsonomy.model.logic package).
A Python REST client exists at bitbucket.org/bibsonomy/bibsonomy-python.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger(__name__)

_BASE = "https://www.bibsonomy.org"


class BibsonomyAdapter(BaseSourceAdapter):
    """BibSonomy REST API adapter for academic publication search.

    Connects to BibSonomy's Java REST API. Supports searching for
    publications by keyword, by tag, and by user.
    """

    def __init__(
        self,
        api_key: str | None = None,
        username: str | None = None,
    ) -> None:
        import os
        api_key = api_key or os.getenv("BIBSONOMY_API_KEY")
        super().__init__(api_key)
        self.username = username or os.getenv("BIBSONOMY_USERNAME", "public")
        self.timeout = 15.0

    @property
    def source_id(self) -> str:
        return "bibsonomy"

    @property
    def available(self) -> bool:
        return True

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    def _auth(self) -> httpx.BasicAuth | None:
        if self.api_key and self.username:
            return httpx.BasicAuth(self.username, self.api_key)
        return None

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search BibSonomy publications matching the query.

        Uses BibSonomy's full-text search via Lucene backend.

        Returns list of normalized paper dicts.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{_BASE}/api/posts",
                    headers=self._headers(),
                    auth=self._auth(),
                    params={
                        "q": query,
                        "format": "json",
                        "resourcetype": "publication",
                        "end": min(limit, 50),
                    },
                )
                if resp.status_code != 200:
                    logger.debug("BibSonomy returned HTTP %d", resp.status_code)
                    return []
                data = resp.json()
                posts = data.get("posts", {}).get("post", [])
                if isinstance(posts, dict):
                    posts = [posts]
                return self._normalize(posts)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.debug("BibSonomy unreachable: %s", e)
            return []
        except Exception as e:
            logger.warning("BibSonomy search error: %s", e)
            return []

    async def search_tags(self, tag: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search by one or more hash tags (BibSonomy-native feature)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{_BASE}/api/tags/{tag}/posts",
                    headers=self._headers(),
                    auth=self._auth(),
                    params={
                        "format": "json",
                        "end": min(limit, 50),
                    },
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                posts = data.get("posts", {}).get("post", [])
                if isinstance(posts, dict):
                    posts = [posts]
                return self._normalize(posts)
        except Exception as e:
            logger.debug("BibSonomy tag search failed: %s", e)
            return []

    async def user_posts(self, username: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get publications by a specific BibSonomy user."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{_BASE}/api/users/{username}/posts",
                    headers=self._headers(),
                    auth=self._auth(),
                    params={
                        "format": "json",
                        "resourcetype": "publication",
                        "end": min(limit, 50),
                    },
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                posts = data.get("posts", {}).get("post", [])
                if isinstance(posts, dict):
                    posts = [posts]
                return self._normalize(posts)
        except Exception as e:
            logger.debug("BibSonomy user posts failed: %s", e)
            return []

    def _normalize(self, posts: list[dict]) -> list[dict[str, Any]]:
        """Convert BibSonomy API response to normalized paper records."""
        results = []
        for post in posts:
            bibtex = post.get("bibtex", post)
            description = post.get("description", "")
            if isinstance(description, dict):
                description = description.get("value", "")
            authors_raw = bibtex.get("author", bibtex.get("editor", ""))
            if isinstance(authors_raw, str):
                authors = [a.strip() for a in authors_raw.split(" and ")]
            else:
                authors = []
            results.append({
                "title": bibtex.get("title", description)[:200],
                "authors": authors,
                "year": str(bibtex.get("year", "") or bibtex.get("pubyear", "")),
                "venue": bibtex.get("journal", bibtex.get("booktitle", "")),
                "url": post.get("href", bibtex.get("url", "")),
                "doi": bibtex.get("doi", bibtex.get("prismdoi", "")),
                "source": "bibsonomy",
                "tags": self._extract_tags(post),
            })
        return results

    @staticmethod
    def _extract_tags(post: dict) -> list[str]:
        tags = post.get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        return [
            t.get("name", "") if isinstance(t, dict) else str(t)
            for t in (tags if isinstance(tags, list) else [tags])
        ]

    async def test_connection(self) -> dict[str, Any]:
        """Test API connectivity."""
        try:
            results = await self.search("test", limit=1)
            return {"healthy": True, "results_found": len(results)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
