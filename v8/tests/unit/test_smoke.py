"""
Smoke tests to verify basic functionality works.
"""

import pytest
from turbo_cdi.domain.entities import KnowledgeCorpus, Fact, Theory
from turbo_cdi.infrastructure.config import Settings
from turbo_cdi.infrastructure.config.container import Container


def test_imports():
    """Test that all main modules can be imported"""
    from turbo_cdi.domain.entities import CorpusId, AnomalyType
    from turbo_cdi.domain.repositories import DiscoveryRepository
    from turbo_cdi.application.use_cases import DiscoverKnowledgeUseCase
    from turbo_cdi.infrastructure.external import LLMClient, CorpusValidatorImpl

    # If we get here without exceptions, imports work
    assert True


def test_settings_creation():
    """Test that settings can be created"""
    settings = Settings()
    assert settings.database_url.startswith("sqlite")
    assert settings.llm_timeout > 0


def test_container_creation():
    """Test that DI container can be created"""
    settings = Settings()
    container = Container(config=settings)

    # Should be able to access properties without errors
    assert hasattr(container, "config")
    assert hasattr(container, "discovery_repository")


def test_entity_creation():
    """Test that domain entities can be created"""
    corpus = KnowledgeCorpus(id="test", name="Test Corpus", domain="test")

    fact = Fact(id="fact_1", statement="Test statement", source="Test source", domain="test")

    theory = Theory(id="theory_1", name="Test Theory", principles=("Principle 1", "Principle 2"))

    assert corpus.id == "test"
    assert fact.statement == "Test statement"
    assert theory.name == "Test Theory"


def test_entity_immutability():
    """Test that entities are properly immutable"""
    corpus = KnowledgeCorpus(id="test", name="Test", domain="test")

    # frozenset should prevent mutation
    with pytest.raises(AttributeError):
        corpus.facts.add(Fact(id="x", statement="x", source="x", domain="x"))


def test_entity_validation():
    """Test that entity validation works"""
    with pytest.raises(ValueError):
        KnowledgeCorpus(id="test", name="", domain="test")

    with pytest.raises(ValueError):
        Fact(id="test", statement="", source="test", domain="test")
