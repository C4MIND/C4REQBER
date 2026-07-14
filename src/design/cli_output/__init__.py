"""
c4-cdi-turbo Design System - CLI output subpackage.
Re-exports all CLI output components.
"""
from ._displays import ErrorDisplay, ProgressIndicator, ResultDisplay
from ._panels import PanelType, StyledPanel
from ._tables import StyledTable
from ._widgets import (
    ConfirmationPrompt,
    StatusIndicator,
    TreeDisplay,
    print_divider,
    print_empty_line,
    print_section_header,
)


__all__ = [
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
