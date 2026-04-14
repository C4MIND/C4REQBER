"""
TURBO-CDI: PubMed Adapter
Search and retrieve papers from PubMed
"""

import urllib.request
import urllib.parse
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PubMedPaper:
    """PubMed paper metadata."""

    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    doi: str
    mesh_terms: List[str]


class PubMedAdapter:
    """
    Adapter for PubMed E-utilities API.

    No API key required for basic usage (rate limited)
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.last_request_time = 0

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",  # relevance, pub_date
    ) -> List[PubMedPaper]:
        """
        Search PubMed for papers.

        Args:
            query: Search query (PubMed syntax)
            max_results: Maximum papers to return
            sort: Sort order

        Returns:
            List of PubMedPaper objects
        """
        # Rate limiting (3 requests per second without key)
        import time

        current_time = time.time()
        delay = 0.34 if self.api_key else 0.4  # Slightly longer without key
        if current_time - self.last_request_time < delay:
            time.sleep(delay - (current_time - self.last_request_time))

        # Step 1: Search for IDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 100),
            "sort": sort,
            "retmode": "json",
        }

        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            search_url = (
                f"{self.BASE_URL}/esearch.fcgi?{urllib.parse.urlencode(search_params)}"
            )
            req = urllib.request.Request(search_url)

            with urllib.request.urlopen(req, timeout=30) as response:
                search_data = json.loads(response.read().decode())
                self.last_request_time = time.time()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return []

            # Step 2: Fetch details for IDs
            return self._fetch_details(id_list)

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def search_by_mesh(
        self, mesh_term: str, max_results: int = 10
    ) -> List[PubMedPaper]:
        """Search by MeSH term."""
        query = f"{mesh_term}[MeSH Terms]"
        return self.search(query, max_results)

    def get_recent(
        self, topic: str, days: int = 30, max_results: int = 20
    ) -> List[PubMedPaper]:
        """Get recent papers on a topic."""
        # PubMed date format: YYYY/MM/DD
        from datetime import datetime, timedelta

        date_cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")

        query = f"{topic} AND ({date_cutoff}[PDAT] : 3000[PDAT])"
        return self.search(query, max_results, sort="pub_date")

    def _fetch_details(self, pmids: List[str]) -> List[PubMedPaper]:
        """Fetch detailed info for PMIDs."""
        if not pmids:
            return []

        import time

        current_time = time.time()
        delay = 0.34 if self.api_key else 0.4
        if current_time - self.last_request_time < delay:
            time.sleep(delay - (current_time - self.last_request_time))

        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        if self.api_key:
            fetch_params["api_key"] = self.api_key

        try:
            fetch_url = (
                f"{self.BASE_URL}/efetch.fcgi?{urllib.parse.urlencode(fetch_params)}"
            )
            req = urllib.request.Request(fetch_url)

            with urllib.request.urlopen(req, timeout=30) as response:
                xml_data = response.read().decode()
                self.last_request_time = time.time()
                return self._parse_pubmed_xml(xml_data)

        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_data: str) -> List[PubMedPaper]:
        """Parse PubMed XML response."""
        import xml.etree.ElementTree as ET

        papers = []

        try:
            root = ET.fromstring(xml_data)

            for article in root.findall(".//PubmedArticle"):
                # PMID
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                # Title
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else ""

                # Abstract
                abstract_parts = article.findall(".//AbstractText")
                abstract = " ".join([part.text or "" for part in abstract_parts])

                # Authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    if last_name is not None:
                        name = last_name.text or ""
                        if fore_name is not None and fore_name.text:
                            name = f"{fore_name.text} {name}"
                        authors.append(name)

                # Journal
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""

                # Publication date
                pub_date_elem = article.find(".//PubDate")
                pub_date = ""
                if pub_date_elem is not None:
                    year = pub_date_elem.find("Year")
                    month = pub_date_elem.find("Month")
                    if year is not None:
                        pub_date = year.text or ""
                        if month is not None:
                            pub_date += f"-{month.text}"

                # DOI
                doi_elem = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_elem.text if doi_elem is not None else ""

                # MeSH terms
                mesh_terms = []
                for mesh in article.findall(".//MeshHeading/DescriptorName"):
                    if mesh.text:
                        mesh_terms.append(mesh.text)

                papers.append(
                    PubMedPaper(
                        pmid=pmid,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        journal=journal,
                        pub_date=pub_date,
                        doi=doi,
                        mesh_terms=mesh_terms,
                    )
                )

        except ET.ParseError as e:
            print(f"XML parse error: {e}")

        return papers

    def format_for_context(self, papers: List[PubMedPaper]) -> str:
        """Format papers as context for LLM."""
        if not papers:
            return "No relevant papers found."

        context = f"Recent biomedical research ({len(papers)} papers):\n\n"

        for i, paper in enumerate(papers[:5], 1):
            context += f"[{i}] {paper.title}\n"
            context += f"    Journal: {paper.journal} ({paper.pub_date})\n"
            context += f"    Authors: {', '.join(paper.authors[:3])}"
            if len(paper.authors) > 3:
                context += f" et al."
            context += "\n"
            if paper.abstract:
                context += f"    Abstract: {paper.abstract[:300]}...\n"
            context += "\n"

        return context


# Common PubMed search fields
PUBMED_FIELDS = {
    "ti": "Title",
    "ab": "Abstract",
    "au": "Author",
    "ta": "Journal",
    "mh": "MeSH Terms",
    "pt": "Publication Type",
    "dp": "Date of Publication",
}
