"""
ORCID API Client — Async HTTP with Rate Limiting

License: ✅ Open Access (public data)
Coverage: 15M+ researcher profiles
API: pub.orcid.org/v3.0 (no key required for public API)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import Any


try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger("c4_cdi_turbo.knowledge.orcid")

ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$")


class AsyncORCIDClient:
    """
    Async ORCID Public API Client.

    License: ✅ Open Access (public data)
    Coverage: 15M+ researcher profiles
    Rate Limit: ~2 requests/sec (polite usage)
    """

    BASE_URL = "https://pub.orcid.org/v3.0"
    RATE_LIMIT = 2.0

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")

        self.client_id = client_id or os.getenv("ORCID_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("ORCID_CLIENT_SECRET", "")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> AsyncORCIDClient:
        headers = {"Accept": "application/json"}
        self._client = httpx.AsyncClient(timeout=self._timeout, headers=headers)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_time = self._last_request + (1.0 / self.RATE_LIMIT) - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request = time.monotonic()

    def _validate_orcid(self, orcid_id: str) -> bool:
        return bool(ORCID_REGEX.match(orcid_id))

    async def get_profile(self, orcid_id: str) -> dict[str, Any] | None:
        """
        Get researcher profile by ORCID ID.

        Args:
            orcid_id: ORCID ID in format 0000-0000-0000-0000

        Returns:
            Profile dictionary or None
        """
        await self._rate_limit()

        orcid_clean = orcid_id.replace(" ", "").upper()
        if not self._validate_orcid(orcid_clean):
            logger.warning("Invalid ORCID ID format: %s", orcid_id)
            return None

        try:
            assert self._client is not None
            response = await self._client.get(f"{self.BASE_URL}/{orcid_clean}/record")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._parse_profile(response.json())

        except Exception as e:
            logger.warning("ORCID profile error: %s", e)
            return None

    def _parse_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        profile: dict[str, Any] = {
            "orcid_id": "",
            "name": "",
            "given_names": "",
            "family_name": "",
            "biography": "",
            "keywords": [],
            "affiliations": [],
            "works_count": 0,
            "works": [],
            "source": "orcid",
        }

        orcid_id = data.get("orcid-identifier", {})
        profile["orcid_id"] = orcid_id.get("path", "")

        name = data.get("person", {}).get("name", {})
        if name:
            given = name.get("given-names", {}).get("value", "")
            family = name.get("family-name", {}).get("value", "")
            profile["given_names"] = given
            profile["family_name"] = family
            profile["name"] = f"{given} {family}".strip()

        bio = data.get("person", {}).get("biography", {})
        if bio:
            profile["biography"] = bio.get("content", "")

        keywords = data.get("person", {}).get("keywords", {}).get("keyword", [])
        for kw in keywords:
            content = kw.get("keyword-content", {})
            if content and content.get("value"):
                profile["keywords"].append(content["value"])

        employments = data.get("activities-summary", {}).get("employments", {}).get("employment-summary", [])
        for emp in employments:
            org = emp.get("organization", {})
            if org:
                profile["affiliations"].append(
                    {
                        "name": org.get("name", ""),
                        "city": org.get("address", {}).get("city", ""),
                        "country": org.get("address", {}).get("country", ""),
                    }
                )

        works = data.get("activities-summary", {}).get("works", {}).get("group", [])
        profile["works_count"] = len(works)

        for work_group in works[:20]:
            work_summary = work_group.get("work-summary", [])
            if work_summary:
                work = work_summary[0]
                title = work.get("title", {}).get("title", {}).get("value", "")
                year = 0
                pub_date = work.get("publication-date", {})
                if pub_date:
                    year_str = pub_date.get("year", {}).get("value", "")
                    if year_str:
                        try:
                            year = int(year_str)
                        except ValueError:
                            pass

                doi = ""
                external_ids = work.get("external-ids", {}).get("external-id", [])
                for ext_id in external_ids:
                    if ext_id.get("external-id-type") == "doi":
                        doi = ext_id.get("external-id-value", "")
                        break

                profile["works"].append(
                    {
                        "title": title,
                        "year": year,
                        "doi": doi,
                        "type": work.get("type", ""),
                    }
                )

        return profile

    async def search(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search ORCID for researcher profiles.

        Note: Public API has limited search. For full search,
        use Member API with credentials.

        Args:
            query: Search query (name, keywords, etc.)
            max_results: Maximum number of results

        Returns:
            List of profile dictionaries (limited data from search)
        """
        await self._rate_limit()

        try:
            assert self._client is not None
            params: dict[str, str | int] = {"q": query, "rows": min(max_results, 100)}
            response = await self._client.get(
                f"{self.BASE_URL}/search/", params=params
            )
            response.raise_for_status()
            return self._parse_search_results(response.json())

        except Exception as e:
            logger.warning("ORCID search error: %s", e)
            return []

    def _parse_search_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for result in data.get("result", []):
            orcid_id = result.get("orcid-identifier", {}).get("path", "")
            given_names = result.get("given-names", {}).get("value", "")
            family_name = result.get("family-names", {}).get("value", "")

            results.append(
                {
                    "orcid_id": orcid_id,
                    "name": f"{given_names} {family_name}".strip(),
                    "given_names": given_names,
                    "family_name": family_name,
                    "source": "orcid",
                }
            )

        return results

    async def get_works(self, orcid_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get works."""
        await self._rate_limit()

        orcid_clean = orcid_id.replace(" ", "").upper()
        if not self._validate_orcid(orcid_clean):
            return []

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/{orcid_clean}/works"
            )
            response.raise_for_status()
            return self._parse_works(response.json())[:max_results]

        except Exception as e:
            logger.warning("ORCID works error: %s", e)
            return []

    def _parse_works(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        works = []
        for group in data.get("group", []):
            work_summary = group.get("work-summary", [])
            if work_summary:
                work = work_summary[0]
                title = work.get("title", {}).get("title", {}).get("value", "")

                year = 0
                pub_date = work.get("publication-date", {})
                if pub_date:
                    year_str = pub_date.get("year", {}).get("value", "")
                    if year_str:
                        try:
                            year = int(year_str)
                        except ValueError:
                            pass

                doi = ""
                external_ids = work.get("external-ids", {}).get("external-id", [])
                for ext_id in external_ids:
                    if ext_id.get("external-id-type") == "doi":
                        doi = ext_id.get("external-id-value", "")
                        break

                journal = ""
                journal_title = work.get("journal-title", {})
                if journal_title:
                    journal = journal_title.get("value", "")

                works.append(
                    {
                        "title": title,
                        "doi": doi,
                        "year": year,
                        "journal": journal,
                        "type": work.get("type", ""),
                        "source": "orcid",
                    }
                )

        return works

    async def get_education(self, orcid_id: str) -> list[dict[str, Any]]:
        """Get education history for a researcher."""
        await self._rate_limit()

        orcid_clean = orcid_id.replace(" ", "").upper()
        if not self._validate_orcid(orcid_clean):
            return []

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/{orcid_clean}/educations"
            )
            response.raise_for_status()
            return self._parse_education(response.json())

        except Exception as e:
            logger.warning("ORCID education error: %s", e)
            return []

    def _parse_education(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        education = []
        for edu in data.get("education-summary", []):
            org = edu.get("organization", {})
            start_date = edu.get("start-date", {})
            end_date = edu.get("end-date", {})

            start_year = start_date.get("year", {}).get("value", "") if start_date else ""
            end_year = end_date.get("year", {}).get("value", "") if end_date else ""

            education.append(
                {
                    "institution": org.get("name", ""),
                    "city": org.get("address", {}).get("city", ""),
                    "country": org.get("address", {}).get("country", ""),
                    "department": edu.get("department-name", ""),
                    "degree": edu.get("role-title", ""),
                    "start_year": start_year,
                    "end_year": end_year,
                    "source": "orcid",
                }
            )

        return education

    async def get_employment(self, orcid_id: str) -> list[dict[str, Any]]:
        """Get employment history for a researcher."""
        await self._rate_limit()

        orcid_clean = orcid_id.replace(" ", "").upper()
        if not self._validate_orcid(orcid_clean):
            return []

        try:
            assert self._client is not None
            response = await self._client.get(
                f"{self.BASE_URL}/{orcid_clean}/employments"
            )
            response.raise_for_status()
            return self._parse_employment(response.json())

        except Exception as e:
            logger.warning("ORCID employment error: %s", e)
            return []

    def _parse_employment(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        employment = []
        for emp in data.get("employment-summary", []):
            org = emp.get("organization", {})
            start_date = emp.get("start-date", {})
            end_date = emp.get("end-date", {})

            start_year = start_date.get("year", {}).get("value", "") if start_date else ""
            end_year = end_date.get("year", {}).get("value", "") if end_date else ""

            employment.append(
                {
                    "organization": org.get("name", ""),
                    "city": org.get("address", {}).get("city", ""),
                    "country": org.get("address", {}).get("country", ""),
                    "department": emp.get("department-name", ""),
                    "title": emp.get("role-title", ""),
                    "start_year": start_year,
                    "end_year": end_year,
                    "source": "orcid",
                }
            )

        return employment

    async def get_researcher(self, orcid_id: str) -> dict[str, Any]:
        """Get researcher profile by ORCID ID (alias for get_profile)."""
        result = await self.get_profile(orcid_id)
        return result or {}

    async def search_by_name(self, name: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search researchers by name (alias for search)."""
        return await self.search(name, max_results)


class ORCIDClient:
    """
    Sync ORCID API Client (backward compatibility).
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._async_client = AsyncORCIDClient(client_id, client_secret, timeout)

    def __enter__(self) -> ORCIDClient:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def get_profile(self, orcid_id: str) -> dict[str, Any] | None:
        """Get profile."""
        async def _get() -> dict[str, Any] | None:
            async with AsyncORCIDClient() as client:
                return await client.get_profile(orcid_id)

        return asyncio.run(_get())

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search."""
        async def _search() -> list[dict[str, Any]]:
            async with AsyncORCIDClient() as client:
                return await client.search(query, max_results)

        return asyncio.run(_search())

    def get_works(self, orcid_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Get works."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncORCIDClient() as client:
                return await client.get_works(orcid_id, max_results)

        return asyncio.run(_get())

    def get_researcher(self, orcid_id: str) -> dict[str, Any] | None:
        """Get researcher."""
        async def _get() -> dict[str, Any] | None:
            async with AsyncORCIDClient() as client:
                return await client.get_researcher(orcid_id)

        return asyncio.run(_get())

    def search_by_name(self, name: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search by name."""
        async def _search() -> list[dict[str, Any]]:
            async with AsyncORCIDClient() as client:
                return await client.search_by_name(name, max_results)

        return asyncio.run(_search())

    def get_education(self, orcid_id: str) -> list[dict[str, Any]]:
        """Get education."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncORCIDClient() as client:
                return await client.get_education(orcid_id)

        return asyncio.run(_get())

    def get_employment(self, orcid_id: str) -> list[dict[str, Any]]:
        """Get employment."""
        async def _get() -> list[dict[str, Any]]:
            async with AsyncORCIDClient() as client:
                return await client.get_employment(orcid_id)

        return asyncio.run(_get())
