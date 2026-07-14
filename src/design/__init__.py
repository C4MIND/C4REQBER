"""
c4-cdi-turbo Design System v1.0.0

Centralized design tokens and UI components for consistent
visual presentation across CLI and Web interfaces.

Usage:
    from src.design import DesignTokens, StyledPanel, PanelType
    from src.design import SPACING, TYPOGRAPHY, ICONS
"""
from __future__ import annotations

from .cli_output import (
    ConfirmationPrompt,
    ErrorDisplay,
    PanelType,
    ProgressIndicator,
    ResultDisplay,
    StatusIndicator,
    StyledPanel,
    StyledTable,
    TreeDisplay,
    print_divider,
    print_empty_line,
    print_section_header,
)
from .tokens import (
    ANIMATION,
    BREAKPOINTS,
    GRID,
    ICONS,
    RADIUS,
    SHADOWS,
    SPACING,
    TYPOGRAPHY,
    Z_INDEX,
    ColorToken,
    DesignTokens,
    get_color_by_status,
    get_icon_by_category,
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
