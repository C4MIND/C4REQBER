"""
Tests for TURBO-CDI core functionality
"""

import pytest
import sys

sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")

from core.c4_state import C4State, C4Space
from core.operators import Operators
from core.cdi_engine import CDIEngine, PhysicalContradiction, ContradictionType
from extractors.contradiction import ContradictionExtractor


class TestC4State:
    """Test C4 state space."""

    def test_state_creation(self):
        state = C4State(T=1, S=2, A=0)
        assert state.T == 1
        assert state.S == 2
        assert state.A == 0

    def test_all_states(self):
        states = C4State.all_states()
        assert len(states) == 27  # Z₃³ = 27

    def test_state_string(self):
        state = C4State(T=1, S=1, A=1)
        assert "Present" in str(state)
        assert "Abstract" in str(state)
        assert "Other" in str(state)


class TestC4Space:
    """Test C4 space operations."""

    def setup_method(self):
        self.space = C4Space()

    def test_hamming_distance(self):
        s1 = C4State(T=0, S=0, A=0)
        s2 = C4State(T=2, S=2, A=2)

        # All 3 axes differ
        assert self.space.hamming_distance(s1, s2) == 3

    def test_same_state_zero_distance(self):
        s = C4State(T=1, S=1, A=1)
        assert self.space.hamming_distance(s, s) == 0

    def test_theorem_11_bound(self):
        """Theorem 11: Any state reachable in ≤6 steps."""
        s1 = C4State(T=0, S=0, A=0)
        s2 = C4State(T=2, S=2, A=2)

        # Maximum Hamming distance = 3
        # So max steps = 3 (one per axis)
        dist = self.space.hamming_distance(s1, s2)
        assert dist <= 3


class TestOperators:
    """Test 27 C4 operators."""

    def setup_method(self):
        self.ops = Operators()

    def test_base_operators_count(self):
        assert len(self.ops.base) == 10  # 9 + variations

    def test_composed_operators_count(self):
        assert len(self.ops.composed) >= 15  # 18 total

    def test_tau_plus_cycles(self):
        """τ³ = identity (period-3)."""
        state = C4State(T=0, S=1, A=2)

        # Apply tau+ 3 times
        s1 = self.ops.get("tau+")(state)
        s2 = self.ops.get("tau+")(s1)
        s3 = self.ops.get("tau+")(s2)

        assert s3.T == state.T  # Back to original

    def test_iota_inversion(self):
        """ι: invert all axes."""
        state = C4State(T=0, S=0, A=0)
        inverted = self.ops.get("iota")(state)

        assert inverted.T == 2  # 0 → 2
        assert inverted.S == 2
        assert inverted.A == 2

    def test_lambda_plus_abstract(self):
        """λ+: Concrete→Abstract→Meta."""
        concrete = C4State(T=1, S=0, A=1)  # S=0 (Concrete)
        abstract = self.ops.get("lambda+")(concrete)

        assert abstract.S == 1  # Now Abstract


class TestCDIEngine:
    """Test CDI algorithm."""

    def setup_method(self):
        self.engine = CDIEngine()

    def test_solve_returns_solution(self):
        contradiction = PhysicalContradiction(
            parameter="Test",
            value_a="A",
            value_not_a="not-A",
            requirement_y="Y",
            requirement_z="Z",
            contradiction_type=ContradictionType.TRADE_OFF,
        )

        solution = self.engine.solve(contradiction)

        assert solution is not None
        assert solution.steps_taken <= 6  # Theorem 11
        assert solution.hypothesis is not None

    def test_einstein_str_validation(self):
        """STR should complete in ≤4 steps."""
        from core.cdi_engine import EinsteinValidator

        validator = EinsteinValidator(self.engine)
        solution = validator.validate_str()

        assert solution.steps_taken <= 4

    def test_einstein_gtr_validation(self):
        """GTR should complete in ≤6 steps."""
        from core.cdi_engine import EinsteinValidator

        validator = EinsteinValidator(self.engine)
        solution = validator.validate_gtr()

        assert solution.steps_taken <= 6


class TestContradictionExtractor:
    """Test contradiction extraction."""

    def setup_method(self):
        self.extractor = ContradictionExtractor()

    def test_extract_trade_off(self):
        problem = "The battery must be high capacity but also very lightweight"
        contradiction = self.extractor.extract(problem)

        assert contradiction is not None
        assert contradiction.contradiction_type == ContradictionType.TRADE_OFF

    def test_extract_battery_contradiction(self):
        problem = "How to achieve fast charging and long battery life?"
        contradiction = self.extractor.extract(problem)

        assert contradiction is not None
        assert (
            "charging" in contradiction.parameter.lower()
            or "battery" in contradiction.parameter.lower()
        )

    def test_extract_software_contradiction(self):
        problem = "Create software that is both secure and easy to use"
        contradiction = self.extractor.extract(problem)

        assert contradiction is not None


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_battery_problem(self):
        """Full pipeline: Battery problem → Contradiction → CDI solution."""
        problem = "How to achieve both high energy density and fast charging?"

        # Extract
        extractor = ContradictionExtractor()
        contradiction = extractor.extract(problem)

        assert contradiction is not None

        # Solve
        engine = CDIEngine()
        solution = engine.solve(contradiction)

        assert solution is not None
        assert solution.steps_taken <= 6
        assert solution.confidence_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
