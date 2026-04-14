"""
Unit tests for domain entities.
"""

import pytest
from datetime import datetime
from turbo_cdi.domain.entities import (
    KnowledgeCorpus,
    CorpusId,
    Fact,
    Theory,
    Anomaly,
    AnomalyType,
    Severity,
)


class TestKnowledgeCorpus:
    """Test KnowledgeCorpus entity"""

    def test_creation(self):
        """Test basic corpus creation"""
        corpus = KnowledgeCorpus(id="test_corpus", name="Test Corpus", domain="physics")

        assert corpus.id == "test_corpus"
        assert corpus.name == "Test Corpus"
        assert corpus.domain == "physics"
        assert corpus.fact_count == 0
        assert corpus.theory_count == 0

    def test_add_fact(self):
        """Test adding facts to corpus"""
        corpus = KnowledgeCorpus(id="test_corpus", name="Test Corpus", domain="physics")

        fact = Fact(
            id="fact_1", statement="E = mc²", source="Einstein, 1905", year=1905, domain="physics"
        )

        new_corpus = corpus.add_fact(fact)

        # Original corpus unchanged (immutability)
        assert corpus.fact_count == 0
        # New corpus has the fact
        assert new_corpus.fact_count == 1
        assert fact in new_corpus.facts

    def test_validation(self):
        """Test corpus validation"""
        with pytest.raises(ValueError, match="Corpus name cannot be empty"):
            KnowledgeCorpus(id="test", name="", domain="physics")

        with pytest.raises(ValueError, match="Corpus domain cannot be empty"):
            KnowledgeCorpus(id="test", name="Test", domain="")

    def test_immutability(self):
        """Test that corpus is immutable"""
        corpus = KnowledgeCorpus(id="test", name="Test", domain="physics")

        # Facts is frozenset, should be immutable
        with pytest.raises(AttributeError):
            corpus.facts.add(Fact(id="x", statement="x", source="x", domain="x"))


class TestFact:
    """Test Fact entity"""

    def test_creation(self):
        """Test fact creation"""
        fact = Fact(
            id="fact_1",
            statement="Gravity attracts masses",
            source="Newton",
            year=1687,
            domain="physics",
            confidence=0.95,
        )

        assert fact.id == "fact_1"
        assert fact.confidence == 0.95

    def test_validation(self):
        """Test fact validation"""
        with pytest.raises(ValueError, match="Fact statement cannot be empty"):
            Fact(id="x", statement="", source="x", domain="x")

        with pytest.raises(ValueError, match="Confidence must be between"):
            Fact(id="x", statement="x", source="x", domain="x", confidence=1.5)


class TestAnomaly:
    """Test Anomaly entity"""

    def test_creation(self):
        """Test anomaly creation"""
        anomaly = Anomaly(
            id="anom_1",
            corpus_id="corpus_1",
            type=AnomalyType.EMPIRICAL,
            fact_statement="Earth is flat",
            theory_name="Spherical Earth Theory",
            conflict_description="Observation contradicts theory",
            criticality=Severity.HIGH,
        )

        assert anomaly.id == "anom_1"
        assert anomaly.type == AnomalyType.EMPIRICAL
        assert anomaly.criticality == Severity.HIGH
        assert isinstance(anomaly.detected_at, datetime)
