"""
Tests for src/validation/consensus_meter.py
"""
from __future__ import annotations

import sys
from pathlib import Path


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from unittest.mock import MagicMock

import pytest

from src.validation.consensus_meter import (
    ConsensusMeter,
    ConsensusScore,
    Evidence,
    EvidenceStrength,
    EvidenceType,
    get_consensus_meter,
)


@pytest.fixture
def meter():
    return ConsensusMeter()


@pytest.fixture
def sample_evidence():
    return [
        Evidence(
            source="Study A",
            type=EvidenceType.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            description="Strong evidence",
            citation_count=100,
            year=2023,
            peer_reviewed=True,
            sample_size=500,
        ),
        Evidence(
            source="Study B",
            type=EvidenceType.CONTRADICTING,
            strength=EvidenceStrength.MODERATE,
            description="Contradictory evidence",
            citation_count=20,
            year=2019,
            peer_reviewed=True,
            sample_size=50,
        ),
        Evidence(
            source="Study C",
            type=EvidenceType.NEUTRAL,
            strength=EvidenceStrength.WEAK,
            description="Neutral observation",
            citation_count=0,
            year=2021,
            peer_reviewed=False,
        ),
    ]


class TestEvidenceAndEnums:
    def test_evidence_type_values(self):
        assert EvidenceType.SUPPORTING.value == "supporting"
        assert EvidenceType.CONTRADICTING.value == "contradicting"
        assert EvidenceType.NEUTRAL.value == "neutral"
        assert EvidenceType.INCONCLUSIVE.value == "inconclusive"

    def test_evidence_strength_values(self):
        assert EvidenceStrength.STRONG.value == 3
        assert EvidenceStrength.MODERATE.value == 2
        assert EvidenceStrength.WEAK.value == 1
        assert EvidenceStrength.ANECDOTAL.value == 0

    def test_evidence_defaults(self):
        ev = Evidence(source="S", type=EvidenceType.SUPPORTING, strength=EvidenceStrength.WEAK, description="D")
        assert ev.citation_count == 0
        assert ev.year == 0
        assert ev.methodology == ""
        assert ev.sample_size is None
        assert ev.peer_reviewed is True


class TestCalculateConsensus:
    def test_empty_evidence(self, meter):
        score = meter.calculate_consensus("h1", "Test", [])
        assert score.supporting_count == 0
        assert score.contradicting_count == 0
        assert score.neutral_count == 0
        assert score.total_count == 0
        assert score.supporting_score == 0
        assert score.contradicting_score == 0
        assert score.consensus_level == "none"

    def test_basic_evidence(self, meter, sample_evidence):
        score = meter.calculate_consensus("h1", "Test", sample_evidence)
        assert score.supporting_count == 1
        assert score.contradicting_count == 1
        assert score.neutral_count == 1
        assert score.total_count == 3
        assert isinstance(score.supporting_score, float)
        assert isinstance(score.contradicting_score, float)

    def test_strong_consensus(self, meter):
        evidence = [
            Evidence(
                source="S1",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG,
                description="D1",
                citation_count=200,
                year=2023,
                peer_reviewed=True,
                sample_size=1000,
            ),
            Evidence(
                source="S2",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG,
                description="D2",
                citation_count=150,
                year=2022,
                peer_reviewed=True,
                sample_size=800,
            ),
        ]
        score = meter.calculate_consensus("h1", "H", evidence)
        assert score.consensus_level == "strong"
        assert score.supporting_score > score.contradicting_score

    def test_contested_consensus(self, meter):
        evidence = [
            Evidence(
                source="S1",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG,
                description="D1",
                citation_count=100,
                year=2023,
                peer_reviewed=True,
            ),
            Evidence(
                source="S2",
                type=EvidenceType.CONTRADICTING,
                strength=EvidenceStrength.STRONG,
                description="D2",
                citation_count=100,
                year=2023,
                peer_reviewed=True,
            ),
        ]
        score = meter.calculate_consensus("h1", "H", evidence)
        assert score.consensus_level in ["contested", "none", "weak"]

    def test_weighted_by_citations(self, meter):
        evidence = [
            Evidence(
                source="S1",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.MODERATE,
                description="D1",
                citation_count=1000,
                year=2020,
                peer_reviewed=True,
            ),
            Evidence(
                source="S2",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.MODERATE,
                description="D2",
                citation_count=0,
                year=2020,
                peer_reviewed=True,
            ),
        ]
        score = meter.calculate_consensus("h1", "H", evidence)
        assert score.supporting_score == 100.0

    def test_recency_boost(self, meter):
        old = Evidence(
            source="Old",
            type=EvidenceType.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            description="D",
            year=2010,
            peer_reviewed=True,
        )
        new = Evidence(
            source="New",
            type=EvidenceType.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            description="D",
            year=2024,
            peer_reviewed=True,
        )
        score_old = meter.calculate_consensus("h1", "H", [old])
        score_new = meter.calculate_consensus("h2", "H", [new])
        assert score_new.supporting_score >= score_old.supporting_score

    def test_methodology_scoring(self, meter):
        evidence = [
            Evidence(
                source="S1",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.WEAK,
                description="D",
                peer_reviewed=True,
                sample_size=200,
            ),
        ]
        score = meter.calculate_consensus("h1", "H", evidence)
        assert score.methodology_score == 100.0

    def test_no_peer_review(self, meter):
        evidence = [
            Evidence(
                source="S1",
                type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.WEAK,
                description="D",
                peer_reviewed=False,
            ),
        ]
        score = meter.calculate_consensus("h1", "H", evidence)
        assert score.methodology_score == 50.0


