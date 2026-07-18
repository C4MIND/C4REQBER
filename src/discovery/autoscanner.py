from __future__ import annotations


"""
AutoScanner — Autonomous unsolved problems scanner.

Scans arXiv, PubMed, Brave Search for "open problem", "unsolved", "challenge"
indicators, extracts problem statements, and ranks them by discovery potential.
"""
import re
from dataclasses import dataclass, field
from typing import Any


LOCAL_PROBLEMS = [
    "catastrophic forgetting in continual learning",
    "improve solar panel efficiency beyond Shockley-Queisser limit",
    "novel antibiotic resistance mechanism",
    "reduce transformer inference cost by 10x",
    "room-temperature superconductivity",
    "CO2 capture at atmospheric concentration",
    "fusion energy plasma confinement",
    "quantum error correction for noisy qubits",
    "Alzheimer disease early detection biomarker",
    "biodegradable plastic that decomposes in seawater",
]


@dataclass
class ProblemCandidate:
    """ProblemCandidate."""

    title: str
    problem: str
    domain: str
    source: str
    year: str | None = None
    impact_score: float = 0.0
    potential_value: str = ""
    raw_paper: dict[str, Any] = field(default_factory=dict)


class AutoScanner:
    """Autonomous scanner for unsolved problems from news and literature."""

    PROBLEM_INDICATORS: list[str] = [
        "open problem",
        "unsolved",
        "remains unknown",
        "still unclear",
        "further research needed",
        "future work",
        "challenge",
        "limitation",
        "no study has",
        "has not been investigated",
        "remains unexplored",
        "few studies",
        "limited research",
        "open question",
        "unknown whether",
        "not yet",
        "contradiction",
        "paradox",
        "remains controversial",
        "further investigation required",
    ]

    DOMAIN_KEYWORDS: dict[str, list[str]] = {
        "physics": [
            "physics",
            "quantum",
            "particle",
            "cosmology",
            "astrophysics",
            "condensed matter",
            "optics",
            "fluid",
        ],
        "biology": [
            "biology",
            "gene",
            "protein",
            "cell",
            "dna",
            "rna",
            "molecular",
            "organism",
            "evolution",
        ],
        "chemistry": [
            "chemistry",
            "molecule",
            "catalyst",
            "reaction",
            "polymer",
            "synthesis",
            "electrochem",
        ],
        "medicine": [
            "medicine",
            "disease",
            "cancer",
            "therapy",
            "drug",
            "clinical",
            "patient",
            "surgery",
        ],
        "cs": [
            "algorithm",
            "machine learning",
            "neural",
            "computation",
            "ai",
            "artificial intelligence",
            "data",
        ],
        "mathematics": [
            "mathematics",
            "number theory",
            "conjecture",
            "proof",
            "topology",
            "algebra",
            "geometry",
        ],
        "materials": [
            "material",
            "alloy",
            "composite",
            "semiconductor",
            "superconductor",
            "nanomaterial",
        ],
        "energy": ["energy", "battery", "solar", "fuel", "nuclear", "renewable", "power"],
        "engineering": [
            "engineering",
            "manufacturing",
            "design",
            "robotics",
            "optimization",
            "control",
        ],
        "social": ["social", "economic", "political", "education", "policy", "behavior"],
    }

    def __init__(self, mega_db: Any = None, llm: Any = None) -> None:
        self.mega_db = mega_db
        self.llm = llm

    async def scan_unsolved_problems(
        self, domains: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Scan arXiv, PubMed, Brave Search for 'open problem', 'unsolved', 'challenge'.

        Returns top-10 problems with prospective scores.
        """
        queries = self._build_queries(domains)
        raw_candidates: list[dict[str, Any]] = []

        if self.mega_db is not None:
            for query in queries[:5]:
                try:
                    results = await self.mega_db.search_all(query, max_per_source=3)
                    extracted = self._extract_candidates(results, query)
                    raw_candidates.extend(extracted)
                except (TimeoutError, TypeError):
                    continue

        deduped = self._deduplicate(raw_candidates)
        scored = self._score_candidates(deduped)

        scored.sort(key=lambda c: c.get("prospect_score", 0), reverse=True)
        return scored[:10]

    def _build_queries(self, domains: list[str] | None) -> list[str]:
        base_queries = [
            '"open problem"',
            '"unsolved" OR "remains unknown"',
            '"future work" OR "further research"',
            '"challenge" OR "limitation"',
            '"contradiction" OR "paradox"',
        ]
        if not domains:
            return base_queries
        domainized = []
        for domain in domains:
            keywords = self.DOMAIN_KEYWORDS.get(domain, [domain])
            kw = " OR ".join(keywords[:3])
            for bq in base_queries:
                domainized.append(f"({kw}) AND ({bq})")
        return domainized[:8] if domainized else base_queries

    def _extract_candidates(
        self, results: dict[str, list[dict[str, Any]]], query: str
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for source, papers in results.items():
            for paper in papers:
                title = paper.get("title", "")
                abstract = paper.get("abstract", "") or paper.get("description", "")
                text = f"{title}. {abstract}"
                matched = self._match_indicators(text)
                if not matched:
                    continue
                sentence = self._extract_relevant_sentence(abstract, matched)
                candidates.append(
                    {
                        "title": title[:200],
                        "problem": sentence[:300],
                        "domain": self._guess_domain(title + " " + abstract),
                        "source": source,
                        "year": str(paper.get("year", "")),
                        "matched_indicator": matched,
                        "raw_paper": paper,
                    }
                )
        return candidates

    def _match_indicators(self, text: str) -> str:
        lower = text.lower()
        for indicator in self.PROBLEM_INDICATORS:
            if indicator in lower:
                return indicator
        return ""

    def _extract_relevant_sentence(self, abstract: str, indicator: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", abstract)
        for s in sentences:
            if indicator.lower() in s.lower():
                return s.strip()[:300]
        return abstract[:300]

    def _guess_domain(self, text: str) -> str:
        text_lower = text.lower()
        best_domain = "general"
        best_score = 0
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_domain = domain
        return best_domain

    def _deduplicate(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for c in candidates:
            key = c.get("title", "")[:80].lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _score_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        indicator_weights = {
            "open problem": 1.0,
            "unsolved": 0.95,
            "remains unknown": 0.90,
            "still unclear": 0.85,
            "contradiction": 0.88,
            "paradox": 0.90,
            "no study has": 0.95,
            "has not been investigated": 0.90,
            "remains unexplored": 0.90,
            "open question": 0.85,
            "unknown whether": 0.80,
            "few studies": 0.70,
            "limited research": 0.70,
            "further research needed": 0.65,
            "future work": 0.60,
            "challenge": 0.55,
            "limitation": 0.50,
        }
        for c in candidates:
            indicator = c.get("matched_indicator", "")
            base_score = indicator_weights.get(indicator, 0.45)
            title_bonus = 0.1 if indicator.lower() in c.get("title", "").lower() else 0.0
            c["prospect_score"] = round(min(1.0, base_score + title_bonus), 2)
            c["potential_value"] = self._estimate_value(c["prospect_score"])
        return candidates

    def _estimate_value(self, score: float) -> str:
        """Heuristic market-size label (not a real valuation). Prefixed for honesty."""
        if score >= 0.90:
            bucket = "$1B+"
        elif score >= 0.75:
            bucket = "$500M+"
        elif score >= 0.60:
            bucket = "$100M+"
        else:
            bucket = "$10M+"
        return f"heuristic:{bucket}"

    async def scan_local(self) -> list[dict[str, Any]]:
        """Demo-only corpus — **do not call from live discovery pipelines**.

        Prefer ``scan_from_papers`` or ``scan_unsolved_problems``.
        """
        return [
            {
                "problem": p,
                "source": "local_db",
                "discovery_potential": 0.7 + i * 0.02,
                "demo": True,
                "note": "Hardcoded demo corpus — not a live literature scan",
            }
            for i, p in enumerate(LOCAL_PROBLEMS[:5])
        ]

    async def scan_from_papers(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract open-problem candidates from real paper abstracts (no demo corpus)."""
        if not papers:
            return []
        bundled = {"pipeline": list(papers)}
        raw = self._extract_candidates(bundled, query="pipeline_papers")
        scored = self._score_candidates(self._deduplicate(raw))
        scored.sort(key=lambda c: c.get("prospect_score", 0), reverse=True)
        for c in scored:
            c["demo"] = False
            c["discovery_potential"] = float(c.get("prospect_score", 0.0))
            c["potential_value_heuristic"] = True
        return scored[:10]

    async def refine_with_llm(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Use LLM to reformulate problem statements into readable headlines."""
        if self.llm is None:
            return candidates
        for c in candidates:
            try:
                prompt = (
                    f"Reformulate this scientific open problem into a clear, "
                    f"concise 1-sentence headline (max 120 chars):\n\n"
                    f"Title: {c.get('title', '')}\n"
                    f"Problem: {c.get('problem', '')}\n\n"
                    f"Headline:"
                )
                response = self.llm.generate(prompt, temperature=0.5, max_tokens=80)
                refined = (
                    response.content if hasattr(response, "content") else str(response)
                ).strip()
                if refined:
                    c["refined_title"] = refined[:150]
            except (AttributeError, KeyError, ValueError):
                c["refined_title"] = c.get("problem", "")[:150]
        return candidates
