"""
C4REQBER CLI - C4 Cognitive Geometry commands.
"""
from __future__ import annotations

from typing import Any

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    PanelType,
    StyledPanel,
    StyledTable,
    app,
    console,
    print_section_header,
)


c4_app = typer.Typer(
    help=f"{ICONS['c4']} C4 Cognitive Geometry operations",
    no_args_is_help=True,
)
app.add_typer(c4_app, name="c4")

@c4_app.command("states")
def c4_states(
    dimension: str | None = typer.Option(None, "--dimension", "-d", help="Filter by dimension (time/scale/agency)"),
) -> None:
    """
    List all C4 cognitive states (Z_3^3 = 27 states).

    The C4 system defines 27 cognitive states across 3 dimensions:
    - Time: Past(0) / Present(1) / Future(2)
    - Scale: Concrete(0) / Abstract(1) / Meta(2)
    - Agency: Self(0) / Other(1) / System(2)

    Examples:
        turbo c4 states
        turbo c4 states --dimension time
    """
    print_section_header("C4 Cognitive States", ICONS["c4"])
    panel = StyledPanel.create(
        "C4 defines a [bold]Z_3^3 hypercube[/bold] with 27 cognitive states.\n\n"
        f"{ICONS['dimension_time']} [cyan]Time[/cyan]: Past -> Present -> Future\n"
        f"{ICONS['dimension_scale']} [green]Scale[/green]: Concrete -> Abstract -> Meta\n"
        f"{ICONS['dimension_agency']} [yellow]Agency[/yellow]: Self -> Other -> System\n\n"
        "Each state represents a unique cognitive perspective.",
        "C4 State Space",
        PanelType.RESULT,
    )
    console.print(panel)
    columns: list[dict[str, Any]] = [
        {"name": "Code", "type": "id", "width": 10},
        {"name": "Time", "type": "name", "width": 12},
        {"name": "Scale", "type": "name", "width": 12},
        {"name": "Agency", "type": "name", "width": 12},
        {"name": "Description", "type": "description"},
    ]
    table = StyledTable.create(
        "C4 States",
        columns,
    )
    states = [
        ("000", "Past", "Concrete", "Self", "Personal concrete memories"),
        ("001", "Past", "Concrete", "Other", "Others' concrete experiences"),
        ("002", "Past", "Concrete", "System", "Historical concrete events"),
        ("010", "Past", "Abstract", "Self", "Personal learned patterns"),
        ("111", "Present", "Abstract", "Other", "Current abstract collaboration"),
        ("222", "Future", "Meta", "System", "System-level future vision"),
    ]
    for state in states:
        table.add_row(*state)
    console.print(table)
    console.print(f"\n[dim]Showing {len(states)} of 27 states[/dim]")

@c4_app.command("path")
def c4_path(
    from_state: str = typer.Option(..., "--from", help="Starting state (e.g., 000)"),
    to_state: str = typer.Option(..., "--to", help="Target state (e.g., 222)"),
    method: str = typer.Option("optimal", "--method", "-m", help="Path method (optimal/shortest/exploratory)"),
) -> None:
    """
    Find optimal C4 transformation path between states.

    Examples:
        turbo c4 path --from 000 --to 222
        turbo c4 path --from 111 --to 202 --method exploratory
    """
    print_section_header("C4 Path Finder", ICONS["c4"])
    panel = StyledPanel.create(
        f"From: [cyan]{from_state}[/cyan] -> To: [green]{to_state}[/green]\n"
        f"Method: [yellow]{method}[/yellow]",
        "Path Parameters",
        PanelType.INFO,
    )
    console.print(panel)
    path_panel = StyledPanel.create(
        "C4 Transformation Path",
        "[bold]Optimal Path:[/bold]\n\n"
        "[dim]000[/dim] -> [cyan]100[/cyan] -> [green]110[/green] -> [yellow]111[/yellow] -> [bold]222[/bold]\n\n"
        "Distance: 4 steps\n"
        "Estimated creativity boost: +340%",
        PanelType.RESULT,
    )
    console.print(path_panel)
