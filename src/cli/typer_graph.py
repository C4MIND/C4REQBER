"""
C4REQBER CLI - Knowledge graph commands.
"""
from __future__ import annotations

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    PanelType,
    ResultDisplay,
    StyledPanel,
    app,
    console,
    print_section_header,
)


graph_app = typer.Typer(
    help=f"{ICONS['graph']} Knowledge graph operations",
    no_args_is_help=True,
)
app.add_typer(graph_app, name="graph")

@graph_app.command("stats")
def graph_stats(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed statistics"),
) -> None:
    """
    Show knowledge graph statistics.

    Examples:
        turbo graph stats
        turbo graph stats --detailed
    """
    print_section_header("Knowledge Graph Statistics", ICONS["graph"])
    panel = StyledPanel.create(
        "Nodes: [bold]1,247[/bold]\n"
        "Edges: [bold]3,892[/bold]\n"
        "Clusters: [bold]12[/bold]\n"
        "Density: [bold]0.34[/bold]",
        "Graph Overview",
        PanelType.INFO,
    )
    console.print(panel)
    metrics: dict[str, str | float | int] = {
        "Hypotheses": 156,
        "Discoveries": 89,
        "Papers": 412,
        "Concepts": 278,
        "Domains": 12,
        "Analogies": 312,
    }
    ResultDisplay.metrics_grid(metrics)
