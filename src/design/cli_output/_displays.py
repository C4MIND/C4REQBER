"""
C4REQBER Design System - CLI displays and progress indicators.
"""
from __future__ import annotations

from typing import Any

from rich.box import ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from ..tokens import ICONS, DesignTokens
from ._panels import PanelType, StyledPanel


console = Console()

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
        panel = StyledPanel.create(content, "Error", PanelType.ERROR)
        console.print(panel)
        if raise_exception:
            raise SystemExit(exit_code)

    @staticmethod
    def show_warning(message: str, suggestion: str | None = None) -> None:
        """Display standardized warning."""
        content = f"[bold]{message}[/bold]"
        if suggestion:
            content += f"\n\n[dim]{ICONS['info']} {suggestion}[/dim]"
        panel = StyledPanel.create(content, "Warning", PanelType.WARNING)
        console.print(panel)

    @staticmethod
    def show_info(message: str, title: str = "Info") -> None:
        """Display standardized info."""
        panel = StyledPanel.create(message, title, PanelType.INFO)
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
        panel = StyledPanel.create(content, "Hypothesis", PanelType.RESULT)
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
        panel = StyledPanel.create(content, "Discovery Summary", PanelType.DISCOVERY)
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
            panel = Panel(content, border_style=DesignTokens.PRIMARY.hex, box=ROUNDED)
            metric_panels.append(panel)
        columns_obj = Columns(metric_panels, equal=True, expand=True)
        console.print(columns_obj)

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
        panel = StyledPanel.create(content, agent_name, PanelType.AGENT)
        console.print(panel)
