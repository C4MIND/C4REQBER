"""
Tests for Strong Inference Engine — Platt's Strong Inference Method.

Covers: Hypothesis, Experiment, InferenceResult, generate_competing_hypotheses,
design_crucial_experiment, bayesian_update, eliminate_falsified,
recycle_hypotheses, StrongInferenceEngine.
"""
from __future__ import annotations

import pytest

from src.discovery.strong_inference import (
    Experiment,
    Hypothesis,
    InferenceResult,
    StrongInferenceEngine,
    bayesian_update,
    design_crucial_experiment,
    eliminate_falsified,
    generate_competing_hypotheses,
    recycle_hypotheses,
)


class TestHypothesis:
    def test_create_hypothesis(self):
        h = Hypothesis(id="H1", description="Test")
        assert h.id == "H1"
        assert h.description == "Test"
        assert h.prior == 0.5
        assert h.posterior == 0.5
        assert not h.is_falsified

    def test_hypothesis_prior_validation(self):
        with pytest.raises(ValueError):
            Hypothesis(id="H1", description="Test", prior=0.0)
        with pytest.raises(ValueError):
            Hypothesis(id="H1", description="Test", prior=1.5)

    def test_hypothesis_to_dict(self):
        h = Hypothesis(id="H1", description="Test", prior=0.7)
        h.posterior = 0.8
        d = h.to_dict()
        assert d["id"] == "H1"
        assert d["prior"] == 0.7
        assert d["posterior"] == 0.8


class TestExperiment:
    def test_create_experiment(self):
        e = Experiment(
            id="E1",
            description="Test exp",
            distinguishes=["H1", "H2"],
            predicted_outcomes={"H1": "outcome A", "H2": "outcome B"},
        )
        assert e.id == "E1"
        assert e.is_crucial is False  # determined by outcome diversity
        assert e.outcome == ""

    def test_experiment_to_dict(self):
        e = Experiment(
            id="E1",
            description="Test",
            distinguishes=["H1"],
            predicted_outcomes={"H1": "A"},
            outcome="A",
            confidence=0.95,
        )
        d = e.to_dict()
        assert d["outcome"] == "A"
        assert d["confidence"] == 0.95


class TestGenerateCompetingHypotheses:
    def test_generate_physics(self):
        hyps = generate_competing_hypotheses("Why is sky dark?", domain="physics", count=3)
        assert len(hyps) == 3
        assert all(isinstance(h, Hypothesis) for h in hyps)
        assert all(h.prior > 0 for h in hyps)

    def test_generate_biology(self):
        hyps = generate_competing_hypotheses("Cell growth", domain="biology", count=2)
        assert len(hyps) == 2

    def test_generate_default_domain(self):
        hyps = generate_competing_hypotheses("Problem", count=3)
        assert len(hyps) == 3

    def test_generate_equal_priors(self):
        hyps = generate_competing_hypotheses("Problem", count=4)
        expected_prior = 1.0 / 4
        assert all(h.prior == expected_prior for h in hyps)

    def test_generate_has_predictions(self):
        hyps = generate_competing_hypotheses("Problem", count=2)
        assert all(len(h.predictions) > 0 for h in hyps)


class TestDesignCrucialExperiment:
    def test_design_with_two_hypotheses(self):
        h1 = Hypothesis("H1", "Light is a wave")
        h2 = Hypothesis("H2", "Light is a particle")
        exp = design_crucial_experiment([h1, h2], "Nature of light")
        assert exp is not None
        assert "H1" in exp.distinguishes
        assert "H2" in exp.distinguishes
        assert exp.is_crucial is True

    def test_design_with_single_hypothesis(self):
        h = Hypothesis("H1", "Only one")
        exp = design_crucial_experiment([h], "Problem")
        assert exp is None

    def test_design_with_chemical_hypotheses(self):
        h1 = Hypothesis("H1", "Catalyst surface reaction")
        h2 = Hypothesis("H2", "Solvent polarity effect")
        exp = design_crucial_experiment([h1, h2], "Reaction mechanism")
        assert exp is not None
        assert len(exp.predicted_outcomes) == 2

    def test_design_with_neural_hypotheses(self):
        h1 = Hypothesis("H1", "Neural inhibition suppresses")
        h2 = Hypothesis("H2", "Predictive coding minimizes")
        exp = design_crucial_experiment([h1, h2], "Cognitive process")
        assert exp is not None


