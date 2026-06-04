"""
C4REQBER Design System - Status indicators, tree displays, prompts, and helpers.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from ..tokens import ICONS, DesignTokens, get_color_by_status


console = Console()

class StatusIndicator:
    """Standardized status indicators."""

    @staticmethod
    def get_status_badge(status: str) -> str:
        """Get a styled status badge."""
        status = status.lower()
        color = get_color_by_status(status).hex
        icon = ICONS.get(status, ICONS["info"])
        return f"[{color}]{icon} {status.upper()}[/{color}]"

    @staticmethod
    def get_confidence_bar(confidence: float, width: int = 20) -> str:
        """Get a visual confidence bar."""
        filled = int(confidence * width)
        empty = width - filled
        if confidence >= 0.7:
            color = DesignTokens.SUCCESS.hex
        elif confidence >= 0.4:
            color = DesignTokens.WARNING.hex
        else:
            color = DesignTokens.ERROR.hex
        return (
            f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/] {int(confidence * 100)}%"
        )

    @staticmethod
    def get_loading_spinner() -> str:
        """Get a loading spinner text."""
        return f"[{DesignTokens.PRIMARY.hex}]{ICONS['loading']}[/] Loading..."

class TreeDisplay:
    """Standardized tree/tree view displays."""

    @staticmethod
    def create(title: str, guide_style: str = DesignTokens.PRIMARY.hex) -> Tree:
        """Create a styled tree."""
        return Tree(f"[bold]{title}[/bold]", guide_style=guide_style)

    @staticmethod
    def add_c4_path(tree: Tree, path: list[dict[str, str]]) -> None:
        """Add a C4 path to a tree."""
        for step in path:
            label = (
                f"[bold]{step.get('dimension', 'Step')}[/bold]: {step.get('value', '')}"
            )
            tree.add(label)

class ConfirmationPrompt:
    """Standardized confirmation prompts."""

    @staticmethod
    def confirm(
        action: str,
        details: str | None = None,
        default: bool = False,
    ) -> bool:
        """Show a confirmation prompt."""
        content = f"[bold {DesignTokens.WARNING.hex}]{ICONS['warning']} Are you sure you want to {action}?[/]"
        if details:
            content += f"\n[dim]{details}[/dim]"
        panel = Panel(content, border_style=DesignTokens.WARNING.hex)
        console.print(panel)
        return default

    @staticmethod
    def destructive(action: str, details: str | None = None) -> bool:
        """Show a destructive action confirmation."""
        content = (
            f"[bold {DesignTokens.ERROR.hex}]{ICONS['error']} "
            f"This action cannot be undone:[/]\n"
            f"[bold]{action}[/bold]"
        )
        if details:
            content += f"\n[dim]{details}[/dim]"
        panel = Panel(content, border_style=DesignTokens.ERROR.hex)
        console.print(panel)
        return False

def print_section_header(title: str, icon: str | None = None) -> None:
    """Print a section header."""
    icon_str = f"{icon} " if icon else ""
    console.print(f"\n[bold {DesignTokens.PRIMARY.hex}]{'━' * 60}[/]")
    console.print(f"[bold {DesignTokens.PRIMARY.hex}]{icon_str}{title.upper()}[/]")
    console.print(f"[bold {DesignTokens.PRIMARY.hex}]{'━' * 60}[/]\n")

def print_divider(style: str = DesignTokens.GRAY_600.hex) -> None:
    """Print a divider line."""
    console.print(f"[{style}]{'─' * 60}[/]")

def print_empty_line() -> None:
    """Print an empty line."""
    console.print()
