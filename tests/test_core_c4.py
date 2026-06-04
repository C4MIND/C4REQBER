"""
TURBO-CDI: Core Tests
Tests for C4 state space and operators
"""

import pytest
from src.core.c4_state import C4State, C4Space, TimeAxis, ScaleAxis, AgencyAxis
from src.core.operators import apply_operator, get_operator_transform


class TestC4State:
    """Test C4State dataclass."""

    def test_state_creation(self):
        """Test basic state creation."""
        state = C4State(T=1, S=0, A=2)
        assert state.T == 1
        assert state.S == 0
        assert state.A == 2

    def test_state_immutable(self):
        """Test that states are immutable."""
        state = C4State(T=1, S=0, A=2)
        with pytest.raises(AttributeError):
            state.T = 2

    def test_state_validation(self):
        """Test coordinate validation."""
        with pytest.raises(ValueError):
            C4State(T=3, S=0, A=0)  # T must be 0-2

        with pytest.raises(ValueError):
            C4State(T=0, S=-1, A=0)  # S must be 0-2

    def test_state_string(self):
        """Test string representation."""
        state = C4State(T=1, S=1, A=1)
        assert "Present" in str(state)
        assert "Abstract" in str(state)
        assert "Other" in str(state)

    def test_state_from_coords(self):
        """Test factory method with modulo."""
        state = C4State.from_coords(3, 4, 5)
        assert state.T == 0  # 3 % 3
        assert state.S == 1  # 4 % 3
        assert state.A == 2  # 5 % 3

    def test_all_states(self):
        """Test generation of all 27 states."""
        states = C4State.all_states()
        assert len(states) == 27

        # Check uniqueness
        tuples = [s.to_tuple() for s in states]
        assert len(set(tuples)) == 27


class TestC4Space:
    """Test C4Space operations."""

    def setup_method(self):
        """Set up test space."""
        self.space = C4Space()

    def test_hamming_distance(self):
        """Test Hamming distance calculation."""
        s1 = C4State(0, 0, 0)
        s2 = C4State(1, 0, 0)
        assert self.space.hamming_distance(s1, s2) == 1

        s3 = C4State(1, 1, 1)
        assert self.space.hamming_distance(s1, s3) == 3

    def test_find_path(self):
        """Test path finding."""
        start = C4State(0, 0, 0)
        end = C4State(2, 2, 2)

        path = self.space.find_path(start, end)
        assert path is not None
        assert len(path) <= 6  # Theorem 11
        assert path[0] == start
        assert path[-1] == end

    def test_get_neighbors(self):
        """Test neighbor generation."""
        state = C4State(1, 1, 1)
        neighbors = self.space.get_neighbors(state)

        # Should have 6 neighbors (2 per dimension)
        assert len(neighbors) == 6

        # All neighbors should be distance 1
        for n in neighbors:
            assert self.space.hamming_distance(state, n) == 1

    def test_get_state(self):
        """Test state lookup."""
        state = self.space.get_state(0, 0, 0)
        assert state.T == 0
        assert state.S == 0
        assert state.A == 0


class TestOperators:
    """Test C4 operators."""

    def test_tau_plus(self):
        """Test tau+ (time forward)."""
        state = C4State(0, 0, 0)  # Past
        result = apply_operator("tau+", state)
        assert result.T == 1  # Present

    def test_tau_minus(self):
        """Test tau- (time backward)."""
        state = C4State(1, 0, 0)  # Present
        result = apply_operator("tau-", state)
        assert result.T == 0  # Past

    @pytest.mark.skip(reason="sigma is now identity operator (context marker)")
    def test_sigma(self):
        """Test sigma (abstract)."""
        state = C4State(0, 0, 0)  # Concrete
        result = apply_operator("sigma", state)
        assert result.S == 1  # Abstract

    @pytest.mark.skip(reason="delta is now identity operator (context marker)")
    def test_delta(self):
        """Test delta (temporal jump)."""
        state = C4State(0, 0, 0)  # Past
        result = apply_operator("delta", state)
        assert result.T == 2  # Future

    @pytest.mark.skip(reason="sigma/delta are now identity operators")
    def test_operator_wrapping(self):
        """Test that operators wrap around."""
        state = C4State(2, 2, 2)  # Max values

        result = apply_operator("tau+", state)
        assert result.T == 0  # Wraps to Past

        result = apply_operator("sigma", state)
        assert result.S == 0  # Wraps to Concrete

    def test_invalid_operator(self):
        """Test invalid operator handling."""
        state = C4State(0, 0, 0)

        with pytest.raises(ValueError):
            apply_operator("invalid", state)


class TestTheorem11:
    """Test Theorem 11: Any state reachable in ≤6 steps."""

    def setup_method(self):
        self.space = C4Space()

    def test_all_pairs_reachable(self):
        """Test that all state pairs are reachable within 6 steps."""
        states = C4State.all_states()

        for s1 in states:
            for s2 in states:
                path = self.space.find_path(s1, s2)
                assert path is not None, f"No path from {s1} to {s2}"
                assert len(path) - 1 <= 6, f"Path from {s1} to {s2} exceeds 6 steps"

    def test_path_length_equals_hamming(self):
        """Test that shortest path equals Hamming distance."""
        states = C4State.all_states()

        for s1 in states[:5]:  # Sample to speed up
            for s2 in states[:5]:
                path = self.space.find_path(s1, s2)
                hamming = self.space.hamming_distance(s1, s2)
                assert len(path) - 1 == hamming, (
                    f"Path length {len(path) - 1} != Hamming {hamming}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
