from __future__ import annotations

import asyncio
from typing import Any

from .base import BaseSourceAdapter
from .base_p6_adapter import BaseP6SourceAdapter


class OpenAlexAdapter(BaseSourceAdapter):
    """OpenAlex — 250M+ works, open access, free.

    Uses ``pyalex`` for robust pagination, automatic abstract reconstruction,
    and typed responses. Falls back to raw API via ``BaseP6SourceAdapter``
    if pyalex is unavailable.
    """

    @property
    def source_id(self) -> str:
        return "openalex"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from pyalex import Works

            loop = asyncio.get_event_loop()
            # pyalex is synchronous; run in executor to avoid blocking
            works = await loop.run_in_executor(
                None,
                lambda: Works()
                .search(query)
                .sort("cited_by_count", desc=True)
                .select(
                    "id,title,publication_year,abstract_inverted_index,"
                    "authorships,doi,primary_location,cited_by_count"
                )
                .get(limit),
            )
            return self._normalize(works)
        except Exception:
            # Fallback to raw BaseP6 adapter if pyalex fails
            return await self._search_raw(query, limit)

    async def _search_raw(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fallback raw API search (legacy behaviour)."""
        from .base_p6_adapter import BaseP6SourceAdapter

        raw = _OpenAlexRawAdapter(api_key=self.api_key)
        return await raw.search(query, limit)

    def _normalize(self, works: list[Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for w in works:
            # pyalex returns Work objects with attribute access
            authors = []
            for auth in getattr(w, "authorships", []) or []:
                author_obj = auth.get("author", {}) if isinstance(auth, dict) else getattr(auth, "author", {})
                if isinstance(author_obj, dict):
                    authors.append(author_obj.get("display_name", ""))
                else:
                    authors.append(getattr(author_obj, "display_name", ""))

            doi_raw = getattr(w, "doi", None) or ""
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""

            venue = getattr(w, "primary_location", None) or {}
            source_info = (venue or {}).get("source", {}) if isinstance(venue, dict) else getattr(venue, "source", {})
            venue_name = ""
            if isinstance(source_info, dict):
                venue_name = source_info.get("display_name", "")
            else:
                venue_name = getattr(source_info, "display_name", "")

            # pyalex auto-reconstructs abstract_inverted_index into .abstract
            abstract = getattr(w, "abstract", "") or ""

            result.append({
                "id": getattr(w, "id", ""),
                "title": getattr(w, "title", "") or "",
                "authors": authors,
                "year": int(getattr(w, "publication_year", 0) or 0),
                "abstract": abstract,
                "abstract_missing": not abstract,
                "doi": doi,
                "venue": venue_name,
                "citation_count": getattr(w, "cited_by_count", 0) or 0,
                "source": self.source_id,
                "source_name": "OpenAlex",
                "sources": ["OpenAlex"],
            })
        return result


class _OpenAlexRawAdapter(BaseP6SourceAdapter):
    """Legacy raw OpenAlex adapter used as fallback."""

    BASE_URL = "https://api.openalex.org"
    DEFAULT_TIMEOUT = 15.0

    @property
    def source_id(self) -> str:
        return "openalex"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "search": query,
            "per_page": min(limit, 200),
            "mailto": "c44tcdi@example.com",
            "select": "id,title,publication_year,abstract_inverted_index,authorships,doi,primary_location,cited_by_count",
        }
        data = await self._get_with_retry("/works", params=params, use_cache=True)
        return self._normalize(data.get("results", []))

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
        if not inverted_index:
            return ""
        words: dict[int, str] = {}
        for word, positions in inverted_index.items():
            if not positions:
                continue
            for pos in positions:
                words[pos] = word
        if not words:
            return ""
        return " ".join(word for _pos, word in sorted(words.items()))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in data:
            authors = []
            for auth in item.get("authorships", []):
                author_obj = auth.get("author", {}) if isinstance(auth, dict) else {}
                if isinstance(author_obj, dict):
                    authors.append(author_obj.get("display_name", ""))
            doi_raw = item.get("doi") or ""
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""
            venue = item.get("primary_location", {})
            source_info = (venue or {}).get("source", {}) if isinstance(venue, dict) else {}
            venue_name = source_info.get("display_name", "") if isinstance(source_info, dict) else ""
            result.append({
                "title": item.get("title", ""),
                "authors": authors,
                "year": int(item.get("publication_year") or 0),
                "abstract": self._reconstruct_abstract(item.get("abstract_inverted_index")),
                "abstract_missing": item.get("abstract_inverted_index") is None,
                "doi": doi,
                "venue": venue_name,
                "citation_count": item.get("cited_by_count", 0) or 0,
                "source": self.source_id,
                "source_name": "OpenAlex",
                "sources": ["OpenAlex"],
            })
        return result
