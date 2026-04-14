"""
TURBO-CDI: arXiv Adapter
Search and retrieve papers from arXiv
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ArxivPaper:
    """arXiv paper metadata."""

    id: str
    title: str
    abstract: str
    authors: List[str]
    published: str
    updated: str
    categories: List[str]
    pdf_url: str
    primary_category: str


class ArxivAdapter:
    """
    Adapter for arXiv API.

    Rate limit: 1 request per 3 seconds recommended
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self.last_request_time = 0

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",  # relevance, lastUpdatedDate, submittedDate
        sort_order: str = "descending",
    ) -> List[ArxivPaper]:
        """
        Search arXiv for papers.

        Args:
            query: Search query (arXiv query syntax)
            max_results: Maximum papers to return (max 100)
            sort_by: Sort criteria
            sort_order: ascending or descending

        Returns:
            List of ArxivPaper objects
        """
        # Rate limiting
        import time

        current_time = time.time()
        if current_time - self.last_request_time < 3:
            time.sleep(3 - (current_time - self.last_request_time))

        # Build query
        params = {
            "search_query": query,
            "start": 0,
            "max_results": min(max_results, 100),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TURBO-CDI/2.1"})

            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode()
                self.last_request_time = time.time()
                return self._parse_feed(data)

        except Exception as e:
            print(f"arXiv search error: {e}")
            return []

    def search_by_category(
        self, category: str, max_results: int = 10
    ) -> List[ArxivPaper]:
        """Search papers in a specific category."""
        query = f"cat:{category}"
        return self.search(query, max_results)

    def get_recent(
        self, category: str = "quant-ph", days: int = 7, max_results: int = 20
    ) -> List[ArxivPaper]:
        """Get recent papers in a category."""
        # arXiv doesn't have direct date filtering in API
        # So we sort by date and take first N
        return self.search(
            f"cat:{category}",
            max_results=max_results,
            sort_by="submittedDate",
            sort_order="descending",
        )

    def _parse_feed(self, xml_data: str) -> List[ArxivPaper]:
        """Parse arXiv Atom feed."""
        papers = []

        try:
            root = ET.fromstring(xml_data)

            # Define namespace
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            for entry in root.findall("atom:entry", ns):
                # Skip if this is the totalResults entry
                if entry.find("atom:title", ns) is None:
                    continue

                title = entry.find("atom:title", ns).text or ""
                title = title.replace("\n", " ").strip()

                abstract = entry.find("atom:summary", ns).text or ""
                abstract = abstract.replace("\n", " ").strip()

                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns)
                    if name is not None and name.text:
                        authors.append(name.text)

                # Get ID
                id_elem = entry.find("atom:id", ns)
                paper_id = id_elem.text if id_elem is not None else ""

                # Get dates
                published = entry.find("atom:published", ns)
                published_str = published.text if published is not None else ""

                updated = entry.find("atom:updated", ns)
                updated_str = updated.text if updated is not None else ""

                # Get categories
                categories = []
                primary_category = ""
                for cat in entry.findall("atom:category", ns):
                    term = cat.get("term", "")
                    if term:
                        categories.append(term)
                        if not primary_category:
                            primary_category = term

                # Get PDF link
                pdf_url = ""
                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")
                        break

                papers.append(
                    ArxivPaper(
                        id=paper_id,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        published=published_str,
                        updated=updated_str,
                        categories=categories,
                        pdf_url=pdf_url,
                        primary_category=primary_category,
                    )
                )

        except ET.ParseError as e:
            print(f"XML parse error: {e}")

        return papers

    def format_for_context(self, papers: List[ArxivPaper]) -> str:
        """Format papers as context for LLM."""
        if not papers:
            return "No relevant papers found."

        context = f"Recent research context ({len(papers)} papers):\n\n"

        for i, paper in enumerate(papers[:5], 1):  # Top 5
            context += f"[{i}] {paper.title}\n"
            context += f"    Authors: {', '.join(paper.authors[:3])}"
            if len(paper.authors) > 3:
                context += f" et al. ({len(paper.authors)} total)"
            context += "\n"
            context += f"    Abstract: {paper.abstract[:300]}...\n\n"

        return context


# Common arXiv categories
ARXIV_CATEGORIES = {
    "physics": {
        "quant-ph": "Quantum Physics",
        "cond-mat": "Condensed Matter",
        "hep-th": "High Energy Physics - Theory",
        "gr-qc": "General Relativity and Quantum Cosmology",
        "astro-ph": "Astrophysics",
    },
    "cs": {
        "cs.AI": "Artificial Intelligence",
        "cs.LG": "Machine Learning",
        "cs.CL": "Computation and Language (NLP)",
        "cs.CV": "Computer Vision",
        "cs.RO": "Robotics",
    },
    "math": {
        "math.CO": "Combinatorics",
        "math.CT": "Category Theory",
        "math.DS": "Dynamical Systems",
        "math.GR": "Group Theory",
    },
    "biology": {
        "q-bio.BM": "Biomolecules",
        "q-bio.CB": "Cell Behavior",
        "q-bio.GN": "Genomics",
        "q-bio.MN": "Molecular Networks",
    },
    "interdisciplinary": {
        "physics.chem-ph": "Chemical Physics",
        "physics.bio-ph": "Biological Physics",
        "cs.CE": "Computational Engineering",
        "stat.ML": "Machine Learning (Statistics)",
    },
}
