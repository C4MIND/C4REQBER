"""
C4REQBER CLI - TRIZ methodology commands.
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


triz_app = typer.Typer(
    help=f"{ICONS['triz']} TRIZ methodology and C4 bridge",
    no_args_is_help=True,
)
app.add_typer(triz_app, name="triz")

@triz_app.command("list")
def triz_list(
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
) -> None:
    """
    List 40 TRIZ principles with descriptions.

    Examples:
        turbo triz list[Any]
        turbo triz list[Any] --category "mechanical"
    """
    print_section_header("TRIZ 40 Principles", ICONS["triz"])
    columns: list[dict[str, Any]] = [
        {"name": "#", "type": "id", "width": 6},
        {"name": "Principle", "type": "name"},
        {"name": "Category", "type": "description", "width": 20},
    ]
    table = StyledTable.create(
        "TRIZ Principles",
        columns,
    )
    principles = [
        ("1", "Segmentation", "Structural"),
        ("2", "Taking out", "Structural"),
        ("19", "Periodic action", "Temporal"),
        ("24", "Mediator", "Functional"),
        ("35", "Parameter changes", "Physical"),
    ]
    for p in principles:
        table.add_row(*p)
    console.print(table)

@triz_app.command("solve")
def triz_solve(
    improving: str = typer.Option(..., "--improving", "-i", help="What to improve"),
    worsening: str = typer.Option(..., "--worsening", "-w", help="What gets worse"),
    domain: str = typer.Option("general", "--domain", "-d", help="Technical domain"),
) -> None:
    """
    Solve contradiction using C4+TRIZ.

    Examples:
        turbo triz solve --improving "speed" --worsening "accuracy"
        turbo triz solve -i "battery capacity" -w "charging time" -d energy
    """
    print_section_header("TRIZ Contradiction Solver", ICONS["triz"])
    panel = StyledPanel.create(
        f"Improving: [green]{improving}[/green]\n"
        f"Worsening: [red]{worsening}[/red]\n"
        f"Domain: [cyan]{domain}[/cyan]",
        "Contradiction",
        PanelType.RESULT,
    )
    console.print(panel)
    solution_panel = StyledPanel.success(
        "[bold]Recommended Principles:[/bold]\n\n"
        "1. [bold]Principle 1: Segmentation[/bold]\n"
        "   -> Divide the process into independent parts\n\n"
        "2. [bold]Principle 19: Periodic Action[/bold]\n"
        "   -> Use intermittent rather than continuous action\n\n"
        "3. [bold]Principle 35: Parameter Changes[/bold]\n"
        "   -> Change physical/chemical state",
        "TRIZ Solution",
    )
    console.print(solution_panel)
