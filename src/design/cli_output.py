"""
Standardized CLI output components using design tokens.

Provides consistent, beautiful output formatting for the CLI interface
with proper semantic styling for different content types.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from rich.box import ROUNDED, Box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from .tokens import ICONS, DesignTokens, get_color_by_status


console = Console()


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
        """Create a standardized table.

        Args:
            title: Table title
            columns: List of column definitions with keys:
                - name: Column header
                - type: Style type (id, name, value, status_success, etc.)
                - width: Optional fixed width
                - max_width: Optional max width
                - justify: left/center/right
                - no_wrap: Whether to prevent wrapping
        """
        table = Table(
            title=f"[bold]{title}[/bold]",
            show_header=show_header,
            header_style="bold white",
            box=box_style,
            expand=expand,
        )

        for col in columns:
            style = StyledTable.COLUMN_STYLES.get(col.get("type"), "white")
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
                {
                    "name": "Confidence",
                    "type": "confidence",
                    "width": 12,
                    "justify": "center",
                },
                {"name": "Method", "type": "method", "width": 15},
                {
                    "name": "Status",
                    "type": "status_success",
                    "width": 12,
                    "justify": "center",
                },
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
                {
                    "name": "Hypotheses",
                    "type": "metric",
                    "width": 10,
                    "justify": "center",
                },
                {
                    "name": "Confidence",
                    "type": "confidence",
                    "width": 12,
                    "justify": "center",
                },
                {"name": "Date", "type": "date", "width": 12},
                {
                    "name": "Status",
                    "type": "status_success",
                    "width": 10,
                    "justify": "center",
                },
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
                {
                    "name": "Citations",
                    "type": "metric",
                    "width": 10,
                    "justify": "center",
                },
                {
                    "name": "Relevance",
                    "type": "confidence",
                    "width": 12,
                    "justify": "center",
                },
            ],
        )


class ProgressIndicator:
    """Standardized progress indicators."""

    @staticmethod
    def discovery_progress() -> Progress:
        """Progress bar for discovery operations."""
        return Progress(
            SpinnerColumn(spinner_name="dots", style=DesignTokens.PRIMARY.hex),
            TextColumn("[bold white]{task.description}"),
            BarColumn(
                complete_style=DesignTokens.PRIMARY.hex,
                finished_style=DesignTokens.SUCCESS.hex,
                pulse_style=DesignTokens.INFO.hex,
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=False,
        )

    @staticmethod
    def search_progress() -> Progress:
        """Progress bar for search operations."""
        return Progress(
            SpinnerColumn(spinner_name="line", style=DesignTokens.INFO.hex),
            TextColumn("[bold white]{task.description}"),
            console=console,
            transient=True,
        )

    @staticmethod
    def agent_progress() -> Progress:
        """Progress bar for multi-agent operations."""
        return Progress(
            SpinnerColumn(spinner_name="dots12", style=DesignTokens.ACCENT.hex),
            TextColumn("[bold white]{task.description}"),
            BarColumn(
                complete_style=DesignTokens.ACCENT.hex,
                finished_style=DesignTokens.SUCCESS.hex,
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )

    @staticmethod
    def validation_progress() -> Progress:
        """Progress bar for validation operations."""
        return Progress(
            SpinnerColumn(spinner_name="bouncingBar", style=DesignTokens.SUCCESS.hex),
            TextColumn("[bold white]{task.description}"),
            BarColumn(
                complete_style=DesignTokens.SUCCESS.hex,
                finished_style=DesignTokens.PRIMARY.hex,
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )


class ErrorDisplay:
    """Standardized error display."""

    @staticmethod
    def show_error(
        message: str,
        suggestion: str | None = None,
        exit_code: int = 1,
        raise_exception: bool = True,
    ) -> None:
        """Display standardized error."""
        content = f"[bold]{message}[/bold]"
        if suggestion:
            content += f"\n\n[dim]{ICONS['info']} {suggestion}[/dim]"

        panel = StyledPanel.create(
            content,
            "Error",
            PanelType.ERROR,
        )
        console.print(panel)

        if raise_exception:
            raise SystemExit(exit_code)

    @staticmethod
    def show_warning(message: str, suggestion: str | None = None) -> None:
        """Display standardized warning."""
        content = f"[bold]{message}[/bold]"
        if suggestion:
            content += f"\n\n[dim]{ICONS['info']} {suggestion}[/dim]"

        panel = StyledPanel.create(
            content,
            "Warning",
            PanelType.WARNING,
        )
        console.print(panel)

    @staticmethod
    def show_info(message: str, title: str = "Info") -> None:
        """Display standardized info."""
        panel = StyledPanel.create(
            message,
            title,
            PanelType.INFO,
        )
        console.print(panel)


class ResultDisplay:
    """Standardized result displays."""

    @staticmethod
    def hypothesis_card(
        hypothesis: str,
        confidence: float,
        method: str,
        c4_path: list[str] | None = None,
        supporting_evidence: list[str] | None = None,
    ) -> None:
        """Display a hypothesis result card."""
        confidence_pct = int(confidence * 100)
        filled_blocks = confidence_pct // 10
        confidence_bar = (
            f"[{DesignTokens.ACCENT.hex}]{'█' * filled_blocks}[/]"
            f"[dim]{'░' * (10 - filled_blocks)}[/]"
        )

        content = f"""[bold white]{hypothesis}[/bold white]

