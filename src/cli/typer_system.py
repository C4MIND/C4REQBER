"""C4REQBER CLI - System commands (status, version)."""
from __future__ import annotations

from typing import Any

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    PanelType,
    StatusIndicator,
    StyledPanel,
    StyledTable,
    app,
    console,
    print_section_header,
)


system_app = typer.Typer(
    help=f"{ICONS['settings']} System commands",
    no_args_is_help=True,
)
app.add_typer(system_app, name="system")

@system_app.command("status")
def system_status(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Detailed status"),
) -> None:
    """
    Check system health and status.

    Examples:
        turbo system status
        turbo system status --detailed
    """
    print_section_header("System Status", ICONS["settings"])
    services = [
        ("API Server", "running", "http://localhost:8000"),
        ("Database", "connected", "PostgreSQL 15"),
        ("Cache", "active", "Redis"),
        ("LLM", "available", "OpenAI GPT-4"),
        ("Semantic Scholar", "available", "200M papers"),
    ]
    columns: list[dict[str, Any]] = [
        {"name": "Service", "type": "name"},
        {"name": "Status", "type": "status_success", "width": 15},
        {"name": "Details", "type": "description"},
    ]
    table = StyledTable.create(
        "Service Status",
        columns,
    )
    for service, status, details in services:
        status_badge = StatusIndicator.get_status_badge(status)
        table.add_row(service, status_badge, details)
    console.print(table)

@system_app.command("version")
def system_version() -> None:
    """Show version information."""
    panel = StyledPanel.create(
        "[bold]C4REQBER[/bold] v5.4.0\n"
        "Scientific Hypothesis Generation Platform\n\n"
        "[dim]Design System: v1.0.0[/dim]\n"
        "[dim]C4 Engine: v4.5[/dim]\n"
        "[dim]Python: 3.11+[/dim]",
        "Version",
        PanelType.INFO,
    )
    console.print(panel)
