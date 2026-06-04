"""
Tests for Abduction Engine — Inference to the Best Explanation (Peirce).

Covers: Observation, Hypothesis, AbductionResult, ibe_score, retroduction,
select_best_explanation, rank_hypotheses, AbductionEngine.
"""
from __future__ import annotations

import math

import pytest

from src.discovery.abduction import (
    AbductionEngine,
    AbductionResult,
    Hypothesis,
    Observation,
    ibe_score,
    rank_hypotheses,
    retroduction,
    select_best_explanation,
)


class TestObservation:
    def test_create_observation_defaults(self):
        o = Observation(description="The sky is blue")
        assert o.description == "The sky is blue"
        assert o.confidence == 1.0
        assert o.source == ""

    def test_create_observation_custom(self):
        o = Observation(description="X", confidence=0.8, source="sensor")
        assert o.confidence == 0.8
        assert o.source == "sensor"

    def test_observation_confidence_out_of_range(self):
        with pytest.raises(ValueError):
            Observation(description="X", confidence=1.5)
        with pytest.raises(ValueError):
            Observation(description="X", confidence=-0.1)

    def test_observation_to_dict_not_needed(self):
        o = Observation(description="test", metadata={"key": "val"})
        assert o.metadata["key"] == "val"


class TestHypothesis:
    def test_create_hypothesis_defaults(self):
        h = Hypothesis(id="H1", description="Test")
        assert h.id == "H1"
        assert h.description == "Test"
        assert h.likelihood_score == 0.0
        assert h.coherence_score == 0.0
        assert h.simplicity_score == 0.0
        assert h.predictive_score == 0.0
        assert h.overall_score == 0.0
        assert h.evidence == []
        assert h.assumptions == []
        assert h.explains == []

    def test_hypothesis_to_dict(self):
        h = Hypothesis(id="H1", description="Test", likelihood_score=0.8)
        d = h.to_dict()
        assert d["id"] == "H1"
        assert d["likelihood_score"] == 0.8
        assert "explains" in d

    def test_hypothesis_rounding(self):
        h = Hypothesis(id="H1", description="Test", overall_score=0.12345678)
        d = h.to_dict()
        assert d["overall_score"] == 0.1235


class TestAbductionResult:
    def test_create_result(self):
        o = Observation(description="obs")
        r = AbductionResult(request_id="abc", observations=[o], hypotheses=[])
        assert r.request_id == "abc"
        assert r.best_explanation is None
        assert r.explanation == ""

    def test_result_to_dict(self):
        o = Observation(description="obs")
        h = Hypothesis(id="H1", description="Best", overall_score=0.9)
        r = AbductionResult(
            request_id="abc",
            observations=[o],
            hypotheses=[h],
            best_explanation=h,
            explanation="Found",
        )
        d = r.to_dict()
        assert d["request_id"] == "abc"
        assert d["best_explanation"] is not None
        assert d["observations"][0]["description"] == "obs"


