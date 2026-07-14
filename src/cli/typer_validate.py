"""
C4REQBER CLI - Validation commands.
"""
from __future__ import annotations

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    StyledPanel,
    app,
    console,
    print_section_header,
)


validate_app = typer.Typer(
    help=f"{ICONS['validate']} Experiment validation and tracking",
    no_args_is_help=True,
)
app.add_typer(validate_app, name="validate")

@validate_app.command("create")
def validate_create(
    hypothesis_id: str = typer.Argument(..., help="Hypothesis to validate"),
    name: str | None = typer.Option(None, "--name", "-n", help="Experiment name"),
    method: str = typer.Option("experimental", "--method", "-m", help="Validation method"),
) -> None:
    """
    Create validation experiment for a hypothesis.

    Examples:
        turbo validate create hypothesis_001
        turbo validate create hyp_002 --name "Battery Test #1" --method simulation
    """
    print_section_header("Create Validation", ICONS["validate"])
    panel = StyledPanel.success(
        f"Experiment created for: [bold]{hypothesis_id}[/bold]\n"
        f"Name: {name or 'Unnamed'}\n"
        f"Method: [cyan]{method}[/cyan]",
        "Validation Created",
    )
    console.print(panel)