[dim]{"━" * 50}[/dim]
[bold]Confidence:[/bold]    {confidence_bar} {confidence_pct}%
[bold]Method:[/bold]        {method}
"""
        if c4_path:
            path_str = " → ".join(c4_path)
            content += f"[bold]C4 Path:[/bold]       {path_str}\n"

        if supporting_evidence:
            content += "\n[bold]Supporting Evidence:[/bold]\n"
            for i, evidence in enumerate(supporting_evidence[:3], 1):
                content += f"  {i}. {evidence}\n"

        panel = StyledPanel.create(
            content,
            "Hypothesis",
            PanelType.RESULT,
        )
        console.print(panel)

    @staticmethod
    def discovery_summary(
        problem: str,
        hypotheses_count: int,
        avg_confidence: float,
        methods_used: list[str],
    ) -> None:
        """Display a discovery summary."""
        confidence_pct = int(avg_confidence * 100)

        content = f"""[bold]Problem:[/bold] {problem}

[dim]{"━" * 50}[/dim]
[bold]Hypotheses Generated:[/bold]   {hypotheses_count}
[bold]Average Confidence:[/bold]     {confidence_pct}%
[bold]Methods Used:[/bold]          {", ".join(methods_used)}
"""
        panel = StyledPanel.create(
            content,
            "Discovery Summary",
            PanelType.DISCOVERY,
        )
        console.print(panel)

    @staticmethod
    def metrics_grid(metrics: dict[str, Any], columns: int = 4) -> None:
        """Display metrics in a grid."""
        metric_panels = []

        for label, value in metrics.items():
            content = (
                f"[bold {DesignTokens.PRIMARY.hex}]{value}[/bold {DesignTokens.PRIMARY.hex}]\n"
                f"[dim]{label}[/dim]"
            )
            panel = Panel(
                content,
                border_style=DesignTokens.PRIMARY.hex,
                box=ROUNDED,
            )
            metric_panels.append(panel)

        columns_obj = Columns(metric_panels, equal=True, expand=True)
        console.print(columns_obj)

    @staticmethod
    def _metric_card(label: str, value: Any) -> Panel:
        """Create a single metric card."""
        content = (
            f"[bold {DesignTokens.PRIMARY.hex}]{value}[/bold {DesignTokens.PRIMARY.hex}]\n"
            f"[dim]{label}[/dim]"
        )
        return Panel(content, border_style=DesignTokens.PRIMARY.hex)

    @staticmethod
    def agent_result(
        agent_name: str,
        result: str,
        confidence: float | None = None,
        execution_time: float | None = None,
    ) -> None:
        """Display an agent result."""
        content = f"[bold]{result}[/bold]"

        details = []
        if confidence is not None:
            details.append(f"Confidence: {int(confidence * 100)}%")
        if execution_time is not None:
            details.append(f"Time: {execution_time:.2f}s")

        if details:
            content += f"\n[dim]{', '.join(details)}[/dim]"

        panel = StyledPanel.create(
            content,
            agent_name,
            PanelType.AGENT,
        )
        console.print(panel)


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
        tree = Tree(
            f"[bold]{title}[/bold]",
            guide_style=guide_style,
        )
        return tree

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

        # This would use typer.prompt in actual implementation
        # Returning default for now
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
