"""
C4REQBER: Consensus Meter
Visual for/against evidence display inspired by Consensus.app
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceType(Enum):
    """Types of evidence in scientific consensus."""

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    NEUTRAL = "neutral"
    INCONCLUSIVE = "inconclusive"


class EvidenceStrength(Enum):
    """Strength of evidence."""

    STRONG = 3
    MODERATE = 2
    WEAK = 1
    ANECDOTAL = 0


@dataclass
class Evidence:
    """A piece of evidence for or against a hypothesis."""

    source: str
    type: EvidenceType
    strength: EvidenceStrength
    description: str
    citation_count: int = 0
    year: int = 0
    methodology: str = ""
    sample_size: int | None = None
    peer_reviewed: bool = True


@dataclass
class ConsensusScore:
    """Overall consensus metrics for a hypothesis."""

    hypothesis_id: str
    hypothesis_text: str

    # Raw counts
    supporting_count: int
    contradicting_count: int
    neutral_count: int
    total_count: int

    # Weighted scores
    supporting_score: float  # 0-100
    contradicting_score: float  # 0-100

    # Derived metrics
    consensus_level: str  # "strong", "moderate", "weak", "none", "contested"
    confidence_score: float  # 0-100

    # Quality metrics
    avg_citation_count: float
    recency_score: float  # 0-100, higher = more recent evidence
    methodology_score: float  # 0-100

    # Evidence breakdown
    evidence: list[Evidence]


class ConsensusMeter:
    """
    Visual consensus meter for hypotheses.

    Inspired by Consensus.app - shows for/against evidence visually.
    """

    CONSENSUS_LEVELS = {
        "strong": (70, 100, "🟢 Strong Consensus"),
        "moderate": (50, 70, "🟡 Moderate Consensus"),
        "weak": (30, 50, "🟠 Weak Consensus"),
        "none": (0, 30, "⚪ No Consensus"),
        "contested": (-100, 0, "🔴 Contested"),
    }

    def __init__(self) -> None:
        pass

    def calculate_consensus(
        self, hypothesis_id: str, hypothesis_text: str, evidence_list: list[Evidence]
    ) -> ConsensusScore:
        """
        Calculate consensus metrics from evidence.

        Args:
            hypothesis_id: Unique ID
            hypothesis_text: The hypothesis text
            evidence_list: List of evidence items

        Returns:
            ConsensusScore with all metrics
        """
        # Count by type
        supporting = [e for e in evidence_list if e.type == EvidenceType.SUPPORTING]
        contradicting = [
            e for e in evidence_list if e.type == EvidenceType.CONTRADICTING
        ]
        neutral = [e for e in evidence_list if e.type == EvidenceType.NEUTRAL]

        # Calculate weighted scores
        def weighted_score(evidence_list: list[Evidence]) -> float:
            """Weighted score."""
            if not evidence_list:
                return 0.0

            total = 0.0
            for e in evidence_list:
                # Base weight from strength
                weight = e.strength.value

                # Boost for citations (log scale, max 2x)
                if e.citation_count > 0:
                    import math

                    weight *= 1 + min(math.log10(e.citation_count) / 10, 1.0)  # type: ignore[assignment]

                # Boost for peer review
                if e.peer_reviewed:
                    weight *= 1.5  # type: ignore[assignment]

                # Boost for recency
                if e.year >= 2020:
                    weight *= 1.2  # type: ignore[assignment]

                total += weight

            return total

        support_score = weighted_score(supporting)
        against_score = weighted_score(contradicting)

        # Normalize to 0-100
        total = support_score + against_score
        if total > 0:
            support_pct = (support_score / total) * 100
            against_pct = (against_score / total) * 100
        else:
            support_pct = 0
            against_pct = 0

        # Determine consensus level
        net_score = support_pct - against_pct
        consensus_level = "none"
        for level, (min_val, max_val, _) in self.CONSENSUS_LEVELS.items():
            if min_val <= net_score <= max_val:
                consensus_level = level
                break

        # Calculate quality metrics
        all_evidence = supporting + contradicting + neutral
        avg_citations = (
            sum(e.citation_count for e in all_evidence) / len(all_evidence)
            if all_evidence
            else 0
        )

        # Recency score (percentage from 2020+)
        recent_count = sum(1 for e in all_evidence if e.year >= 2020)
        recency_score = (recent_count / len(all_evidence) * 100) if all_evidence else 0

        # Methodology score (based on sample sizes and peer review)
        methodology_scores = []
        for e in all_evidence:
            score = 50  # Base
            if e.peer_reviewed:
                score += 30
            if e.sample_size and e.sample_size > 100:
                score += 20
            elif e.sample_size and e.sample_size > 30:
                score += 10
            methodology_scores.append(score)

        avg_methodology = (
            sum(methodology_scores) / len(methodology_scores)
            if methodology_scores
            else 0
        )

        # Overall confidence
        confidence = (support_pct + avg_methodology + recency_score) / 3

        return ConsensusScore(
            hypothesis_id=hypothesis_id,
            hypothesis_text=hypothesis_text,
            supporting_count=len(supporting),
            contradicting_count=len(contradicting),
            neutral_count=len(neutral),
            total_count=len(evidence_list),
            supporting_score=support_pct,
            contradicting_score=against_pct,
            consensus_level=consensus_level,
            confidence_score=confidence,
            avg_citation_count=avg_citations,
            recency_score=recency_score,
            methodology_score=avg_methodology,
            evidence=evidence_list,
        )

    def render_consensus_bar(self, score: ConsensusScore, width: int = 50) -> str:
        """
        Render ASCII consensus bar.

        [███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
        Supporting (35%)                    Against (15%)
        """
        support_width = int((score.supporting_score / 100) * width)
        against_width = int((score.contradicting_score / 100) * width)
        neutral_width = width - support_width - against_width

        bar = (
            "[" + "█" * support_width + "░" * neutral_width + "▒" * against_width + "]"
        )

        lines = [
            "",
            bar,
            f"Supporting ({score.supporting_score:.0f}%)"
            + " " * (width - 20)
            + f"Against ({score.contradicting_score:.0f}%)",
            "",
        ]

        return "\n".join(lines)

    def render_rich_meter(self, score: ConsensusScore) -> str:
        """Render Rich-compatible consensus meter."""

        # Get consensus level display
        level_info = self.CONSENSUS_LEVELS.get(
            score.consensus_level, (0, 0, "❓ Unknown")
        )
        level_text = level_info[2]

        lines = [
            f"[bold]{level_text}[/bold]",
            "",
            f"Confidence: [cyan]{score.confidence_score:.0f}%[/cyan]",
            f"Evidence: [green]{score.supporting_count} supporting[/green] | "
            f"[red]{score.contradicting_count} contradicting[/red] | "
            f"[yellow]{score.neutral_count} neutral[/yellow]",
            "",
            "Quality Metrics:",
            f"  • Avg citations: {score.avg_citation_count:.0f}",
            f"  • Recency: {score.recency_score:.0f}%",
            f"  • Methodology: {score.methodology_score:.0f}%",
        ]

        return "\n".join(lines)

    def generate_summary_text(self, score: ConsensusScore) -> str:
        """Generate human-readable consensus summary."""
        templates = {
            "strong": (
                f"There is strong scientific consensus ({score.confidence_score:.0f}% confidence) "
                f"supporting this hypothesis. {score.supporting_count} studies support it, "
                f"while only {score.contradicting_count} contradict it."
            ),
            "moderate": (
                f"There is moderate consensus ({score.confidence_score:.0f}% confidence) "
                f"for this hypothesis. While {score.supporting_count} studies support it, "
                f"{score.contradicting_count} studies present contradictory evidence."
            ),
            "weak": (
                f"Consensus is weak ({score.confidence_score:.0f}% confidence). "
                f"Limited evidence exists with {score.supporting_count} supporting and "
                f"{score.contradicting_count} contradicting studies."
            ),
            "none": (
                f"No clear consensus exists ({score.confidence_score:.0f}% confidence). "
                f"Insufficient evidence to evaluate this hypothesis."
            ),
            "contested": (
                f"This hypothesis is scientifically contested ({score.confidence_score:.0f}% confidence). "
                f"Significant contradictory evidence ({score.contradicting_count} studies) "
                f"challenges the {score.supporting_count} supporting studies."
            ),
        }

        return templates.get(score.consensus_level, templates["none"])

    def _classify_consensus(self, hypothesis: str, abstract: str) -> dict[str, Any]:
        """Classify consensus between hypothesis and scientific abstract."""
        import re

        def extract_terms(text: str) -> set[str]:
            """Extract terms."""
            words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
            stop_words = {"that", "with", "from", "this", "what", "when", "where", "which", "would", "could", "should", "about", "their", "there", "these", "those"}
            return {w for w in words if w not in stop_words}

        h_terms = extract_terms(hypothesis)
        a_terms = extract_terms(abstract)

        if not h_terms or not a_terms:
            return {"classification": "INSUFFICIENT_DATA", "confidence": 0.0}

        intersection = h_terms & a_terms
        union = h_terms | a_terms
        jaccard = len(intersection) / len(union) if union else 0.0

        h_set = set(h_terms)
        a_word_count = len(a_terms)
        matched = sum(1 for w in a_terms if w in h_set)
        coverage = matched / a_word_count if a_word_count > 0 else 0.0

        consensus_score = 0.4 * jaccard + 0.3 * coverage + 0.3 * min(1.0, len(intersection) / 5)

        if consensus_score > 0.6:
            classification = "SUPPORTING"
        elif consensus_score > 0.3:
            classification = "PARTIALLY_SUPPORTING"
        elif consensus_score > 0.1:
            classification = "WEAKLY_RELATED"
        else:
            classification = "UNRELATED"

        return {
            "classification": classification,
            "confidence": round(consensus_score, 3),
            "jaccard_similarity": round(jaccard, 3),
            "term_overlap": round(coverage, 3),
            "shared_terms": sorted(list(intersection))[:10],
            "method": "TERM_FREQUENCY_ANALYSIS",
            "note": "Statistical classification. For LLM-enhanced classification, configure an API provider.",
        }

    def extract_evidence_from_papers(
        self, papers: list[dict[str, Any]], hypothesis: str
    ) -> list[Evidence]:
        """
        Extract evidence from Semantic Scholar papers.

        This is a simplified version - in production would use LLM
        to classify each paper as supporting/contradicting/neutral.
        """
        evidence = []

        for paper_data in papers:
            paper = paper_data.get("paper", paper_data)

            # Simple heuristic: if hypothesis keywords in abstract, count as supporting
            # In production, use LLM for actual classification
            abstract = getattr(paper, "abstract", "") or ""
            getattr(paper, "title", "") or ""

            # Classify using term frequency analysis
            classification = self._classify_consensus(hypothesis, abstract)
            class_map = {
                "SUPPORTING": EvidenceType.SUPPORTING,
                "PARTIALLY_SUPPORTING": EvidenceType.SUPPORTING,
                "WEAKLY_RELATED": EvidenceType.NEUTRAL,
                "UNRELATED": EvidenceType.CONTRADICTING,
                "INSUFFICIENT_DATA": EvidenceType.INCONCLUSIVE,
            }
            ev_type = class_map.get(classification["classification"], EvidenceType.NEUTRAL)

            ev = Evidence(
                source=getattr(paper, "title", "Unknown"),
                type=ev_type,
                strength=EvidenceStrength.MODERATE
                if getattr(paper, "citation_count", 0) > 50
                else EvidenceStrength.WEAK,
                description=getattr(paper, "abstract", "")[:200] + "..."
                if len(getattr(paper, "abstract", "")) > 200
                else getattr(paper, "abstract", ""),
                citation_count=getattr(paper, "citation_count", 0) or 0,
                year=getattr(paper, "year", 0) or 0,
                methodology="",
                peer_reviewed=True,
            )
            evidence.append(ev)

        return evidence


def get_consensus_meter() -> ConsensusMeter:
    """Get singleton consensus meter (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("consensus_meter", ConsensusMeter)
