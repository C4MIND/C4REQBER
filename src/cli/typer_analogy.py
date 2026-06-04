"""
C4REQBER CLI - Analogy engine commands.
"""
from __future__ import annotations

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    PanelType,
    StyledPanel,
    app,
    console,
    print_section_header,
)


analogy_app = typer.Typer(
    help=f"{ICONS['analogy']} Cross-domain analogy discovery",
    no_args_is_help=True,
)
app.add_typer(analogy_app, name="analogy")

@analogy_app.command("find")
def analogy_find(
    concept: str = typer.Argument(..., help="Concept to find analogies for"),
    from_domain: str | None = typer.Option(None, "--from", help="Source domain"),
    to_domain: str | None = typer.Option(None, "--to", help="Target domain"),
    depth: int = typer.Option(2, "--depth", "-d", help="Search depth"),
) -> None:
    """
    Find analogies for a concept across domains.

    Examples:
        turbo analogy find "neural network"
        turbo analogy find "Photosynthesis" --to "energy"
        turbo analogy find "immune system" --from biology --to cybersecurity
    """
    print_section_header("Analogy Discovery", ICONS["analogy"])
    panel = StyledPanel.create(
        f"Concept: [bold white]{concept}[/bold white]\n"
        f"From: [cyan]{from_domain or 'Any'}[/cyan] -> To: [green]{to_domain or 'Any'}[/green]\n"
        f"Depth: [yellow]{depth}[/yellow]",
        "Analogy Search",
        PanelType.INFO,
    )
    console.print(panel)
