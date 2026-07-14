"""Tests for Contradiction Miner — Contradiction Detector."""

from __future__ import annotations

from src.contradiction_miner.detector import (
    Contradiction,
    ContradictionDetector,
    ContradictionResult,
    detect_contradictions,
)
from src.contradiction_miner.extractor import Claim


def _make_claim(cid: str, subject: str, predicate: str, polarity: str = "positive") -> Claim:
    return Claim(
        id=cid,
        text=f"{subject} {predicate}",
        subject=subject,
        predicate=predicate,
        polarity=polarity,
        confidence=0.7,
    )


class TestContradiction:
    def test_default_evidence(self):
        c = Contradiction(claim_a="A", claim_b="B", type="direct", confidence=0.9)
        assert c.evidence == ""


class TestContradictionResult:
    def test_empty_claims(self):
        result = detect_contradictions([])
        assert result.total_pairs_checked == 0
        assert result.contradiction_rate == 0
        assert result.contradictions == []

    def test_single_claim(self):
        result = detect_contradictions([_make_claim("C0", "X", "is good")])
        assert result.total_pairs_checked == 0
        assert result.contradiction_rate == 0


class TestContradictionDetector:
    def setup_method(self):
        self.detector = ContradictionDetector()

    def test_direct_negation_same_subject(self):
        claims = [
            _make_claim("C0", "Coffee", "is beneficial", "positive"),
            _make_claim("C1", "Coffee", "is not beneficial", "negative"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) == 1
        assert result.contradictions[0].type == "direct"
        assert result.contradictions[0].confidence == 0.9

    def test_direct_negation_different_subjects(self):
        claims = [
            _make_claim("C0", "Coffee", "is beneficial", "positive"),
            _make_claim("C1", "Tea", "is not beneficial", "negative"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) == 0

    def test_opposite_pair_increase_decrease(self):
        claims = [
            _make_claim("C0", "Coffee", "increases", "positive"),
            _make_claim("C1", "Coffee", "decreases", "positive"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) >= 1
        found = any(c.type == "polarity" and c.evidence == "increase vs decrease" for c in result.contradictions)
        assert found

    def test_opposite_pair_improve_worsen(self):
        claims = [
            _make_claim("C0", "Diet", "improves", "positive"),
            _make_claim("C1", "Diet", "worsens", "positive"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) >= 1

    def test_opposite_pair_swapped_order(self):
        claims = [
            _make_claim("C0", "Drug", "decreases", "positive"),
            _make_claim("C1", "Drug", "increases", "positive"),
        ]
        result = self.detector.detect(claims)
        found = any(
            c.evidence in ("decrease vs increase", "increase vs decrease")
            for c in result.contradictions
        )
        assert found

    def test_polarity_mismatch(self):
        claims = [
            _make_claim("C0", "Sunlight", "is healthy", "positive"),
            _make_claim("C1", "Sunlight", "is dangerous", "negative"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) >= 1

    def test_no_contradiction_between_compatible_claims(self):
        claims = [
            _make_claim("C0", "Coffee", "increases heart rate", "positive"),
            _make_claim("C1", "Coffee", "improves memory", "positive"),
        ]
        result = self.detector.detect(claims)
        assert result.contradictions == []

    def test_has_negation_detection(self):
        assert self.detector._has_negation("is not beneficial") is True
        assert self.detector._has_negation("is beneficial") is False
        assert self.detector._has_negation("never works") is True

    def test_multiple_pairs_contradiction_rate(self):
        claims = [
            _make_claim("C0", "A", "is good", "positive"),
            _make_claim("C1", "A", "is not good", "negative"),
            _make_claim("C2", "B", "is fine", "positive"),
        ]
        result = self.detector.detect(claims)
        assert result.total_pairs_checked == 3
        assert result.contradiction_rate > 0

    def test_two_claims_one_contradiction(self):
        claims = [
            _make_claim("C0", "X", "is effective", "positive"),
            _make_claim("C1", "X", "is not effective", "negative"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) >= 1
        assert result.total_pairs_checked == 1

    def test_detect_contradictions_function(self):
        claims = [
            _make_claim("C0", "Exercise", "improves health", "positive"),
            _make_claim("C1", "Exercise", "worsens health", "negative"),
        ]
        result = detect_contradictions(claims)
        assert isinstance(result, ContradictionResult)
        assert len(result.contradictions) >= 1

    def test_negation_word_never(self):
        claims = [
            _make_claim("C0", "Treatment", "never works", "negative"),
            _make_claim("C1", "Treatment", "works well", "positive"),
        ]
        result = self.detector.detect(claims)
        assert len(result.contradictions) >= 1

    def test_cause_prevent_opposite(self):
        claims = [
            _make_claim("C0", "Vaccine", "causes disease", "positive"),
            _make_claim("C1", "Vaccine", "prevents disease", "positive"),
        ]
        result = self.detector.detect(claims)
        found = any(c.evidence == "cause vs prevent" or c.evidence == "prevent vs cause" for c in result.contradictions)
        assert found
