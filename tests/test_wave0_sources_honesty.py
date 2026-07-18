"""Regression tests for Wave-0 honesty fixes (sources + query shaping)."""

from __future__ import annotations

from src.knowledge.contact_email import contact_email
from src.knowledge.orchestrator import MultiSourceSearcher
from src.llm.model_assignment import normalize_model_id
from src.pipeline.config import PipelineConfig
from src.pipeline.quality import QualityGates
from src.plugins.unified_registry import WebSearchPlugin


def test_web_search_plugin_returns_empty_not_example_com() -> None:
    results = WebSearchPlugin().execute("anything", max_results=5)
    assert results == []
    assert not any("example.com" in str(r) for r in results)


def test_shape_search_query_truncates_long_russian_prompt() -> None:
    long_ru = (
        "Исследовать влияние нейронных сетей на диагностику заболеваний "
        "сердечно-сосудистой системы с учётом клинических протоколов и "
        "мета-анализов за последние десять лет " * 20
    )
    shaped = MultiSourceSearcher._shape_search_query(
        MultiSourceSearcher.__new__(MultiSourceSearcher), long_ru, max_len=200
    )
    assert len(shaped) <= 200
    assert "example.com" not in shaped
    assert len(shaped.split()) >= 3


def test_contact_email_never_example_com() -> None:
    assert "example.com" not in contact_email().lower()


def test_normalize_bare_openai_model() -> None:
    assert normalize_model_id("gpt-4o-mini") == "openai/gpt-4o-mini"


def test_quality_gates_hard_fail_dummy_sources() -> None:
    gates = QualityGates(PipelineConfig(name="test"))
    result = gates.check_sources(
        [
            {"title": "Result 0", "url": "http://example.com/0", "source": "web"},
            {"title": "Result 1", "url": "http://example.com/1", "source": "web"},
        ]
    )
    assert result.passed is False
    assert result.score == 0.0