class TestIbeScore:
    def test_score_basic(self):
        h = Hypothesis(id="H1", description="sky is blue due to scattering")
        obs = [Observation("The sky is blue")]
        score = ibe_score(h, obs)
        assert 0.0 < score <= 1.0

    def test_score_empty_observations(self):
        h = Hypothesis(id="H1", description="test")
        score = ibe_score(h, [])
        # When no observations, likelihood=0, score depends on simplicity + predictive
        assert 0.0 <= score < 1.0

    def test_score_with_assumptions(self):
        h = Hypothesis(
            id="H1",
            description="simple explanation",
            assumptions=["A1", "A2"],
        )
        obs = [Observation("Something happens")]
        score = ibe_score(h, obs)
        assert 0.0 < score <= 1.0

    def test_score_contradictory_assumptions(self):
        h = Hypothesis(
            id="H1",
            description="test",
            assumptions=["Gravity is present", "Gravity is not present"],
        )
        obs = [Observation("Objects fall")]
        score = ibe_score(h, obs)
        # Coherence should be reduced due to contradiction
        assert score < 1.0

    def test_score_predictive_power(self):
        h = Hypothesis(id="H1", description="volcanic ash scattering particles")
        obs = [Observation("The sky is red")]
        score = ibe_score(h, obs)
        assert score > 0.0

    def test_score_all_weights_zero(self):
        h = Hypothesis(id="H1", description="test")
        obs = [Observation("obs")]
        score = ibe_score(h, obs, 0, 0, 0, 0)
        assert score == 0.0

    def test_score_likelihood_full_match(self):
        h = Hypothesis(id="H1", description="the sky is blue")
        obs = [Observation("the sky is blue")]
        score = ibe_score(h, obs, likelihood_weight=1.0, coherence_weight=0, simplicity_weight=0, predictive_weight=0)
        assert score > 0.5

    def test_score_likelihood_no_match(self):
        h = Hypothesis(id="H1", description="completely unrelated")
        obs = [Observation("the sky is blue")]
        score = ibe_score(h, obs, likelihood_weight=1.0, coherence_weight=0, simplicity_weight=0, predictive_weight=0)
        assert score == 0.0


class TestRetroduction:
    def test_generate_physics(self):
        obs = [Observation("Mercury perihelion precesses")]
        hyps = retroduction(obs, domain="physics", max_hypotheses=3)
        assert len(hyps) == 3
        assert all(isinstance(h, Hypothesis) for h in hyps)
        assert all("Mercury" in h.description for h in hyps)

    def test_generate_biology(self):
        obs = [Observation("Cell divides rapidly")]
        hyps = retroduction(obs, domain="biology", max_hypotheses=2)
        assert len(hyps) == 2

    def test_generate_general_fallback(self):
        obs = [Observation("Something happens")]
        hyps = retroduction(obs, domain="unknown", max_hypotheses=3)
        assert len(hyps) == 3

    def test_generate_empty_observations(self):
        hyps = retroduction([], domain="general", max_hypotheses=2)
        assert len(hyps) == 2
        assert "observed phenomena" in hyps[0].description

    def test_generate_custom_templates(self):
        obs = [Observation("X")]
        templates = ["Custom A: {}", "Custom B: {}"]
        hyps = retroduction(obs, custom_templates=templates, max_hypotheses=2)
        assert len(hyps) == 2
        assert hyps[0].description.startswith("Custom A")

    def test_generate_zero_count(self):
        hyps = retroduction([Observation("X")], max_hypotheses=0)
        assert len(hyps) == 0


class TestSelectBestExplanation:
    def test_select_best(self):
        h1 = Hypothesis(id="H1", description="Gravity bends light")
        h2 = Hypothesis(id="H2", description="Refraction in ether", assumptions=["ether exists"])
        obs = [Observation("Star shift during eclipse")]
        best = select_best_explanation([h1, h2], obs)
        assert best is not None
        assert best.overall_score >= 0.0

    def test_select_empty(self):
        best = select_best_explanation([], [Observation("obs")])
        assert best is None

    def test_select_single(self):
        h = Hypothesis(id="H1", description="test")
        obs = [Observation("obs")]
        best = select_best_explanation([h], obs)
        assert best == h
        assert best.overall_score >= 0.0


class TestRankHypotheses:
    def test_rank_multiple(self):
        h1 = Hypothesis(id="H1", description="Gravity bends light")
        h2 = Hypothesis(id="H2", description="Refraction in ether", assumptions=["ether"])
        obs = [Observation("Star shift during eclipse")]
        ranked = rank_hypotheses([h1, h2], obs)
        assert len(ranked) == 2
        assert ranked[0][1] >= ranked[1][1]
        assert abs(sum(p for _, p in ranked) - 1.0) < 1e-6

    def test_rank_empty(self):
        assert rank_hypotheses([], [Observation("obs")]) == []

    def test_rank_single(self):
        h = Hypothesis(id="H1", description="test")
        ranked = rank_hypotheses([h], [Observation("obs")])
        assert len(ranked) == 1
        assert ranked[0][1] == 1.0

    def test_rank_equal_scores(self):
        h1 = Hypothesis(id="H1", description="a")
        h2 = Hypothesis(id="H2", description="b")
        obs = [Observation("x")]
        ranked = rank_hypotheses([h1, h2], obs)
        assert len(ranked) == 2
        assert ranked[0][1] == ranked[1][1]


