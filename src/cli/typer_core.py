"""
C4REQBER CLI - Core discovery commands (solve, discover, explain).
"""

from __future__ import annotations

import typer

from .typer_app import (  # type: ignore[attr-defined]
    ICONS,
    DesignTokens,
    PanelType,
    ProgressIndicator,
    ResultDisplay,
    StyledPanel,
    app,
    console,
    print_section_header,
)


core_app = typer.Typer(
    help=f"{ICONS['discover']} Core discovery commands (most used)",
    no_args_is_help=True,
)
app.add_typer(core_app, name="core")


@core_app.command("solve")
@app.command("solve")
def solve_command(
    problem: str = typer.Argument(..., help="Problem statement to solve"),
    full: bool = typer.Option(False, "--full", "-f", help="Full analysis with all methods"),
    max_hypotheses: int = typer.Option(5, "--max", "-n", help="Maximum hypotheses to generate"),
    output: str | None = typer.Option(None, "--output", "-o", help="Export to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """
    One-shot full discovery cycle - complete analysis in a single command.

    This is the fastest way to get comprehensive results combining:
    - C4 Cognitive Geometry analysis
    - TRIZ methodology
    - Analogy discovery
    - Literature search (Semantic Scholar)
    - Multi-agent validation

    Examples:
        turbo solve "increase battery life"
        turbo solve "optimize neural network" --full --output report.md
        turbo core solve "reduce manufacturing cost" -n 10
    """
    # Honesty: this legacy turbo CLI path used hardcoded fake hypotheses / metrics.
    # Fail-closed — real solve is `blast solve` (blast_app → UniversalSolvePipeline).
    console.print(
        "[red]error:[/red] legacy `turbo solve` / `typer_app` path is disabled "
        '(demo stubs removed). Use: [bold]blast solve[/bold] "your problem"'
    )
    raise typer.Exit(2)


@core_app.command("discover")
@app.command("discover")
def discover_command(
    problem: str = typer.Argument(..., help="Problem statement"),
    agents: int = typer.Option(4, "--agents", "-a", help="Number of agents to use"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Debate iterations"),
    output: str | None = typer.Option(None, "--output", "-o", help="Export results"),
) -> None:
    """
    Multi-agent collaborative discovery with debate.

    Uses specialized AI agents:
    - [cyan]Analyst[/cyan]: Breaks down problem structure
    - [green]Scientist[/cyan]: Generates hypotheses
    - [yellow]Critic[/cyan]: Evaluates and finds flaws
    - [blue]Synthesizer[/cyan]: Combines best ideas

    Examples:
        turbo discover "improve heat dissipation"
        turbo discover "reduce material cost" --agents 6 --iterations 5
    """
    console.print(
        "[red]error:[/red] legacy `turbo discover` is disabled (demo stubs). "
        "Use: [bold]blast turbo[/bold] / [bold]blast solve[/bold]"
    )
    raise typer.Exit(2)


@core_app.command("explain")
@app.command("explain")
def explain_command(
    discovery_id: str = typer.Argument(..., help="Discovery ID to explain"),
    level: str = typer.Option(
        "technical", "--level", "-l", help="Explanation level (simple/technical/expert)"
    ),
    focus: str | None = typer.Option(None, "--focus", "-f", help="Focus on specific aspect"),
) -> None:
    """
    Explain C4 reasoning and discovery process.

    Shows:
    - C4 transformation path taken
    - Why specific states were chosen
    - How TRIZ principles were applied
    - Evidence supporting each hypothesis

    Examples:
        turbo explain discovery_001
        turbo explain discovery_001 --level simple
        turbo explain discovery_001 --focus triz
    """
    console.print(
        "[red]error:[/red] legacy `turbo explain` is disabled (demo stubs). "
        "Use: [bold]blast[/bold] product CLI"
    )
    raise typer.Exit(2)
