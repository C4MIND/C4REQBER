"""
TURBO-CDI v8.0 - Test Suite
Phase 0 Foundation Tests
"""

import pytest
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis
from modules import PentadOperation, SeptetObject
from modules.grammar.engine import GrammarEngine, Transformation
from modules.navigation.engine import NavigationEngine
from modules.operators.engine import OperatorsEngine
from cognitive.outcome_tracker.core import OutcomeTracker
from cognitive.bias_detector.core import BiasDetector, UserProfile, BiasType
from scientific.falsification.engine import FalsificationEngine
from core.orchestrator import TurboCDIv8, TurboCDIv8Sync

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGrammarModule:
    """Test L5 Grammar module"""

    def test_all_transformations_created(self):
        engine = GrammarEngine()
        transformations = engine.get_all_transformations()
        assert len(transformations) == 35  # 5 ops × 7 targets

    def test_get_by_operation(self):
        engine = GrammarEngine()
        activate_ops = engine.get_by_operation(PentadOperation.ACTIVATE)
        assert len(activate_ops) == 7

    def test_get_by_target(self):
        engine = GrammarEngine()
        structure_targets = engine.get_by_target(SeptetObject.STRUCTURE)
        assert len(structure_targets) == 5

    def test_validate_composition_max_6(self):
        engine = GrammarEngine()
        # Create 7 transformations
        transforms = [engine.get_all_transformations()[0]] * 7
        assert not engine.validate_composition(transforms)


class TestNavigationModule:
    """Test L4 Navigation module"""

    def test_all_states(self):
        engine = NavigationEngine()
        states = engine.get_all_states()
        assert len(states) == 27  # 3³

    def test_navigate_same_state(self):
        engine = NavigationEngine()
        state = C4State(TimeAxis.PRESENT, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
        path = engine.navigate(state, state)
        assert len(path) == 1
        assert path[0] == state

    def test_navigate_different_states(self):
        engine = NavigationEngine()
        s1 = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        s2 = C4State(TimeAxis.FUTURE, ScaleAxis.META, AgencyAxis.SYSTEM)
        path = engine.navigate(s1, s2)
        assert len(path) > 1
        assert path[0] == s1
        assert path[-1] == s2

    def test_theorem_11(self):
        engine = NavigationEngine()
        passed, counter = engine.verify_theorem_11(n_trials=500)
        assert passed, f"Theorem 11 falsified: {counter}"


class TestOperatorsModule:
    """Test L3 Operators module"""

    def test_all_operators(self):
        engine = OperatorsEngine()
        operators = engine.get_all_operators()
        assert len(operators) == 14

    def test_get_by_phase(self):
        engine = OperatorsEngine()
        from modules.operators.engine import OperatorPhase

        alpha_ops = engine.get_by_phase(OperatorPhase.ALPHA)
        assert len(alpha_ops) == 3

    def test_resonance_calculation(self):
        engine = OperatorsEngine()
        op = engine.get_operator("op_alpha_1")
        resonance = op.calculate_resonance("physics")
        assert 0 < resonance < 1


# ═══════════════════════════════════════════════════════════════════════════════
# COGNITIVE LAYER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestOutcomeTracker:
    """Test Outcome Tracker"""

    def test_record_prediction(self):
        tracker = OutcomeTracker()
        pred_id = tracker.record_prediction(
            transformation_id="test_trans",
            domain="psychology",
            predicted_effectiveness=0.75,
            predicted_reversibility=0.60,
            context={"test": True},
        )
        assert pred_id.startswith("pred_")
        assert len(tracker.get_pending_predictions()) == 1

    def test_record_outcome(self):
        tracker = OutcomeTracker()
        pred_id = tracker.record_prediction(
            transformation_id="test_trans",
            domain="psychology",
            predicted_effectiveness=0.75,
            predicted_reversibility=0.60,
            context={},
        )
        calibration = tracker.record_outcome(
            prediction_id=pred_id, actual_effectiveness=0.80, user_satisfaction=0.9
        )
        assert calibration.brier >= 0
        assert calibration.confidence in ["low", "medium", "high", "unknown"]


class TestBiasDetector:
    """Test Bias Detector"""

    def test_detect_optimism_bias_long_chain(self):
        detector = BiasDetector()
        plan = {
            "path": [{"operation": "ACTIVATE"}] * 5,  # 5 steps
            "estimated_effectiveness": 0.9,
        }
        warnings = detector.analyze_transformation_plan(plan, {})

        optimism_warnings = [w for w in warnings if w.bias_type == BiasType.OPTIMISM_BIAS]
        assert len(optimism_warnings) > 0

    def test_nudge_generation(self):
        detector = BiasDetector()
        plan = {"path": [{"operation": "ACTIVATE"}] * 5, "estimated_effectiveness": 0.9}
        warnings = detector.analyze_transformation_plan(plan, {})
        nudge = detector.generate_nudge(warnings)

        assert len(nudge) > 0
        assert "⚠️" in nudge or "💭" in nudge


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntegration:
    """Test full v8 integration"""

    def test_orchestrator_creation(self):
        turbo = TurboCDIv8Sync()
        assert turbo._async._initialized
        assert turbo._async.grammar is not None
        assert turbo._async.navigation is not None

    def test_plan_transformation(self):
        turbo = TurboCDIv8Sync()
        turbo.set_user("test_user")

        from_state = C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF)
        to_state = C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)

        plan = turbo.plan_transformation(
            from_state=from_state,
            to_state=to_state,
            domain="psychology",
            target=SeptetObject.STATE,
        )

        assert len(plan.path) > 0
        assert plan.transformation is not None
        assert 0 <= plan.estimated_effectiveness <= 1
        assert plan.nudge is not None  # Should have bias detection

    def test_falsification_suite(self):
        turbo = TurboCDIv8Sync()
        report = turbo.run_falsification_suite(n_trials=100)

        assert report.total_hypotheses == 7
        assert report.survival_rate >= 0  # Could be 0 if all falsified
        assert 0 <= report.falsified_count <= report.total_hypotheses


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
