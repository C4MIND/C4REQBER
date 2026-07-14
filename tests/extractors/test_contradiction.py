"""Tests for src/extractors/contradiction.py — ContradictionExtractor."""
from __future__ import annotations

from src.extractors.contradiction import ContradictionExtractor


class TestPatterns:
    def setup_method(self):
        self.extractor = ContradictionExtractor()

    def test_high_vs_low_pattern(self):
        match = self.extractor.PATTERNS["high_vs_low"].search(
            "must be high but also low"
        )
        assert match is not None

    def test_trade_off_pattern(self):
        match = self.extractor.PATTERNS["trade_off"].search(
            "trade off between speed and accuracy"
        )
        assert match is not None

    def test_simultaneous_pattern(self):
        match = self.extractor.PATTERNS["simultaneous"].search(
            "must heat and simultaneously cool"
        )
        assert match is not None

    def test_no_match(self):
        match = self.extractor.PATTERNS["high_vs_low"].search("No contradiction here")
        assert match is None


class TestContradictionExtractor:
    def setup_method(self):
        self.extractor = ContradictionExtractor()

    def test_instantiation(self):
        assert self.extractor is not None

    def test_domain_indicators(self):
        assert "battery" in self.extractor.DOMAIN_INDICATORS
        assert "material" in self.extractor.DOMAIN_INDICATORS

    def test_extract_from_statement(self):
        result = self.extractor.extract(
            "must be strong but also light"
        )
        assert result is not None

    def test_extract_all_from_statement(self):
        results = self.extractor.extract_all(
            "must be fast but also slow"
        )
        assert isinstance(results, list)
