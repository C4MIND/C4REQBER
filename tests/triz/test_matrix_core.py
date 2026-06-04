"""Tests for src/triz/matrix_core.py"""
import pytest

from src.triz.matrix_core import MATRIX, PARAMETERS, get_parameter_id, get_parameter_name


class TestParameters:
    def test_parameter_count(self):
        assert len(PARAMETERS) == 39

    def test_parameter_ids_are_sequential(self):
        assert set(PARAMETERS.keys()) == set(range(1, 40))

    def test_parameter_names_are_strings(self):
        for name in PARAMETERS.values():
            assert isinstance(name, str)
            assert len(name) > 0


class TestGetParameterName:
    def test_known_parameters(self):
        assert get_parameter_name(1) == "Weight of moving object"
        assert get_parameter_name(9) == "Speed"
        assert get_parameter_name(39) == "Productivity"

    def test_unknown_parameter(self):
        assert get_parameter_name(0) == "Unknown parameter 0"
        assert get_parameter_name(40) == "Unknown parameter 40"
        assert get_parameter_name(999) == "Unknown parameter 999"


class TestGetParameterId:
    def test_exact_match(self):
        assert get_parameter_id("Speed") == 9
        assert get_parameter_id("speed") == 9

    def test_partial_match(self):
        assert get_parameter_id("weight") == 1  # "Weight of moving object"
        assert get_parameter_id("moving") == 1

    def test_no_match(self):
        assert get_parameter_id("nonexistent") is None


class TestMatrixStructure:
    def test_matrix_is_dict(self):
        assert isinstance(MATRIX, dict)

    def test_matrix_has_rows(self):
        assert len(MATRIX) > 0

    def test_all_row_keys_are_integers(self):
        for key in MATRIX:
            assert isinstance(key, int)
            assert 1 <= key <= 39

    def test_rows_are_dicts(self):
        for row in MATRIX.values():
            assert isinstance(row, dict)

    def test_cell_values_are_lists_of_integers(self):
        for improving, row in MATRIX.items():
            for worsening, principles in row.items():
                assert isinstance(improving, int)
                assert isinstance(worsening, int)
                assert isinstance(principles, list)
                for p in principles:
                    assert isinstance(p, int)
                    assert 1 <= p <= 40

    def test_no_diagonal_entries(self):
        """A parameter cannot contradict itself."""
        for improving, row in MATRIX.items():
            assert improving not in row

    def test_matrix_cells_have_principles(self):
        """Every cell should recommend at least one principle."""
        for row in MATRIX.values():
            for principles in row.values():
                assert len(principles) > 0

    def test_sample_cells(self):
        """Verify a few known cells from the classical matrix."""
        assert 35 in MATRIX[1][2]  # Weight moving vs stationary
        assert 29 in MATRIX[1][3]  # Weight moving vs length moving
        assert 10 in MATRIX[9][10]  # Speed vs Force
