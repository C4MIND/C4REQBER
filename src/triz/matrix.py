"""TRIZ 39×39 Contradiction Matrix — Query API Layer.

Imports raw data from matrix_core.py.
Provides query functions: get_recommended_principles, get_all_matrix_cells, count_cells.
"""
from __future__ import annotations

from src.triz.matrix_core import MATRIX, PARAMETERS, get_parameter_id, get_parameter_name


def get_recommended_principles(improving: int, worsening: int) -> list[int]:
    """
    Get recommended principles for a contradiction.

    Args:
        improving: ID of the parameter to improve (1-39)
        worsening: ID of the parameter that worsens (1-39)

    Returns:
        List of principle numbers (1-40)
    """
    if improving == worsening:
        return []

    row = MATRIX.get(improving, {})
    return row.get(worsening, [])


def get_all_matrix_cells() -> list[tuple[int, int, list[int]]]:
    """Return all populated matrix cells as (improving, worsening, principles) tuples."""
    cells = []
    for improving, row in MATRIX.items():
        for worsening, principles in row.items():
            cells.append((improving, worsening, principles))
    return cells


def count_cells() -> int:
    """Count total number of populated matrix cells."""
    return sum(len(row) for row in MATRIX.values())
