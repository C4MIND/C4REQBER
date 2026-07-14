"""Tests for src/triz/solver.py"""
import pytest

from src.triz.solver import (
    SolverResult,
    SuggestedPrinciple,
    _match_parameter,
    _score_parameters_by_keywords,
    extract_parameters_from_text,
    get_matrix_stats,
    list_all_parameters,
    solve_contradiction,
    solve_from_text,
)


class TestExtractParametersFromText:
    def test_explicit_contradiction_improve_but_worsen(self):
        text = "I want to improve speed but force gets worse"
        improving, worsening = extract_parameters_from_text(text)
        assert improving is not None
        assert worsening is not None

    def test_more_less_pattern(self):
        text = "more speed but less reliability"
        improving, worsening = extract_parameters_from_text(text)
        assert improving is not None
        assert worsening is not None

    def test_increase_without_pattern(self):
        text = "increase strength without increasing weight"
        improving, worsening = extract_parameters_from_text(text)
        assert improving is not None
        assert worsening is not None

    def test_no_contradiction(self):
        text = "The weather is nice today"
        improving, worsening = extract_parameters_from_text(text)
        assert improving is None
        assert worsening is None


class TestMatchParameter:
    def test_match_speed(self):
        assert _match_parameter("speed") == 9

    def test_match_force(self):
        assert _match_parameter("force") == 10

    def test_no_match(self):
        assert _match_parameter("xyznonexistent") is None


class TestScoreParametersByKeywords:
    def test_single_keyword(self):
        improving, _worsening = _score_parameters_by_keywords("speed and force")
        assert improving is not None

    def test_empty_text(self):
        assert _score_parameters_by_keywords("") == (None, None)


class TestSolveContradiction:
    def test_valid_contradiction(self):
        result = solve_contradiction(1, 9)
        assert isinstance(result, SolverResult)
        assert result.improving_param_id == 1
        assert result.improving_param_name == "Weight of moving object"
        assert result.worsening_param_id == 9
        assert result.worsening_param_name == "Speed"
        assert isinstance(result.principles, list)
        assert len(result.principles) > 0

    def test_principles_are_suggested_principle(self):
        result = solve_contradiction(9, 1)
        for sp in result.principles:
            assert isinstance(sp, SuggestedPrinciple)
            assert 1 <= sp.number <= 40
            assert isinstance(sp.name, str)
            assert isinstance(sp.description, str)
            assert isinstance(sp.explanation, str)
            assert 0.0 <= sp.relevance_score <= 1.0
            assert isinstance(sp.examples, list)

    def test_with_context(self):
        result = solve_contradiction(1, 9, problem_context="Aircraft design")
        assert isinstance(result, SolverResult)
        assert "Aircraft design" in result.principles[0].explanation or "Weight" in result.principles[0].explanation


class TestSolveFromText:
    def test_solvable_text(self):
        text = "I need more speed but force is getting worse"
        result = solve_from_text(text)
        assert result is not None
        assert isinstance(result, SolverResult)

    def test_unsolvable_text(self):
        text = "The weather is nice today"
        result = solve_from_text(text)
        assert result is None


class TestListAllParameters:
    def test_returns_39_parameters(self):
        params = list_all_parameters()
        assert len(params) == 39

    def test_returns_tuples(self):
        params = list_all_parameters()
        for pid, name in params:
            assert isinstance(pid, int)
            assert isinstance(name, str)


class TestGetMatrixStats:
    def test_keys_present(self):
        stats = get_matrix_stats()
        assert "total_possible_cells" in stats
        assert "populated_cells" in stats
        assert "parameters" in stats
        assert "principles" in stats

    def test_values_are_integers(self):
        stats = get_matrix_stats()
        for v in stats.values():
            assert isinstance(v, int)

    def test_parameter_and_principle_counts(self):
        stats = get_matrix_stats()
        assert stats["parameters"] == 39
        assert stats["principles"] == 40

    def test_populated_cells_positive(self):
        stats = get_matrix_stats()
        assert stats["populated_cells"] > 0

    def test_populated_lte_total(self):
        stats = get_matrix_stats()
        assert stats["populated_cells"] <= stats["total_possible_cells"]
