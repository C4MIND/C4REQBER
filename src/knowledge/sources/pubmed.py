from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from .base import BaseSourceAdapter


logger = logging.getLogger("c44tcdi.knowledge.multi_source")


class PubmedAdapter(BaseSourceAdapter):
    """PubMed E-utilities — 36M+ biomedical citations."""

    @property
    def source_id(self) -> str:
        return "pubmed"

    async def search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Search."""
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        async with httpx.AsyncClient(timeout=5.0) as client:
            search_resp = await client.get(
                f"{base}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": min(limit, 100),
                    "retmode": "json",
                    "sort": "relevance",
                },
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []

            fetch_resp = await client.get(
                f"{base}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "xml",
                },
            )
            fetch_resp.raise_for_status()
            return self._normalize(fetch_resp.text, id_list)

    def _normalize(self, xml_text: str, id_list: list[str]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
            for article in root.findall(".//PubmedArticle"):
                pmid = ""
                pmid_el = article.find(".//PMID")
                if pmid_el is not None and pmid_el.text:
                    pmid = pmid_el.text.strip()
                title_el = article.find(".//ArticleTitle")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                abstract_el = article.find(".//AbstractText")
                abstract = abstract_el.text.strip() if abstract_el is not None and abstract_el.text else ""
                authors: list[str] = []
                for author_el in article.findall(".//Author"):
                    last = author_el.find("LastName")
                    fore = author_el.find("ForeName")
                    parts = []
                    if last is not None and last.text:
                        parts.append(last.text.strip())
                    if fore is not None and fore.text:
                        parts.append(fore.text.strip())
                    if parts:
                        authors.append(" ".join(parts))
                year = 0
                date_el = article.find(".//PubDate")
                if date_el is not None:
                    year_el = date_el.find("Year")
                    if year_el is not None and year_el.text:
                        try:
                            year = int(year_el.text.strip())
                        except ValueError:
                            pass
                doi = ""
                for eid_el in article.findall(".//ArticleId"):
                    if eid_el.get("IdType") == "doi":
                        doi = eid_el.text.strip() if eid_el.text else ""
                journal_el = article.find(".//Journal/Title")
                journal = journal_el.text.strip() if journal_el is not None and journal_el.text else ""
                result.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "doi": doi,
                    "pmid": pmid,
                    "venue": journal,
                    "citation_count": 0,
                    "source": "pubmed",
                    "source_name": "PubMed",
                    "sources": ["PubMed"],
                })
        except ET.ParseError as e:
            logger.debug("PubMed XML parse error: %s", e)
        return result