class TestRenderConsensusBar:
    def test_render_bar(self, meter, sample_evidence):
        score = meter.calculate_consensus("h1", "H", sample_evidence)
        bar = meter.render_consensus_bar(score, width=50)
        assert "[" in bar
        assert "]" in bar
        assert "Supporting" in bar or "Against" in bar

    def test_render_bar_zero_width(self, meter):
        score = meter.calculate_consensus("h1", "H", [])
        bar = meter.render_consensus_bar(score, width=10)
        assert "[" in bar
        assert "]" in bar


class TestRenderRichMeter:
    def test_render_rich(self, meter, sample_evidence):
        score = meter.calculate_consensus("h1", "H", sample_evidence)
        rich = meter.render_rich_meter(score)
        assert "Confidence:" in rich
        assert "supporting" in rich
        assert "contradicting" in rich

    def test_render_rich_unknown_level(self, meter):
        score = MagicMock()
        score.consensus_level = "unknown"
        score.confidence_score = 50.0
        score.supporting_count = 1
        score.contradicting_count = 1
        score.neutral_count = 0
        score.avg_citation_count = 0.0
        score.recency_score = 0.0
        score.methodology_score = 0.0
        rich = meter.render_rich_meter(score)
        assert "Unknown" in rich or "❓" in rich


class TestGenerateSummaryText:
    def test_all_levels(self, meter):
        for level in ["strong", "moderate", "weak", "none", "contested"]:
            score = MagicMock()
            score.consensus_level = level
            score.confidence_score = 50.0
            score.supporting_count = 5
            score.contradicting_count = 2
            text = meter.generate_summary_text(score)
            assert len(text) > 0
            assert "50%" in text or "confidence" in text

    def test_unknown_level_fallback(self, meter):
        score = MagicMock()
        score.consensus_level = "unknown"
        score.confidence_score = 50.0
        score.supporting_count = 0
        score.contradicting_count = 0
        text = meter.generate_summary_text(score)
        assert "Insufficient" in text or "No clear consensus" in text


class TestClassifyConsensus:
    def test_supporting(self, meter):
        result = meter._classify_consensus("machine learning improves prediction accuracy", "machine learning prediction accuracy improvement study")
        assert result["classification"] == "SUPPORTING"
        assert result["confidence"] > 0.6

    def test_partially_supporting(self, meter):
        result = meter._classify_consensus("machine learning improves prediction", "deep learning neural networks image classification")
        assert result["classification"] in ["PARTIALLY_SUPPORTING", "SUPPORTING", "WEAKLY_RELATED"]

    def test_unrelated(self, meter):
        result = meter._classify_consensus("quantum gravity unification", "machine learning improves prediction accuracy")
        assert result["classification"] in ["UNRELATED", "WEAKLY_RELATED"]

    def test_insufficient_data(self, meter):
        result = meter._classify_consensus("", "")
        assert result["classification"] == "INSUFFICIENT_DATA"
        assert result["confidence"] == 0.0

    def test_term_extraction(self, meter):
        result = meter._classify_consensus("gravity waves detection", "gravitational wave observation black hole merger")
        assert "jaccard_similarity" in result
        assert "term_overlap" in result
        assert "shared_terms" in result
        assert isinstance(result["shared_terms"], list)


class TestExtractEvidenceFromPapers:
    def test_with_paper_objects(self, meter):
        papers = [
            {
                "paper": MagicMock(
                    title="Test Paper",
                    abstract="This supports the hypothesis about gravity",
                    citation_count=100,
                    year=2023,
                ),
            }
        ]
        evidence = meter.extract_evidence_from_papers(papers, "gravity hypothesis")
        assert len(evidence) >= 1
        assert evidence[0].source == "Test Paper"

    def test_with_dict_papers(self, meter):
        papers = [
            {
                "title": "Dict Paper",
                "abstract": "This discusses gravity and relativity",
                "citation_count": 50,
                "year": 2022,
            }
        ]
        evidence = meter.extract_evidence_from_papers(papers, "gravity hypothesis")
        assert len(evidence) >= 1
        # Dict papers use getattr which returns default for dict keys, so source is "Unknown"
        assert evidence[0].source == "Unknown"

    def test_empty_papers(self, meter):
        evidence = meter.extract_evidence_from_papers([], "hypothesis")
        assert evidence == []

    def test_citation_strength(self, meter):
        papers = [
            {
                "paper": MagicMock(
                    title="High Cite",
                    abstract="Supports the hypothesis",
                    citation_count=100,
                    year=2023,
                ),
            }
        ]
        evidence = meter.extract_evidence_from_papers(papers, "hypothesis")
        assert evidence[0].strength == EvidenceStrength.MODERATE

        papers[0]["paper"].citation_count = 10
        evidence = meter.extract_evidence_from_papers(papers, "hypothesis")
        assert evidence[0].strength == EvidenceStrength.WEAK


class TestSingleton:
    def test_get_consensus_meter(self):
        m1 = get_consensus_meter()
        m2 = get_consensus_meter()
        assert m1 is m2
        assert isinstance(m1, ConsensusMeter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
