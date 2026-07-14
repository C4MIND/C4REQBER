"""Tests for hypothesis ranking module."""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from src.discovery.ranking.cost_model import CostModel
from src.discovery.ranking.eig_estimator import EIGEstimator
from src.discovery.ranking.mcdm_ranker import MCDMRanker, RankedHypothesis
from src.discovery.ranking.orchestrator import rank_hypotheses
from src.discovery.ranking.prior_scorer import PriorScorer


class TestPriorScorer:
    def test_score_returns_all_criteria(self) -> None:
        scorer = PriorScorer()
        result = scorer.score({"text": "Hypothesis"}, [])
        assert set(result.keys()) == {"novelty", "plausibility", "formalizability", "falsifiability"}
        assert all(0.0 <= v <= 1.0 for v in result.values())

    def test_novelty_with_empty_literature(self) -> None:
        scorer = PriorScorer()
        result = scorer.score({"text": "Test"}, [])
        assert result["novelty"] == 1.0

    def test_formalizability_detects_math(self) -> None:
        scorer = PriorScorer()
        result = scorer.score({"text": "forall x, P(x) implies Q(x)"}, [])
        assert result["formalizability"] > 0.5

    def test_falsifiability_detects_testable(self) -> None:
        scorer = PriorScorer()
        result = scorer.score({"text": "X increases Y by 20%"}, [])
        assert result["falsifiability"] > 0.4

    def test_cosine_sim(self) -> None:
        a = np.array([1.0, 0.0])
        b = np.array([1.0, 0.0])
        assert PriorScorer._cosine_sim(a, b) == pytest.approx(1.0)

        c = np.array([0.0, 1.0])
        assert PriorScorer._cosine_sim(a, c) == pytest.approx(0.0)


class TestEIGEstimator:
    def test_estimate_returns_0_to_1(self) -> None:
        est = EIGEstimator()
        result = est.estimate({"text": "test"}, "physics")
        assert 0.0 <= result <= 1.0

    def test_estimate_with_unavailable_simulator(self) -> None:
        est = EIGEstimator()
        result = est.estimate({"text": "test"}, "unknown_domain")
        assert 0.0 <= result <= 1.0


class TestCostModel:
    def test_estimate_returns_all_fields(self) -> None:
        model = CostModel()
        result = model.estimate({"text": "Some hypothesis text"})
        assert set(result.keys()) == {"llm_cost_usd", "sim_cost_usd", "data_cost_usd", "total_usd"}
        assert result["total_usd"] == pytest.approx(result["llm_cost_usd"] + result["sim_cost_usd"] + result["data_cost_usd"])

    def test_cost_increases_with_languages(self) -> None:
        model = CostModel()
        r1 = model.estimate({"text": "test"}, {"languages": 1})
        r3 = model.estimate({"text": "test"}, {"languages": 3})
        assert r3["total_usd"] > r1["total_usd"]


class TestMCDMRanker:
    def test_rank_empty(self) -> None:
        ranker = MCDMRanker()
        assert ranker.rank([]) == []

    def test_rank_single(self) -> None:
        ranker = MCDMRanker()
        result = ranker.rank([{"text": "H1"}], criteria={"eig": [0.5], "novelty": [0.5], "plausibility": [0.5], "falsifiability": [0.5]})
        assert len(result) == 1
        assert result[0].rank == 1

    def test_rank_multiple(self) -> None:
        ranker = MCDMRanker()
        hyps = [{"text": "H1"}, {"text": "H2"}, {"text": "H3"}]
        criteria = {
            "eig": [0.9, 0.5, 0.1],
            "novelty": [0.5, 0.5, 0.5],
            "plausibility": [0.5, 0.5, 0.5],
            "falsifiability": [0.5, 0.5, 0.5],
        }
        result = ranker.rank(hyps, criteria=criteria)
        assert result[0].hypothesis["text"] == "H1"  # highest EIG
        assert result[2].hypothesis["text"] == "H3"  # lowest EIG

    def test_weight_normalization(self) -> None:
        ranker = MCDMRanker(weights={"eig": 2.0, "novelty": 2.0})
        assert pytest.approx(sum(ranker.weights.values())) == 1.0

    def test_cost_inverse_prefers_cheaper(self) -> None:
        ranker = MCDMRanker()
        hyps = [{"text": "H1"}, {"text": "H2"}]
        criteria = {"eig": [0.5, 0.5], "novelty": [0.5, 0.5], "plausibility": [0.5, 0.5], "falsifiability": [0.5, 0.5]}
        costs = [{"total_usd": 10.0}, {"total_usd": 1.0}]
        result = ranker.rank(hyps, criteria=criteria, costs=costs)
        assert result[0].hypothesis["text"] == "H2"  # cheaper


class TestRankHypothesesOrchestrator:
    @pytest.mark.anyio(backend="asyncio")
    async def test_empty_hypotheses(self) -> None:
        result = await rank_hypotheses([], {})
        assert result == []

    @pytest.mark.anyio(backend="asyncio")
    async def test_ranks_hypotheses(self) -> None:
        hyps = [
            {"text": "H1: X causes Y"},
            {"text": "H2: Z affects W"},
        ]
        result = await rank_hypotheses(hyps, {"literature": [], "domain": "physics"})
        assert len(result) <= 3
        assert all(isinstance(r, RankedHypothesis) for r in result)

    @pytest.mark.anyio(backend="asyncio")
    async def test_respects_max_simulations(self) -> None:
        hyps = [{"text": f"H{i}"} for i in range(10)]
        result = await rank_hypotheses(hyps, {}, max_simulations=2)
        assert len(result) == 2