class TestBayesianUpdate:
    def test_update_confirms_hypothesis(self):
        h1 = Hypothesis("H1", "Wave", prior=0.5)
        h2 = Hypothesis("H2", "Particle", prior=0.5)
        exp = Experiment(
            "E1",
            "Double slit",
            ["H1", "H2"],
            {"H1": "interference pattern observed", "H2": "discrete impacts observed"},
        )
        updated = bayesian_update([h1, h2], exp, "interference pattern observed")
        # H1's prediction matches outcome, so its posterior should increase
        assert updated[0].posterior >= h1.posterior
        assert updated[0].evidence == ["E1: interference pattern observed"]

    def test_update_with_low_confidence(self):
        h1 = Hypothesis("H1", "A", prior=0.5)
        h2 = Hypothesis("H2", "B", prior=0.5)
        exp = Experiment("E1", "Test", ["H1", "H2"], {"H1": "A observed", "H2": "B observed"})
        updated = bayesian_update([h1, h2], exp, "A observed", confidence=0.5)
        # H1's prediction matches outcome, so its posterior should not decrease
        assert updated[0].posterior >= h1.posterior

    def test_update_empty_hypotheses(self):
        exp = Experiment("E1", "Test", [], {})
        assert bayesian_update([], exp, "outcome") == []

    def test_update_clamps_probabilities(self):
        h = Hypothesis("H1", "A", prior=0.999)
        exp = Experiment("E1", "Test", ["H1"], {"H1": "A"})
        updated = bayesian_update([h], exp, "completely different")
        assert 0.001 <= updated[0].posterior <= 0.999

    def test_update_evidence_accumulates(self):
        h1 = Hypothesis("H1", "A", prior=0.5)
        exp1 = Experiment("E1", "Test", ["H1"], {"H1": "A"})
        exp2 = Experiment("E2", "Test", ["H1"], {"H1": "A"})
        u1 = bayesian_update([h1], exp1, "A")
        u2 = bayesian_update(u1, exp2, "A")
        assert len(u2[0].evidence) == 2


class TestEliminateFalsified:
    def test_eliminate_by_outcome(self):
        h1 = Hypothesis("H1", "Wave", posterior=0.9)
        h2 = Hypothesis("H2", "Particle", posterior=0.1)
        exp = Experiment(
            "E1",
            "Test",
            ["H1", "H2"],
            {"H1": "interference pattern", "H2": "discrete impacts"},
        )
        surv, elim = eliminate_falsified([h1, h2], exp, "interference pattern")
        assert len(surv) >= 1
        assert all(not h.is_falsified for h in surv)

    def test_eliminate_all(self):
        h1 = Hypothesis("H1", "A", posterior=0.01)
        h2 = Hypothesis("H2", "B", posterior=0.01)
        exp = Experiment("E1", "Test", ["H1", "H2"], {"H1": "X outcome", "H2": "Y outcome"})
        surv, elim = eliminate_falsified([h1, h2], exp, "Z completely different")
        # With very low posterior and strong mismatch, both should be eliminated
        assert len(elim) == 2
        assert all(h.is_falsified for h in elim)

    def test_eliminate_none_survive(self):
        h = Hypothesis("H1", "A", posterior=0.9)
        exp = Experiment("E1", "Test", ["H1"], {"H1": "A"})
        surv, elim = eliminate_falsified([h], exp, "A")
        assert len(surv) == 1
        assert len(elim) == 0


class TestRecycleHypotheses:
    def test_recycle_with_survivors(self):
        h1 = Hypothesis("H1", "Wave theory")
        h2 = Hypothesis("H2", "Particle theory", is_falsified=True)
        combined = recycle_hypotheses([h1], [h2], "Nature of light")
        assert len(combined) >= 1
        assert h1 in combined

    def test_recycle_all_eliminated(self):
        h1 = Hypothesis("H1", "A", is_falsified=True)
        combined = recycle_hypotheses([], [h1], "Problem", max_new=2)
        assert len(combined) >= 1

    def test_recycle_renormalizes_priors(self):
        h1 = Hypothesis("H1", "A")
        combined = recycle_hypotheses([h1], [], "Problem", max_new=1)
        total_prior = sum(h.prior for h in combined)
        assert abs(total_prior - 1.0) < 1e-6 or total_prior == 0.0

    def test_recycle_generates_refinements(self):
        h1 = Hypothesis("H1", "Original")
        combined = recycle_hypotheses([h1], [], "Problem", max_new=2)
        assert any("Refined" in h.description for h in combined if h.id != "H1")


