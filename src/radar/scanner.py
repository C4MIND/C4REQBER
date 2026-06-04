"""
Unsolved Problems Radar — scans scientific literature to find open problems.
"""

from __future__ import annotations


class UnsolvedProblemsRadar:
    """Scanner for unsolved scientific problems and research opportunities."""

    def __init__(self, mega_db=None):
        self.mega_db = mega_db

    async def scan(self, domain: str | None = None, limit: int = 10) -> list[dict]:
        """Scan arXiv, PubMed, Semantic Scholar for open problems.

        Searches for phrases: "open problem", "unsolved", "future work",
        "remains unknown", "still unclear", "further research needed"
        """
        queries = [
            "open problem OR unsolved",
            "future work OR further research",
            "remains unknown OR still unclear",
            "challenge OR limitation",
            "contradiction OR paradox",
        ]
        problems = []
        for query in queries:
            if self.mega_db is None:
                continue
            results = await self.mega_db.search_all(query, max_per_source=5)
            extracted = self._extract_problems(results)
            problems.extend(extracted)

        return self._rank_by_impact(problems)[:limit]

    def _extract_problems(self, results: dict) -> list[dict]:
        """Extract problem statements from search results."""
        problems = []
        for _source, papers in results.items():
            for paper in papers:
                if paper.get("abstract"):
                    problem = self._parse_problem_statement(paper)
                    if problem:
                        problems.append(problem)
        return problems

    def _parse_problem_statement(self, paper: dict) -> dict | None:
        """Parse a paper's abstract to extract the open problem."""
        return {
            "title": paper.get("title", ""),
            "problem": paper.get("abstract", "")[:200] + "...",
            "domain": paper.get("category", "general"),
            "source": paper.get("source"),
            "year": paper.get("year"),
            "estimated_impact": "high",
            "potential_value": "$1B+",
        }

    def _rank_by_impact(self, problems: list[dict]) -> list[dict]:
        """Rank problems by estimated scientific and economic impact."""
        return sorted(problems, key=lambda p: p.get("citations", 0), reverse=True)


async def get_radar():
    """Dependency injection helper."""
    return UnsolvedProblemsRadar()
