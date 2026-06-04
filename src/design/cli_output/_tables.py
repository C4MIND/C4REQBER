"""
C4REQBER Design System - CLI table components.
"""
from __future__ import annotations

from typing import Any

from rich.box import ROUNDED, Box
from rich.table import Table

from ..tokens import DesignTokens


class StyledTable:
    """Factory for consistently styled tables."""

    COLUMN_STYLES = {
        "id": DesignTokens.INFO.hex,
        "name": DesignTokens.PRIMARY.hex,
        "value": DesignTokens.SUCCESS.hex,
        "status_success": DesignTokens.SUCCESS.hex,
        "status_pending": DesignTokens.WARNING.hex,
        "status_error": DesignTokens.ERROR.hex,
        "metric": f"bold {DesignTokens.PRIMARY.hex}",
        "date": "dim",
        "description": "white",
        "identifier": DesignTokens.INFO.hex,
        "confidence": DesignTokens.ACCENT.hex,
        "method": DesignTokens.PRIMARY.hex,
    }

    @staticmethod
    def create(
        title: str,
        columns: list[dict[str, Any]],
        show_header: bool = True,
        box_style: Box = ROUNDED,
        expand: bool = True,
    ) -> Table:
        """Create a standardized table."""
        table = Table(
            title=f"[bold]{title}[/bold]",
            show_header=show_header,
            header_style="bold white",
            box=box_style,
            expand=expand,
        )
        for col in columns:
            style = StyledTable.COLUMN_STYLES.get(col.get("type") or "", "white")
            table.add_column(
                col["name"],
                style=style,
                width=col.get("width"),
                max_width=col.get("max_width"),
                justify=col.get("justify", "left"),
                no_wrap=col.get("no_wrap", False),
            )
        return table

    @staticmethod
    def hypothesis_table() -> Table:
        """Create a standard hypotheses table."""
        return StyledTable.create(
            "Generated Hypotheses",
            [
                {"name": "ID", "type": "id", "width": 8},
                {"name": "Hypothesis", "type": "name"},
                {"name": "Confidence", "type": "confidence", "width": 12, "justify": "center"},
                {"name": "Method", "type": "method", "width": 15},
                {"name": "Status", "type": "status_success", "width": 12, "justify": "center"},
            ],
        )

    @staticmethod
    def discovery_table() -> Table:
        """Create a standard discoveries table."""
        return StyledTable.create(
            "Discovery History",
            [
                {"name": "ID", "type": "id", "width": 8},
                {"name": "Problem", "type": "name", "max_width": 40},
                {"name": "Hypotheses", "type": "metric", "width": 10, "justify": "center"},
                {"name": "Confidence", "type": "confidence", "width": 12, "justify": "center"},
                {"name": "Date", "type": "date", "width": 12},
                {"name": "Status", "type": "status_success", "width": 10, "justify": "center"},
            ],
        )

    @staticmethod
    def search_results_table() -> Table:
        """Create a standard search results table."""
        return StyledTable.create(
            "Search Results",
            [
                {"name": "ID", "type": "id", "width": 8},
                {"name": "Title", "type": "name", "max_width": 50},
                {"name": "Year", "type": "date", "width": 6, "justify": "center"},
                {"name": "Citations", "type": "metric", "width": 10, "justify": "center"},
                {"name": "Relevance", "type": "confidence", "width": 12, "justify": "center"},
            ],
        )
