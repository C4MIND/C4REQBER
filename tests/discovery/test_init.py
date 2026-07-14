"""Tests for discovery module __init__ exports."""
from __future__ import annotations


class TestDiscoveryImports:
    def test_abduction_exports(self):
        from src.discovery import (
            AbductionEngine,
            AbductionHypothesis,
            AbductionResult,
            Observation,
            ibe_score,
            rank_hypotheses,
            retroduction,
            select_best_explanation,
        )

        assert AbductionEngine is not None
        assert AbductionResult is not None
        assert Observation is not None

    def test_strong_inference_exports(self):
        from src.discovery import (
            Experiment,
            InferenceResult,
            StrongInferenceEngine,
            StrongInferenceHypothesis,
            bayesian_update,
            design_crucial_experiment,
            eliminate_falsified,
            generate_competing_hypotheses,
            recycle_hypotheses,
        )

        assert StrongInferenceEngine is not None
        assert InferenceResult is not None
        assert Experiment is not None

    def test_falsification_exports(self):
        from src.discovery import (
            FalsificationEngine,
            FalsificationHypothesis,
            FalsificationReport,
            TestResult,
            demarcation,
            evaluate_hypothesis,
            is_falsifiable,
            modus_tollens,
            severity_score,
        )

        assert FalsificationEngine is not None
        assert FalsificationReport is not None
        assert TestResult is not None

    def test_all_list_complete(self):
        from src.discovery import __all__

        assert len(__all__) >= 20
        assert "AbductionEngine" in __all__
        assert "StrongInferenceEngine" in __all__
        assert "FalsificationEngine" in __all__
