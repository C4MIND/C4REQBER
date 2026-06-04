"""
TRIZ Matrix Resolver - Contradiction resolution and principles lookup.
"""


from .matrix_core import MATRIX


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
