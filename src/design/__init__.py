"""
TURBO-CDI Design System v1.0.0

Centralized design tokens and UI components for consistent
visual presentation across CLI and Web interfaces.

Usage:
    from src.design import DesignTokens, StyledPanel, PanelType
    from src.design import SPACING, TYPOGRAPHY, ICONS
"""

from .tokens import (
    DesignTokens,
    ColorToken,
    SPACING,
    TYPOGRAPHY,
    RADIUS,
    SHADOWS,
    ANIMATION,
    ICONS,
    Z_INDEX,
    BREAKPOINTS,
    GRID,
    get_color_by_status,
    get_icon_by_category,
)

from .cli_output import (
    PanelType,
    StyledPanel,
    StyledTable,
    ProgressIndicator,
    ErrorDisplay,
    ResultDisplay,
    StatusIndicator,
    TreeDisplay,
    ConfirmationPrompt,
    print_section_header,
    print_divider,
    print_empty_line,
)

__version__ = "1.0.0"
__all__ = [
    # Version
    "__version__",
    # Tokens
    "DesignTokens",
    "ColorToken",
    "SPACING",
    "TYPOGRAPHY",
    "RADIUS",
    "SHADOWS",
    "ANIMATION",
    "ICONS",
    "Z_INDEX",
    "BREAKPOINTS",
    "GRID",
    "get_color_by_status",
    "get_icon_by_category",
    # CLI Output
    "PanelType",
    "StyledPanel",
    "StyledTable",
    "ProgressIndicator",
    "ErrorDisplay",
    "ResultDisplay",
    "StatusIndicator",
    "TreeDisplay",
    "ConfirmationPrompt",
    "print_section_header",
    "print_divider",
    "print_empty_line",
]
