"""
C4REQBER: Explainability Engine - Renderers
"""
from __future__ import annotations

from explainability.core import ExplanationLevel, PathExplanation


def render_explanation(
    explanation: PathExplanation,
    level: ExplanationLevel = ExplanationLevel.TECHNICAL,
) -> None:
    """Render explanation to console."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Header
    console.print(
        Panel.fit(
            f"[bold blue]C4 Path Explanation[/bold blue]\n\n"
            f"Problem: {explanation.problem[:60]}...\n"
            f"Path: {' → '.join(explanation.c4_path)}",
            title="🔍 Explainability Engine",
        )
    )

    # Summary
    console.print(f"\n[bold]Summary:[/bold]\n{explanation.summary}\n")
    console.print(f"[bold]Intuition:[/bold] {explanation.intuition}")
    console.print(f"[bold]Key Insight:[/bold] {explanation.key_insight}\n")

    # Step-by-step
    console.print("[bold]Step-by-Step Breakdown:[/bold]")
    for step in explanation.steps:
        console.print(f"\n[cyan]Step {step.step_number}: {step.operator}[/cyan]")
        console.print(f"  [dim]What:[/dim] {step.what}")
        console.print(f"  [dim]Why:[/dim] {step.why}")
        console.print(f"  [dim]How:[/dim] {step.how}")
        if step.example:
            console.print(f"  [dim]Example:[/dim] {step.example}")

    # Expected outcomes
    console.print("\n[bold]Expected Outcomes:[/bold]")
    for outcome in explanation.expected_outcomes:
        console.print(f"  ✓ {outcome}")

    # Warnings
    console.print("\n[bold yellow]Warning Signs:[/bold yellow]")
    for warning in explanation.warning_signs:
        console.print(f"  ⚠ {warning}")

    # Alternatives
    if explanation.alternative_paths:
        console.print("\n[bold]Alternative Paths:[/bold]")
        for path in explanation.alternative_paths:
            console.print(f"  → {' → '.join(path)}")
