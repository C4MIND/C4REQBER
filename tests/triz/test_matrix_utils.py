"""Tests for src/triz/matrix_utils.py"""
import pytest

from src.triz.matrix_utils import count_cells, get_all_matrix_cells


class TestGetAllMatrixCells:
    def test_returns_list(self):
        cells = get_all_matrix_cells()
        assert isinstance(cells, list)

    def test_cells_are_tuples(self):
        cells = get_all_matrix_cells()
        for cell in cells:
            assert isinstance(cell, tuple)
            assert len(cell) == 3
            improving, worsening, principles = cell
            assert isinstance(improving, int)
            assert isinstance(worsening, int)
            assert isinstance(principles, list)
            assert improving != worsening

    def test_no_duplicates(self):
        cells = get_all_matrix_cells()
        pairs = [(c[0], c[1]) for c in cells]
        assert len(pairs) == len(set(pairs))


class TestCountCells:
    def test_count_matches_cells(self):
        cells = get_all_matrix_cells()
        count = count_cells()
        assert count == len(cells)

    def test_count_is_positive(self):
        assert count_cells() > 0

    def test_count_is_consistent(self):
        assert count_cells() == count_cells()
