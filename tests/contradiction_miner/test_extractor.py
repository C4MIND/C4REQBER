"""Tests for Contradiction Miner — Claim Extractor."""

from __future__ import annotations

import pytest

from src.contradiction_miner.extractor import (
    Claim,
    ClaimExtractor,
    ExtractionResult,
    extract_claims,
)


class TestClaim:
    def test_default_values(self):
        c = Claim(id="C0", text="X is Y", subject="X", predicate="is Y", polarity="positive", confidence=0.5)
        assert c.source == ""
        assert c.section == ""

    def test_full_fields(self):
        c = Claim(
            id="C1",
            text="Coffee increases alertness",
            subject="Coffee",
            predicate="increases",
            polarity="positive",
            confidence=0.8,
            source="doi:10.1234/abc",
            section="Introduction",
        )
        assert c.source == "doi:10.1234/abc"
        assert c.section == "Introduction"


class TestExtractionResult:
    def test_empty_text(self):
        result = extract_claims("")
        assert result.total_sentences == 0
        assert result.claims_per_sentence == 0
        assert result.claims == []

    def test_whitespace_only(self):
        result = extract_claims("   ")
        assert result.total_sentences == 0
        assert result.claims == []


class TestClaimExtractor:
    def setup_method(self):
        self.extractor = ClaimExtractor()

    def test_single_claim_copula(self):
        result = self.extractor.extract("Coffee is a stimulant.")
        assert len(result.claims) == 1
        assert result.claims[0].subject == "Coffee"
        assert "is" in result.claims[0].predicate
        assert result.claims[0].confidence == 0.7

    def test_causal_claim(self):
        result = self.extractor.extract("Smoking causes lung cancer.")
        assert len(result.claims) == 1
        assert result.claims[0].predicate == "causes"

    def test_comparative_claim(self):
        result = self.extractor.extract("Exercise improves cardiovascular health.")
        assert len(result.claims) == 1
        assert result.claims[0].predicate == "improves"

    def test_multiple_sentences(self):
        result = self.extractor.extract(
            "Coffee increases alertness. Exercise improves mood. Smoking causes cancer."
        )
        assert result.total_sentences == 3
        assert len(result.claims) == 3

    def test_sentence_splitting(self):
        result = self.extractor.extract(
            "First claim here! Another claim? Final claim."
        )
        assert result.total_sentences == 3

    def test_short_sentence_filtered(self):
        result = self.extractor.extract("Coffee increases alertness. Hi.")
        assert result.total_sentences == 2
        assert len(result.claims) >= 1
        short_claim_ids = [c.id for c in result.claims if c.subject == "Hi"]
        assert len(short_claim_ids) == 0

    def test_claims_per_sentence_ratio(self):
        result = self.extractor.extract(
            "Coffee increases alertness. Exercise improves mood."
        )
        assert result.claims_per_sentence == 1.0

    def test_positive_polarity(self):
        result = self.extractor.extract("Water is essential.")
        assert result.claims[0].polarity == "positive"

    def test_negative_polarity(self):
        result = self.extractor.extract("The treatment is not effective.")
        assert result.claims[0].polarity == "negative"

    def test_evidence_suggests_pattern(self):
        result = self.extractor.extract("Evidence suggests dark matter exists.")
        assert len(result.claims) == 1
        assert result.claims[0].confidence == 0.7

    def test_claim_id_uniqueness(self):
        result = self.extractor.extract("A is B. C is D. E is F.")
        ids = [c.id for c in result.claims]
        assert len(ids) == len(set(ids))

    def test_weak_claim_confidence(self):
        result = self.extractor.extract("Something something something something.")
        assert result.claims[0].confidence == 0.3
        assert result.claims[0].predicate == "exists"


def test_extract_claims_function():
    result = extract_claims("Coffee is good. Tea is bad.")
    assert isinstance(result, ExtractionResult)
    assert len(result.claims) == 2
