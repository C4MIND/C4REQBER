"""Tests for discovery module integration across all three engines."""
from __future__ import annotations

from src.discovery.abduction import AbductionEngine, Observation
from src.discovery.falsification import FalsificationEngine
from src.discovery.strong_inference import StrongInferenceEngine


class TestDiscoveryIntegration:
    def test_abduction_to_falsification_pipeline(self):
        """Generate hypotheses with abduction, then falsify the best one."""
        abduction = AbductionEngine()
        obs = [
            Observation("Mercury perihelion precesses unexpectedly"),
            Observation("Newtonian prediction is off by 43 arcsec/century"),
        ]
        abduction_result = abduction.infer_to_best_explanation(obs, domain="physics")

        assert abduction_result.best_explanation is not None

        falsification = FalsificationEngine()
        best = abduction_result.best_explanation
        report = falsification.evaluate(
            "Gravity causes anomalous precession",
            [
                ("Should observe gravitational effects", "Anomalous precession observed"),
            ],
            hypothesis_id=best.id,
        )

        assert report.is_falsifiable is True
        assert len(report.tests) == 1

    def test_strong_inference_to_falsification_pipeline(self):
        """Run strong inference, then check falsifiability of surviving hypotheses."""
        si = StrongInferenceEngine(max_cycles=2)
        result = si.run(problem="Why do objects fall?", domain="physics")

        assert result.cycles >= 1

        falsification = FalsificationEngine()
        for h in result.surviving_hypotheses:
            report = falsification.evaluate(h.description, [], hypothesis_id=h.id)
            assert report.demarcation in (
                "science", "mathematics", "insufficient_information", "non_science"
            )

    def test_full_discovery_cycle(self):
        """Complete L5 discovery cycle: abduce -> infer -> falsify."""
        # Step 1: Abduction — generate explanations
        abduction = AbductionEngine()
        obs = [Observation("Unexpected redshift in galaxy spectra")]
        abduction_result = abduction.infer_to_best_explanation(obs, domain="physics", max_hypotheses=3)

        # Step 2: Strong Inference — compare competing explanations
        si = StrongInferenceEngine(max_cycles=2)
        from src.discovery.strong_inference import Hypothesis as SIHypothesis

        si_hypotheses = [
            SIHypothesis(id=h.id, description=h.description)
            for h in abduction_result.hypotheses
        ]
        si_result = si.run(
            problem="Explain redshift anomaly",
            hypotheses=si_hypotheses,
        )

        # Step 3: Falsification — evaluate surviving hypotheses
        falsification = FalsificationEngine()
        for h in si_result.surviving_hypotheses:
            report = falsification.evaluate(
                h.description,
                [("Should show Doppler effect", "Observed redshift consistent")],
                hypothesis_id=h.id,
            )
            assert report.is_falsifiable is True

        assert abduction_result.best_explanation is not None
        assert si_result.cycles >= 1

    def test_all_engines_independent(self):
        """Each engine can operate independently."""
        abduction = AbductionEngine()
        si = StrongInferenceEngine(max_cycles=1)
        falsification = FalsificationEngine()

        r1 = abduction.infer_to_best_explanation([Observation("X")], max_hypotheses=2)
        r2 = si.run(problem="Y")
        r3 = falsification.evaluate("All Z are W", [])

        assert r1.best_explanation is not None
        assert r2.cycles >= 0
        assert r3.is_falsifiable is True

    def test_demarcation_across_domains(self):
        """Test demarcation on statements from different domains."""
        falsification = FalsificationEngine()

        statements = [
            ("All metals conduct electricity", "science"),
            ("Astrology predicts personality", "pseudoscience"),
            ("God exists", "metaphysics"),
            ("2 + 2 = 4", "mathematics"),
            ("Hi", "insufficient_information"),
        ]

        for stmt, expected in statements:
            result = falsification.classify(stmt)
            assert result == expected, f"Expected {expected} for '{stmt}', got {result}"
