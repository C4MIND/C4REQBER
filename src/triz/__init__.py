"""TRIZ package initialization."""

import logging


_logger = logging.getLogger(__name__)

try:
    from .bridge import (
        C4TrizBridge as TRIZBridge,
    )
    from .bridge import (
        get_c4_triz_bridge_obj,
        get_c4_triz_mapping,
        map_c4_to_triz_parameters,
        recommend_for_contradiction,
    )
except ImportError as e:
    _logger.debug("bridge not available: %s", e)
    get_c4_triz_bridge_obj = None  # type: ignore
    get_c4_triz_mapping = None  # type: ignore
    map_c4_to_triz_parameters = None  # type: ignore
    recommend_for_contradiction = None  # type: ignore

try:
    from .principles import (
        PRINCIPLES,
        Principle,
        SubPrinciple,
        get_all_principles,
        get_principle,
        search_principles,
    )
except ImportError as e:
    _logger.debug("principles not available: %s", e)
    Principle = None  # type: ignore
    SubPrinciple = None  # type: ignore
    PRINCIPLES = None  # type: ignore
    get_principle = None  # type: ignore
    get_all_principles = None  # type: ignore
    search_principles = None  # type: ignore

try:
    from .matrix import (
        MATRIX,
        PARAMETERS,
        count_cells,
        get_all_matrix_cells,
        get_parameter_id,
        get_parameter_name,
        get_recommended_principles,
    )
except ImportError as e:
    _logger.debug("matrix not available: %s", e)
    PARAMETERS = None  # type: ignore
    MATRIX = None  # type: ignore
    get_parameter_name = None  # type: ignore
    get_parameter_id = None  # type: ignore
    get_recommended_principles = None  # type: ignore
    get_all_matrix_cells = None  # type: ignore
    count_cells = None  # type: ignore

try:
    from .solver import (
        SolverResult,
        SuggestedPrinciple,
        extract_parameters_from_text,
        get_matrix_stats,
        list_all_parameters,
        solve_contradiction,
        solve_from_text,
    )
except ImportError as e:
    _logger.debug("solver not available: %s", e)
    SuggestedPrinciple = None  # type: ignore
    SolverResult = None  # type: ignore
    solve_contradiction = None  # type: ignore
    solve_from_text = None  # type: ignore
    extract_parameters_from_text = None  # type: ignore
    list_all_parameters = None  # type: ignore
    get_matrix_stats = None  # type: ignore

__all__ = [
    "Principle",
    "SubPrinciple",
    "PRINCIPLES",
    "get_principle",
    "get_all_principles",
    "search_principles",
    "PARAMETERS",
    "MATRIX",
    "get_parameter_name",
    "get_parameter_id",
    "get_recommended_principles",
    "get_all_matrix_cells",
    "count_cells",
    "SuggestedPrinciple",
    "SolverResult",
    "solve_contradiction",
    "solve_from_text",
    "extract_parameters_from_text",
    "list_all_parameters",
    "get_matrix_stats",
    "get_c4_triz_bridge_obj",
    "get_c4_triz_mapping",
    "map_c4_to_triz_parameters",
    "recommend_for_contradiction",
    "TRIZBridge",
]
