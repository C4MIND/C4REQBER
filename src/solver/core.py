"""
C4REQBER: Core Solver Logic
Result dataclass, cost estimation, rendering, and reporting.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console


console = Console()


@dataclass
class OneShotResult:
    """Result of a one-shot discovery cycle."""

    problem: str
    timestamp: datetime

    # Phase 1: Literature Review
    relevant_papers: list[dict[str, Any]]
    consensus_analysis: dict[str, Any] | None = None

    # Phase 2: Hypothesis Generation
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    top_hypothesis: dict[str, Any] | None = None

    # Phase 3: Validation Planning
    validation_plan: dict[str, Any] | None = None
    falsifiability_criteria: list[dict[str, Any]] = field(default_factory=list)

    # Phase 4: Recommendations
    recommendations: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # Metadata
    duration_seconds: float = 0.0
    total_api_calls: int = 0
    estimated_cost_usd: float = 0.0


def estimate_cost(result: OneShotResult) -> float:
    """Estimate total cost of the discovery process."""
    api_cost = result.total_api_calls * 0.01
    validation_cost = sum(h.get("validation_cost", 0) for h in result.hypotheses)
    return api_cost + validation_cost  # type: ignore[no-any-return]


def render_summary(result: OneShotResult) -> str:
    """Render rich text summary of results."""
    lines = [
        "",
        "[bold green]✓ Discovery Cycle Complete![/bold green]",
        "",
        f"Duration: {result.duration_seconds:.1f} seconds",
        f"API Calls: {result.total_api_calls}",
        f"Estimated Cost: ${result.estimated_cost_usd:,.0f}",
        "",
    ]

    if result.relevant_papers:
        lines.append(
            f"[bold]Literature:[/bold] {len(result.relevant_papers)} papers found"
        )

    if result.consensus_analysis:
        ca = result.consensus_analysis
        lines.append(
            f"[bold]Consensus:[/bold] {ca['level'].upper()} "
            f"({ca['confidence']:.0f}% confidence)"
        )

    if result.top_hypothesis:
        h = result.top_hypothesis
        lines.extend(
            [
                "",
                "[bold]Top Hypothesis:[/bold]",
                f"{h['hypothesis']}",
                f"Method: {h['method']} | Confidence: {h['confidence']:.0%}",
            ]
        )
        sim = h.get("simulation")
        if sim and sim.get("pattern_id"):
            lines.append(
                f"Simulation: {sim['pattern_id']} ({sim.get('status', 'unknown')})"
            )

    if result.recommendations:
        lines.extend(
            [
                "",
                "[bold]Recommendations:[/bold]",
            ]
        )
        for rec in result.recommendations[:3]:
            lines.append(f"  • {rec}")

    return "\n".join(lines)


def export_report(
    result: OneShotResult, output_path: str, format: str = "markdown"
) -> None:
    """Export full report to file."""
    path = Path(output_path)

    if format == "json":
        data = {
            "problem": result.problem,
            "timestamp": result.timestamp.isoformat(),
            "duration_seconds": result.duration_seconds,
            "literature": result.relevant_papers,
            "consensus": result.consensus_analysis,
            "hypotheses": result.hypotheses,
            "validation_plan": result.validation_plan,
            "recommendations": result.recommendations,
            "next_steps": result.next_steps,
            "estimated_cost_usd": result.estimated_cost_usd,
        }
        path.write_text(json.dumps(data, indent=2))

    else:  # Markdown
        md = f"""# C4REQBER Discovery Report

**Problem:** {result.problem}
**Generated:** {result.timestamp.strftime("%Y-%m-%d %H:%M")}
**Duration:** {result.duration_seconds:.1f} seconds

## Executive Summary

"""

        if result.consensus_analysis:
            md += f"""**Scientific Consensus:** {result.consensus_analysis["level"].upper()}
{result.consensus_analysis["summary"]}

"""

        if result.top_hypothesis:
            h = result.top_hypothesis
            md += f"""**Top Hypothesis:** {h["hypothesis"]}

- **Confidence:** {h["confidence"]:.0%}
- **Method:** {h["method"]}
- **Estimated Validation Cost:** ${h.get("validation_cost", 0):,.0f}
- **Estimated Time:** {h.get("validation_time", "Unknown")}

"""

        md += "## Recommendations\n\n"
        for rec in result.recommendations:
            md += f"- {rec}\n"

        md += "\n## Next Steps\n\n"
        for step in result.next_steps:
            md += f"{step}\n"

        if result.relevant_papers:
            md += "\n## Literature Review\n\n"
            for paper in result.relevant_papers[:5]:
                md += f"### {paper['title']}\n"
                md += f"- Authors: {', '.join(paper['authors'])}\n"
                md += f"- Year: {paper['year']} | Citations: {paper['citation_count']}\n"
                if paper.get("tldr"):
                    md += f"- TL;DR: {paper['tldr']}\n"
                md += "\n"

        if result.hypotheses:
            md += "\n## All Hypotheses\n\n"
            for h in result.hypotheses:
                md += f"### {h['id']} (Confidence: {h['confidence']:.0%})\n\n"
                md += f"**Hypothesis:** {h['hypothesis']}\n\n"
                md += f"**Mechanism:** {h['mechanism']}\n\n"
                md += f"**C4 Path:** {' → '.join(h['c4_path'])}\n\n"
                md += f"**TRIZ Principles:** {', '.join(map(str, h['triz_principles']))}\n\n"
                md += "---\n\n"

        path.write_text(md)

    console.print(f"[green]✓ Report exported to {output_path}[/green]")
