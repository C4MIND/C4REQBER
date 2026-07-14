"""
C4REQBER Design System - CLI output panels and table components.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from rich.box import ROUNDED, Box
from rich.panel import Panel

from ..tokens import ICONS, DesignTokens


class PanelType(Enum):
    """Semantic panel types with consistent styling."""

    INFO = {
        "border": DesignTokens.INFO.hex,
        "title_style": f"bold {DesignTokens.INFO.hex}",
        "icon": ICONS["info"],
    }
    SUCCESS = {
        "border": DesignTokens.SUCCESS.hex,
        "title_style": f"bold {DesignTokens.SUCCESS.hex}",
        "icon": ICONS["success"],
    }
    WARNING = {
        "border": DesignTokens.WARNING.hex,
        "title_style": f"bold {DesignTokens.WARNING.hex}",
        "icon": ICONS["warning"],
    }
    ERROR = {
        "border": DesignTokens.ERROR.hex,
        "title_style": f"bold {DesignTokens.ERROR.hex}",
        "icon": ICONS["error"],
    }
    RESULT = {
        "border": DesignTokens.PRIMARY.hex,
        "title_style": f"bold {DesignTokens.PRIMARY.hex}",
        "icon": ICONS["hypothesis"],
    }
    DISCOVERY = {
        "border": DesignTokens.PRIMARY.hex,
        "title_style": f"bold bright_white on {DesignTokens.PRIMARY.hex}",
        "icon": ICONS["discover"],
    }
    AGENT = {
        "border": DesignTokens.ACCENT.hex,
        "title_style": f"bold {DesignTokens.ACCENT.hex}",
        "icon": ICONS["agent"],
    }
    NEUTRAL = {
        "border": DesignTokens.GRAY_400.hex,
        "title_style": f"bold {DesignTokens.GRAY_400.hex}",
        "icon": ICONS["info"],
    }

class StyledPanel:
    """Factory for consistently styled panels."""

    @staticmethod
    def create(
        content: Any,
        title: str,
        panel_type: PanelType = PanelType.NEUTRAL,
        subtitle: str | None = None,
        padding: tuple[Any, ...] = (1, 2),
        box_style: Box = ROUNDED,
        expand: bool = True,
    ) -> Panel:
        """Create a standardized panel."""
        config = panel_type.value
        full_title = f"{config['icon']} {title.upper()}"

        return Panel(
            content,
            title=full_title,
            title_align="left",
            subtitle=subtitle,
            border_style=config["border"],
            padding=padding,
            box=box_style,
            expand=expand,
        )

    @staticmethod
    def info(content: Any, title: str = "Info", **kwargs: Any) -> Panel:
        """Create an info panel."""
        return StyledPanel.create(content, title, PanelType.INFO, **kwargs)

    @staticmethod
    def success(content: Any, title: str = "Success", **kwargs: Any) -> Panel:
        """Create a success panel."""
        return StyledPanel.create(content, title, PanelType.SUCCESS, **kwargs)

    @staticmethod
    def warning(content: Any, title: str = "Warning", **kwargs: Any) -> Panel:
        """Create a warning panel."""
        return StyledPanel.create(content, title, PanelType.WARNING, **kwargs)

    @staticmethod
    def error(content: Any, title: str = "Error", **kwargs: Any) -> Panel:
        """Create an error panel."""
        return StyledPanel.create(content, title, PanelType.ERROR, **kwargs)

    @staticmethod
    def result(content: Any, title: str = "Result", **kwargs: Any) -> Panel:
        """Create a result panel."""
        return StyledPanel.create(content, title, PanelType.RESULT, **kwargs)

    @staticmethod
    def discovery(content: Any, title: str = "Discovery", **kwargs: Any) -> Panel:
        """Create a discovery panel."""
        return StyledPanel.create(content, title, PanelType.DISCOVERY, **kwargs)
