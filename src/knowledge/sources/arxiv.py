from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


def _extract_doi(text: str) -> str | None:
    m = re.search(r"(10\.\d{4,}/[^\s]+)", text)
    return m.group(1).rstrip(".,;:") if m else None


class ArxivAdapter(BaseSourceAdapter):
    """arXiv — 2M+ preprints, physics/CS/math."""

    @property
    def source_id(self) -> str:
        return "arxiv"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        url = "https://export.arxiv.org/api/query"
        params: dict[str, Any] = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 100),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return self._normalize(resp.text)

    def _normalize(self, xml_text: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }
            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                abstract_el = entry.find("atom:summary", ns)
                abstract = abstract_el.text.strip() if abstract_el is not None and abstract_el.text else ""
                authors: list[str] = []
                for author_el in entry.findall("atom:author", ns):
                    name_el = author_el.find("atom:name", ns)
                    if name_el is not None and name_el.text:
                        authors.append(name_el.text.strip())
                id_text = ""
                id_el = entry.find("atom:id", ns)
                if id_el is not None and id_el.text:
                    id_text = id_el.text.strip()
                arxiv_id = id_text.replace("http://arxiv.org/abs/", "").strip()
                published = ""
                pub_el = entry.find("atom:published", ns)
                if pub_el is not None and pub_el.text:
                    published = pub_el.text.strip()
                year = int(published[:4]) if len(published) >= 4 else 0
                doi_link = ""
                for link_el in entry.findall("atom:link", ns):
                    href = link_el.get("href", "")
                    if "doi.org" in href:
                        doi_link = href
                doi = _extract_doi(doi_link) or ""
                result.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "doi": doi,
                    "arxiv_id": arxiv_id,
                    "venue": "arXiv",
                    "citation_count": 0,
                    "source": "arxiv",
                    "source_name": "arXiv",
                    "sources": ["arXiv"],
                })
        except ET.ParseError as e:
            logger.debug("arXiv XML parse error: %s", e)
        return result
