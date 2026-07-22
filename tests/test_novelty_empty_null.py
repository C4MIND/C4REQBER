"""W2: empty prior art → novelty null; gates fail-closed on zero checkable sources."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.knowledge.novelty_scorer import NoveltyScorer
from src.pipeline.config import PipelineConfig
from src.pipeline.quality import QualityGates


def test_novelty_scorer_empty_prior_art_returns_none() -> None:
    scorer = NoveltyScorer()
    assert scorer.score("Some proposed solution text", []) is None
    assert scorer.flag(None) == "NOVELTY_UNCHECKED"


def test_novelty_scorer_empty_corpus_text_returns_none() -> None:
    scorer = NoveltyScorer()
    prior = [{"title": "", "abstract": ""}, {"title": "  ", "abstract": ""}]
    with patch.object(scorer, "_get_model") as mock_get:
        mock_get.side_effect = AssertionError("model must not load for empty corpus")
        assert scorer.score("proposed text", prior) is None


def test_novelty_scorer_flag_never_coerces_null_to_score() -> None:
    scorer = NoveltyScorer()
    assert scorer.flag(None) == "NOVELTY_UNCHECKED"
    assert scorer.flag(0.85) == "POTENTIALLY_NOVEL"


def test_novelty_scorer_real_score_when_prior_present() -> None:
    scorer = NoveltyScorer()
    fake_model = MagicMock()
    emb_a = np.array([1.0, 0.0])
    emb_b = np.array([0.0, 1.0])
    fake_model.encode.side_effect = [np.array([emb_a, emb_b]), np.array([emb_b])]

    with patch.object(scorer, "_get_model", return_value=fake_model):
        score = scorer.score(
            "orthogonal hypothesis",
            [
                {"title": "Paper A", "abstract": "about A"},
                {"title": "Paper B", "abstract": "about B"},
            ],
        )
    assert score is not None
    assert 0.0 <= score <= 1.0


def test_quality_gate_zero_checkable_doi_url_hard_fails() -> None:
    gates = QualityGates(PipelineConfig(name="test", min_sources_with_url=2))
    result = gates.check_sources(
        [
            {"title": "No link paper", "source": "openalex"},
            {
                "title": "Scholar stub",
                "url": "https://scholar.google.com/scholar?q=foo",
                "source": "web",
            },
        ]
    )
    assert result.passed is False
    assert result.score == 0.0
    assert result.details.get("checkable") == 0


def test_quality_gate_checkable_doi_counts() -> None:
    gates = QualityGates(PipelineConfig(name="test", min_sources_with_url=1, min_sources=1))
    result = gates.check_sources(
        [
            {"title": "Real paper", "doi": "10.1234/abc", "source": "openalex"},
        ]
    )
    assert result.details.get("checkable") == 1
    assert result.passed is True


@pytest.mark.asyncio
async def test_synthesis_empty_sources_novelty_null() -> None:
    from src.agents.pipeline.steps.step_08_synthesis import SynthesisStep
    from src.c4.state import C4State

    step = SynthesisStep()
    router = MagicMock()
    long_solution = "word " * 450
    router.generate = MagicMock(return_value=long_solution)

    context: dict = {
        "problem": "novelty null test",
        "c4_state": C4State(0, 0, 0),
        "plugin_results": [],
        "gap_results": [],
        "quality_gate_results": {"all_passed": True},
        "perspectives": [],
        "provider_router": router,
        "cost_tracker": None,
        "sources": [],
        "max_tokens": 500,
    }

    with (
        patch("src.llm.get_gateway") as mock_gw,
        patch("src.agents.pipeline.steps.step_08_synthesis.CitationVerifier") as mock_cv,
        patch("src.agents.pipeline.steps.step_08_synthesis.NoveltyScorer") as mock_ns,
    ):
        from unittest.mock import AsyncMock

        mock_gw.return_value.generate_sync.return_value = long_solution
        mock_cv.return_value.verify = AsyncMock(return_value=[])
        mock_cv.return_value.close = AsyncMock()
        mock_ns.return_value.score.return_value = None
        mock_ns.return_value.flag.return_value = "NOVELTY_UNCHECKED"

        result = await step.execute(context)

    novelty = result.output_data.get("novelty", {})
    assert novelty.get("score") is None
    assert novelty.get("flag") == "NOVELTY_UNCHECKED"