class TestAbductionEngine:
    def test_create_engine(self):
        e = AbductionEngine()
        assert e.likelihood_weight == 0.40
        assert e.coherence_weight == 0.25
        assert e.simplicity_weight == 0.20
        assert e.predictive_weight == 0.15

    def test_create_engine_custom_weights(self):
        e = AbductionEngine(
            likelihood_weight=0.5,
            coherence_weight=0.3,
            simplicity_weight=0.1,
            predictive_weight=0.1,
        )
        assert e.likelihood_weight == 0.5

    def test_infer_to_best_explanation(self):
        e = AbductionEngine()
        obs = [Observation("Unexpected cognitive load spike")]
        result = e.infer_to_best_explanation(obs, domain="cognitive", max_hypotheses=3)
        assert isinstance(result, AbductionResult)
        assert len(result.hypotheses) == 3
        assert result.best_explanation is not None
        assert result.explanation != ""

    def test_infer_best_explanation_sorted(self):
        e = AbductionEngine()
        obs = [Observation("Systematic pattern emerges from random data")]
        result = e.infer_to_best_explanation(obs, domain="general", max_hypotheses=5)
        scores = [h.overall_score for h in result.hypotheses]
        # Best explanation should have highest score; all scores computed
        assert result.best_explanation is not None
        assert result.best_explanation.overall_score == max(scores)

    def test_infer_custom_templates(self):
        e = AbductionEngine()
        obs = [Observation("X")]
        templates = ["Custom mechanism: {}"]
        result = e.infer_to_best_explanation(
            obs, custom_templates=templates, max_hypotheses=1
        )
        assert len(result.hypotheses) == 1
        assert "Custom mechanism" in result.hypotheses[0].description

    def test_infer_empty_observations(self):
        e = AbductionEngine()
        result = e.infer_to_best_explanation([], domain="general", max_hypotheses=2)
        assert isinstance(result, AbductionResult)
        assert len(result.hypotheses) == 2

    def test_infer_result_metadata(self):
        e = AbductionEngine()
        obs = [Observation("Test")]
        result = e.infer_to_best_explanation(obs, domain="physics")
        assert result.metadata["method"] == "Inference to the Best Explanation (Peirce)"
        assert result.metadata["domain"] == "physics"
        assert result.metadata["scoring_dimensions"] == 4

    def test_infer_result_to_dict(self):
        e = AbductionEngine()
        obs = [Observation("Test")]
        result = e.infer_to_best_explanation(obs, max_hypotheses=2)
        d = result.to_dict()
        assert "request_id" in d
        assert "observations" in d
        assert "hypotheses" in d
        assert "best_explanation" in d

    def test_infer_probability_in_metadata(self):
        e = AbductionEngine()
        obs = [Observation("Test")]
        result = e.infer_to_best_explanation(obs, max_hypotheses=3)
        for h in result.hypotheses:
            assert "ibe_probability" in h.metadata
            assert 0.0 <= h.metadata["ibe_probability"] <= 1.0


class TestDomainTemplates:
    def test_all_domains_present(self):
        from src.discovery.abduction import DOMAIN_TEMPLATES

        assert "physics" in DOMAIN_TEMPLATES
        assert "biology" in DOMAIN_TEMPLATES
        assert "chemistry" in DOMAIN_TEMPLATES
        assert "cognitive" in DOMAIN_TEMPLATES
        assert "general" in DOMAIN_TEMPLATES

    def test_each_domain_has_templates(self):
        from src.discovery.abduction import DOMAIN_TEMPLATES

        for domain, templates in DOMAIN_TEMPLATES.items():
            assert len(templates) >= 3, f"Domain {domain} has too few templates"
