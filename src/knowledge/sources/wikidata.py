from __future__ import annotations

from typing import Any

from src.knowledge.contact_email import contact_email

from .base_p6_adapter import BaseP6SourceAdapter


class WikidataAdapter(BaseP6SourceAdapter):
    """Wikidata SPARQL endpoint — knowledge graph, entities, semantic links.

    Provides entity lookup and semantic search via SPARQL queries.
    For paper search, Wikidata is indirect: we query for scholarly articles
    linked to entities, or search via Wikipedia-derived labels.
    """

    BASE_URL = "https://query.wikidata.org"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CACHE_TTL = 600.0  # 10 min — SPARQL queries are expensive

    @property
    def source_id(self) -> str:
        return "wikidata"

    def __init__(self, **kwargs: Any) -> None:
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/sparql-results+json")
        headers.setdefault("User-Agent", f"c4reqber/1.0 (mailto:{contact_email()})")
        super().__init__(headers=headers, **kwargs)

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search for scholarly articles via Wikidata SPARQL.

        Uses a broad query matching article labels, aliases, and descriptions.
        """
        escaped_query = query.replace('"', '\\"')
        sparql = f"""
        SELECT ?item ?itemLabel ?authorLabel ?pubDate ?doi ?venueLabel ?citedByCount WHERE {{
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
          ?item wdt:P31 wd:Q13442814 ;  # instance of scholarly article
                rdfs:label ?label .
          FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{escaped_query}")))
          OPTIONAL {{ ?item wdt:P50 ?author. }}
          OPTIONAL {{ ?item wdt:P577 ?pubDate. }}
          OPTIONAL {{ ?item wdt:P356 ?doi. }}
          OPTIONAL {{ ?item wdt:P1433 ?venue. }}
          OPTIONAL {{ ?item wdt:P2860 ?cited. }}
        }}
        GROUP BY ?item ?itemLabel ?authorLabel ?pubDate ?doi ?venueLabel ?citedByCount
        LIMIT {min(limit, 100)}
        """
        params = {"query": sparql}
        data = await self._get_with_retry("/sparql", params=params, use_cache=True)
        return self._normalize(data.get("results", {}).get("bindings", []))

    def _normalize(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in data:
            item_uri = item.get("item", {}).get("value", "")
            item_id = item_uri.split("/")[-1] if item_uri else ""
            if item_id in seen:
                continue
            seen.add(item_id)

            title = item.get("itemLabel", {}).get("value", "")
            author = item.get("authorLabel", {}).get("value", "")
            authors = [author] if author else []
            date_val = item.get("pubDate", {}).get("value", "")
            year = 0
            if date_val:
                try:
                    year = int(date_val.split("-")[0])
                except ValueError:
                    pass
            doi = item.get("doi", {}).get("value", "")
            if doi.startswith("http://dx.doi.org/"):
                doi = doi.replace("http://dx.doi.org/", "")
            elif doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")
            venue = item.get("venueLabel", {}).get("value", "")

            result.append(
                {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": "",
                    "doi": doi,
                    "venue": venue,
                    "citation_count": 0,  # SPARQL COUNT is expensive; skip for now
                    "source": self.source_id,
                    "source_name": "Wikidata",
                    "sources": ["Wikidata"],
                    "wikidata_id": item_id,
                }
            )
        return result

    async def entity_lookup(self, entity_id: str) -> dict[str, Any]:
        """Look up a Wikidata entity by Q-id (e.g. 'Q42' for Douglas Adams)."""
        sparql = f"""
        SELECT ?prop ?propLabel ?value ?valueLabel WHERE {{
          wd:{entity_id} ?prop ?value.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 200
        """
        params = {"query": sparql}
        return await self._get_with_retry("/sparql", params=params, use_cache=True)
