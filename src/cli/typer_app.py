"""C4REQBER CLI - Shared Typer app and Rich-UI design system.

Synchronized with TUI v8 CyberpunkTheme for consistent visual language.
"""
from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text

app = typer.Typer(
    name="turbo",
    help="C4REQBER v5.4 - Scientific Hypothesis Generation Platform",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

# ─── Cyberpunk color palette (synced with TUI v8) ──────────────────────────
_COLORS = {
    "primary": "#00FF41",    # Matrix Green
    "secondary": "#00D4FF",  # Cyber Cyan
    "accent": "#FF006E",     # Neon Pink
    "warning": "#FFB800",    # Amber
    "danger": "#FF2A2A",     # Blood Red
    "muted": "#6B7280",      # Steel Gray
    "ghost": "#2A2A3E",      # Trace lines
    "white": "#FFFFFF",
}

ICONS: dict[str, str] = {
    "agent": "🤖",
    "analogy": "🔗",
    "c4": "🧠",
    "dimension_agency": "🎯",
    "dimension_scale": "📐",
    "dimension_time": "⏳",
    "discover": "🔍",
    "graph": "📊",
    "hypothesis": "💡",
    "info": "ℹ️",
    "multi_agent": "👥",
    "paper": "📄",
    "patent": "📜",
    "search": "🔎",
    "settings": "⚙️",
    "success": "✅",
    "triz": "🔧",
    "validate": "✓",
    "warning": "⚠️",
}


class PanelType:
    """Panel type enum for StyledPanel."""

    INFO = "info"
    RESULT = "result"
    DISCOVERY = "discovery"
    AGENT = "agent"
    WARNING = "warning"
    ERROR = "error"


class DesignTokens:
    """Design tokens for CLI styling."""

    PRIMARY = _COLORS["primary"]
    SECONDARY = _COLORS["secondary"]
    ACCENT = _COLORS["accent"]
    WARNING = _COLORS["warning"]
    DANGER = _COLORS["danger"]
    MUTED = _COLORS["muted"]


class StyledPanel:
    """Rich panel wrapper synced with TUI v8 CyberpunkTheme."""

    _TYPE_STYLES: dict[str, str] = {
        PanelType.INFO: _COLORS["secondary"],
        PanelType.RESULT: _COLORS["primary"],
        PanelType.DISCOVERY: _COLORS["accent"],
        PanelType.AGENT: _COLORS["white"],
        PanelType.WARNING: _COLORS["warning"],
        PanelType.ERROR: _COLORS["danger"],
    }

    @staticmethod
    def create(title: str, content: str, panel_type: str = PanelType.INFO) -> Panel:
        border_color = StyledPanel._TYPE_STYLES.get(panel_type, _COLORS["secondary"])
        return Panel(
            Text.from_markup(content),
            title=f"[bold {border_color}]{title}[/bold {border_color}]",
            border_style=Style(color=border_color),
            padding=(1, 2),
        )

    @staticmethod
    def result(content: str) -> Panel:
        return StyledPanel.create("Result", content, PanelType.RESULT)

    @staticmethod
    def info(content: str) -> Panel:
        return StyledPanel.create("Info", content, PanelType.INFO)

    @staticmethod
    def warning(content: str) -> Panel:
        return StyledPanel.create("Warning", content, PanelType.WARNING)

    @staticmethod
    def error(content: str) -> Panel:
        return StyledPanel.create("Error", content, PanelType.ERROR)

    @staticmethod
    def success(content: str, title: str = "Success") -> Panel:
        return StyledPanel.create(title, content, PanelType.RESULT)


class ProgressIndicator:
    """Rich progress indicators for CLI commands."""

    @staticmethod
    def _make_progress(description: str) -> Progress:
        return Progress(
            SpinnerColumn(style=Style(color=_COLORS["accent"])),
            TextColumn(f"[bold {_COLORS['primary']}]{description}[/bold {_COLORS['primary']}]"),
            BarColumn(complete_style=Style(color=_COLORS["primary"]), finished_style=Style(color=_COLORS["accent"])),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        )

    @staticmethod
    def discovery_progress() -> Progress:
        return ProgressIndicator._make_progress("Discovering")

    @staticmethod
    def search_progress() -> Progress:
        return ProgressIndicator._make_progress("Searching")

    @staticmethod
    def agent_progress() -> Progress:
        return ProgressIndicator._make_progress("Agent")


class ResultDisplay:
    """Rich result display helpers synced with TUI v8."""

    @staticmethod
    def discovery_summary(
        problem: str,
        hypotheses_count: int | None = None,
        avg_confidence: float | None = None,
        methods_used: list[str] | None = None,
        sources: int | None = None,
        gaps: int | None = None,
        confidence: float | None = None,
    ) -> None:
        table = Table(title="Discovery Summary", title_style=Style(color=_COLORS["accent"], bold=True))
        table.add_column("Metric", style=Style(color=_COLORS["secondary"]))
        table.add_column("Value", style=Style(color=_COLORS["primary"]))
        table.add_row("Problem", problem[:60])
        if sources is not None:
            table.add_row("Sources", str(sources))
        if gaps is not None:
            table.add_row("Gaps", str(gaps))
        if confidence is not None:
            table.add_row("Confidence", f"{confidence:.1%}")
        if hypotheses_count is not None:
            table.add_row("Hypotheses", str(hypotheses_count))
        if avg_confidence is not None:
            table.add_row("Avg Confidence", f"{avg_confidence:.1%}")
        if methods_used is not None:
            table.add_row("Methods", ", ".join(methods_used))
        console.print(table)

    @staticmethod
    def hypothesis_card(text: str, confidence: float, method: str, id: str | None = None) -> None:
        color = _COLORS["primary"] if confidence > 0.7 else _COLORS["warning"] if confidence > 0.4 else _COLORS["danger"]
        title = f"[bold {color}]💡 Hypothesis"
        if id:
            title += f" {id}"
        title += f" ({confidence:.0%})[/bold {color}]"
        panel = Panel(
            Text.from_markup(f"[bold]{text[:200]}[/bold]\n\nMethod: {method}"),
            title=title,
            border_style=Style(color=color),
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def metrics_grid(metrics: dict[str, str | float | int]) -> None:
        table = Table(title="Metrics", title_style=Style(color=_COLORS["accent"], bold=True))
        table.add_column("Metric", style=Style(color=_COLORS["secondary"]))
        table.add_column("Value", style=Style(color=_COLORS["primary"]))
        for key, value in metrics.items():
            display = f"{value:.4f}" if isinstance(value, float) else str(value)
            table.add_row(key, display)
        console.print(table)

    @staticmethod
    def agent_result(role: str, output: str, confidence: float | None = None, execution_time: float | None = None) -> None:
        color = _COLORS["secondary"] if confidence is None or confidence > 0.7 else _COLORS["warning"]
        title = f"[bold {color}]{ICONS.get('agent', '🤖')} {role}[/bold {color}]"
        content = output[:500]
        if execution_time is not None:
            content += f"\n\n[dim]Execution time: {execution_time:.2f}s[/dim]"
        panel = Panel(
            Text.from_markup(content),
            title=title,
            border_style=Style(color=color),
            padding=(1, 2),
        )
        console.print(panel)


class StyledTable:
    """Rich table rendering helpers for CLI commands."""

    @staticmethod
    def create(title: str, columns: list[dict[str, Any]] | list[str], rows: list[list[str]] | None = None) -> Table:
        """Create a Rich Table.

        Supports two column formats:
          - list[str]: simple column names
          - list[dict]: {"name": "...", "width": 10, "type": "id|name|description"}
        Optionally pre-populates rows.
        """
        table = Table(title=title, title_style=Style(color=_COLORS["accent"], bold=True))
        for col in columns:
            if isinstance(col, dict):
                name = col.get("name", "")
                width = col.get("width")
                col_type = col.get("type", "")
                style = _COLORS["secondary"]
                if "success" in col_type:
                    style = _COLORS["primary"]
                elif "danger" in col_type:
                    style = _COLORS["danger"]
                kwargs: dict[str, Any] = {"style": Style(color=style)}
                if width:
                    kwargs["max_width"] = width
                    kwargs["no_wrap"] = True
                table.add_column(name, **kwargs)
            else:
                table.add_column(str(col), style=Style(color=_COLORS["secondary"]))
        if rows:
            for row in rows:
                table.add_row(*row)
        return table

    @staticmethod
    def search_results_table(results: list[dict[str, str]] | None = None) -> Table:
        table = Table(title="Search Results", title_style=Style(color=_COLORS["accent"], bold=True))
        results = results or []
        if results:
            for key in results[0].keys():
                table.add_column(key, style=Style(color=_COLORS["secondary"]))
            for item in results:
                table.add_row(*[str(v)[:40] for v in item.values()])
        return table


class StatusIndicator:
    """Status badge helpers synced with TUI v8."""

    _STATUS_COLORS: dict[str, str] = {
        "success": _COLORS["primary"],
        "ready": _COLORS["primary"],
        "running": _COLORS["secondary"],
        "warning": _COLORS["warning"],
        "error": _COLORS["danger"],
        "failed": _COLORS["danger"],
        "pending": _COLORS["muted"],
    }

    @staticmethod
    def get_status_badge(status: str) -> str:
        color = StatusIndicator._STATUS_COLORS.get(status.lower(), _COLORS["white"])
        return f"[bold {color}]{status.upper()}[/bold {color}]"


def print_section_header(title: str, icon: str = "") -> None:
    """Print a section header with optional icon, synced with TUI v8 style."""
    console.print()
    console.print(Rule(title=f"[bold {_COLORS['accent']}]{icon} {title}[/bold {_COLORS['accent']}]", style=Style(color=_COLORS["ghost"])))
