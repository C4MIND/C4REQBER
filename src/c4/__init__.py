"""C4 Engine — thin package init."""
from .engine import C4Space
from .state import C4State, all_27_states, hamming_distance, verify_theorem_11


__all__ = ["C4State", "C4Space", "all_27_states", "hamming_distance", "verify_theorem_11"]
