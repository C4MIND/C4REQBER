"""
TRIZ Matrix Utilities - Helpers and query functions for the contradiction matrix.
"""


from .matrix_core import MATRIX


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