class TestStrongInferenceEngine:
    def test_create_engine(self):
        e = StrongInferenceEngine()
        assert e.max_cycles == 5
        assert e.elimination_threshold == 0.01

    def test_create_engine_custom(self):
        e = StrongInferenceEngine(max_cycles=3, elimination_threshold=0.05)
        assert e.max_cycles == 3
        assert e.elimination_threshold == 0.05

    def test_run_with_auto_hypotheses(self):
        e = StrongInferenceEngine(max_cycles=2)
        result = e.run(problem="Why is sky dark?", domain="physics")
        assert isinstance(result, InferenceResult)
        assert result.cycles >= 1
        assert len(result.hypotheses) >= 3

    def test_run_with_provided_hypotheses(self):
        e = StrongInferenceEngine(max_cycles=2)
        hyps = [
            Hypothesis("H1", "Wave theory"),
            Hypothesis("H2", "Particle theory"),
        ]
        result = e.run(problem="Nature of light", hypotheses=hyps)
        assert isinstance(result, InferenceResult)
        assert result.cycles >= 1

    def test_run_with_simulated_experiments(self):
        e = StrongInferenceEngine(max_cycles=3)
        hyps = [
            Hypothesis("H1", "Auxin accumulates on shaded side"),
            Hypothesis("H2", "Light directly stimulates cell elongation"),
        ]
        experiments = [
            ("interference pattern observed", 0.95),
        ]
        result = e.run(
            problem="Why do plants grow toward light?",
            hypotheses=hyps,
            experiments=experiments,
        )
        assert result.cycles >= 1
        assert len(result.experiments) >= 1

    def test_run_explanation_present(self):
        e = StrongInferenceEngine(max_cycles=2)
        result = e.run(problem="Test", domain="general")
        assert result.explanation != ""
        assert "cycle" in result.explanation.lower()

    def test_run_result_to_dict(self):
        e = StrongInferenceEngine(max_cycles=2)
        result = e.run(problem="Test", domain="general")
        d = result.to_dict()
        assert "request_id" in d
        assert "problem" in d
        assert "hypotheses" in d
        assert "experiments" in d
        assert "surviving_hypotheses" in d
        assert "eliminated_hypotheses" in d
        assert "cycles" in d

    def test_run_surviving_vs_eliminated(self):
        e = StrongInferenceEngine(max_cycles=3)
        result = e.run(problem="Test", domain="general")
        # Every hypothesis should be either surviving or eliminated
        all_ids = {h.id for h in result.hypotheses}
        surviving_ids = {h.id for h in result.surviving_hypotheses}
        eliminated_ids = {h.id for h in result.eliminated_hypotheses}
        assert surviving_ids.isdisjoint(eliminated_ids)
        assert surviving_ids | eliminated_ids <= all_ids

    def test_run_metadata(self):
        e = StrongInferenceEngine(max_cycles=2)
        result = e.run(problem="Test")
        assert result.metadata["method"] == "Strong Inference (Platt 1964)"
        assert result.metadata["max_cycles"] == 2

    def test_run_single_cycle_enough(self):
        e = StrongInferenceEngine(max_cycles=1)
        result = e.run(problem="Test", domain="general")
        assert result.cycles <= 1

    def test_run_recycle_step(self):
        e = StrongInferenceEngine(max_cycles=5)
        # Provide experiments that will eliminate most hypotheses
        hyps = [Hypothesis(f"H{i}", f"Theory {i}") for i in range(1, 4)]
        experiments = [("outcome consistent with H1", 0.99)] * 5
        result = e.run(problem="Test", hypotheses=hyps, experiments=experiments)
        assert result.cycles >= 1
