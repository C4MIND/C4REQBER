"""Tests for src/triz/matrix_resolver.py"""
import pytest

from src.triz.matrix_resolver import get_recommended_principles


class TestGetRecommendedPrinciples:
    def test_same_parameter_returns_empty(self):
        """Improving and worsening the same parameter is not a contradiction."""
        assert get_recommended_principles(1, 1) == []
        assert get_recommended_principles(39, 39) == []

    def test_known_contradiction(self):
        """Weight of moving object (1) vs Speed (9) should recommend principles."""
        result = get_recommended_principles(1, 9)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(p, int) and 1 <= p <= 40 for p in result)

    def test_reverse_direction(self):
        """Matrix is asymmetric; reversing should give different principles."""
        forward = get_recommended_principles(1, 9)
        reverse = get_recommended_principles(9, 1)
        assert forward != reverse

    def test_all_valid_parameters(self):
        """Every valid pair (i, j) where i != j should return a list."""
        for i in range(1, 40):
            for j in range(1, 40):
                if i != j:
                    result = get_recommended_principles(i, j)
                    assert isinstance(result, list)
