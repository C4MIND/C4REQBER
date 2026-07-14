"""
C4REQBER: One-Shot Mode
Single command for complete discovery cycle.

This module is a compatibility wrapper that re-exports all public APIs
from the modular solver subpackage. All new code should import from
core / strategies directly.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from .core import (
    OneShotResult,
    console,
    estimate_cost,
    export_report,
    render_summary,
)
from .strategies import (
    analyze_consensus,
    create_validation_plan,
    generate_hypotheses,
    generate_next_steps,
    generate_recommendations,
    run_pattern_simulations,
    search_literature,
)


__all__ = [
    "OneShotResult",
    "OneShotSolver",
    "console",
    "estimate_cost",
    "export_report",
    "render_summary",
    "get_one_shot_solver",
    "search_literature",
    "analyze_consensus",
    "generate_hypotheses",
    "create_validation_plan",
    "run_pattern_simulations",
    "generate_recommendations",
    "generate_next_steps",
]


class OneShotSolver:
    """
    One-shot scientific discovery solver.

    Executes a complete discovery cycle:
    1. Search literature (Semantic Scholar)
    2. Analyze consensus (Consensus Meter)
    3. Generate hypotheses (C4+TRIZ+Analogy)
    4. Create validation plan
    5. Export results

    Usage:
        turbo solve "increase battery density" --full
    """

    def __init__(self) -> None:
        pass

    async def solve(
        self,
        problem: str,
        max_hypotheses: int = 5,
        include_validation: bool = True,
        literature_search: bool = True,
        consensus_analysis: bool = True,
    ) -> OneShotResult:
        """
        Execute complete one-shot discovery cycle.

        Args:
            problem: Research problem to solve
            max_hypotheses: Maximum hypotheses to generate
            include_validation: Create validation plan
            literature_search: Search Semantic Scholar
            consensus_analysis: Analyze scientific consensus

        Returns:
            OneShotResult with all findings
        """
        start_time = datetime.now()
        result = OneShotResult(
            problem=problem,
            timestamp=start_time,
            relevant_papers=[],
        )

        console.print(
            Panel.fit(
                f"[bold blue]🔬 C4REQBER One-Shot Solver[/bold blue]\n\n"
                f"Problem: {problem}\n"
                f"Mode: [green]FULL CYCLE[/green]",
                title="Starting Discovery",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            # Phase 1: Literature Review
            if literature_search:
                task1 = progress.add_task(
                    "[cyan]Phase 1: Literature Review...", total=100
                )
                papers = await search_literature(problem)
                result.relevant_papers = papers
                result.total_api_calls += 1
                progress.update(task1, completed=100)

            # Phase 2: Consensus Analysis
            if consensus_analysis and result.relevant_papers:
                task2 = progress.add_task(
                    "[cyan]Phase 2: Consensus Analysis...", total=100
                )
                consensus = await analyze_consensus(
                    problem, result.relevant_papers
                )
                result.consensus_analysis = consensus
                progress.update(task2, completed=100)

            # Phase 3: Generate Hypotheses
            task3 = progress.add_task(
                "[cyan]Phase 3: Generating Hypotheses...", total=100
            )
            hypotheses = await generate_hypotheses(problem, max_hypotheses)
            result.hypotheses = hypotheses
            if hypotheses:
                result.top_hypothesis = hypotheses[0]
            progress.update(task3, completed=100)

            # Phase 3b: Pattern Simulation (v6 integration)
            if result.hypotheses:
                task3b = progress.add_task(
                    "[cyan]Phase 3b: Running Pattern Simulations...",
                    total=len(result.hypotheses),
                )
                await run_pattern_simulations(result.hypotheses, problem=problem)
                result.hypotheses = sorted(
                    result.hypotheses,
                    key=lambda h: h.get("simulation", {}).get(
                        "confidence", h.get("confidence", 0.5)
                    ),
                    reverse=True,
                )
                result.top_hypothesis = result.hypotheses[0]
                progress.update(task3b, completed=len(result.hypotheses))

            # Phase 4: Validation Planning
            if include_validation and result.top_hypothesis:
                task4 = progress.add_task(
                    "[cyan]Phase 4: Validation Planning...", total=100
                )
                validation = await create_validation_plan(result.top_hypothesis)
                result.validation_plan = validation
                result.falsifiability_criteria = validation.get("criteria", [])
                progress.update(task4, completed=100)

            # Phase 5: Recommendations
            task5 = progress.add_task(
                "[cyan]Phase 5: Generating Recommendations...", total=100
            )
            result.recommendations = generate_recommendations(result)
            result.next_steps = generate_next_steps(result)
            progress.update(task5, completed=100)

        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.estimated_cost_usd = estimate_cost(result)

        return result

    def render_summary(self, result: OneShotResult) -> str:
        """Render rich text summary of results."""
        return render_summary(result)

    def export_report(
        self, result: OneShotResult, output_path: str, format: str = "markdown"
    ) -> Any:
        """Export full report to file."""
        return export_report(result, output_path, format)


def get_one_shot_solver() -> OneShotSolver:
    """Get singleton one-shot solver (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("one_shot_solver", OneShotSolver)
