"""
TURBO-CDI: One-Shot Mode
Single command for complete discovery cycle
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


console = Console()


@dataclass
class OneShotResult:
    """Result of a one-shot discovery cycle."""

    problem: str
    timestamp: datetime

    # Phase 1: Literature Review
    relevant_papers: List[Dict[str, Any]]
    consensus_analysis: Optional[Dict[str, Any]] = None

    # Phase 2: Hypothesis Generation
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    top_hypothesis: Optional[Dict[str, Any]] = None

    # Phase 3: Validation Planning
    validation_plan: Optional[Dict[str, Any]] = None
    falsifiability_criteria: List[Dict[str, Any]] = field(default_factory=list)

    # Phase 4: Recommendations
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    # Metadata
    duration_seconds: float = 0.0
    total_api_calls: int = 0
    estimated_cost_usd: float = 0.0


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

    def __init__(self):
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
                f"[bold blue]🔬 TURBO-CDI One-Shot Solver[/bold blue]\n\n"
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
                papers = await self._search_literature(problem)
                result.relevant_papers = papers
                result.total_api_calls += 1
                progress.update(task1, completed=100)

            # Phase 2: Consensus Analysis
            if consensus_analysis and result.relevant_papers:
                task2 = progress.add_task(
                    "[cyan]Phase 2: Consensus Analysis...", total=100
                )
                consensus = await self._analyze_consensus(
                    problem, result.relevant_papers
                )
                result.consensus_analysis = consensus
                progress.update(task2, completed=100)

            # Phase 3: Generate Hypotheses
            task3 = progress.add_task(
                "[cyan]Phase 3: Generating Hypotheses...", total=100
            )
            hypotheses = await self._generate_hypotheses(problem, max_hypotheses)
            result.hypotheses = hypotheses
            if hypotheses:
                result.top_hypothesis = hypotheses[0]
            progress.update(task3, completed=100)

            # Phase 4: Validation Planning
            if include_validation and result.top_hypothesis:
                task4 = progress.add_task(
                    "[cyan]Phase 4: Validation Planning...", total=100
                )
                validation = await self._create_validation_plan(result.top_hypothesis)
                result.validation_plan = validation
                result.falsifiability_criteria = validation.get("criteria", [])
                progress.update(task4, completed=100)

            # Phase 5: Recommendations
            task5 = progress.add_task(
                "[cyan]Phase 5: Generating Recommendations...", total=100
            )
            result.recommendations = self._generate_recommendations(result)
            result.next_steps = self._generate_next_steps(result)
            progress.update(task5, completed=100)

        # Calculate duration
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.estimated_cost_usd = self._estimate_cost(result)

        return result

    async def _search_literature(
        self, problem: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search Semantic Scholar for relevant papers."""
        try:
            from src.search.semantic_scholar import get_semantic_scholar_client

            client = get_semantic_scholar_client()
            papers = await client.search_papers(problem, limit=limit)

            return [
                {
                    "title": p.title,
                    "authors": p.authors[:3] if len(p.authors) > 3 else p.authors,
                    "year": p.year,
                    "citation_count": p.citation_count,
                    "abstract": p.abstract[:200] + "..."
                    if len(p.abstract) > 200
                    else p.abstract,
                    "fields": p.fields_of_study,
                    "open_access": p.open_access_pdf is not None,
                    "tldr": p.tldr[:150] + "..." if len(p.tldr) > 150 else p.tldr,
                }
                for p in papers
            ]
        except Exception as e:
            console.print(f"[yellow]Warning: Literature search failed: {e}[/yellow]")
            return []

    async def _analyze_consensus(
        self, problem: str, papers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze scientific consensus from papers."""
        try:
            from src.validation.consensus_meter import (
                get_consensus_meter,
                Evidence,
                EvidenceType,
                EvidenceStrength,
            )

            meter = get_consensus_meter()

            # Create evidence from papers
            evidence_list = []
            for paper in papers:
                # Simplified classification - in production use LLM
                ev_type = (
                    EvidenceType.SUPPORTING
                    if paper.get("citation_count", 0) > 50
                    else EvidenceType.NEUTRAL
                )

                ev = Evidence(
                    source=paper["title"],
                    type=ev_type,
                    strength=EvidenceStrength.MODERATE
                    if paper.get("citation_count", 0) > 20
                    else EvidenceStrength.WEAK,
                    description=paper.get("abstract", ""),
                    citation_count=paper.get("citation_count", 0),
                    year=paper.get("year", 0),
                    peer_reviewed=True,
                )
                evidence_list.append(ev)

            # Calculate consensus
            score = meter.calculate_consensus(
                hypothesis_id="temp",
                hypothesis_text=problem,
                evidence_list=evidence_list,
            )

            return {
                "level": score.consensus_level,
                "confidence": score.confidence_score,
                "supporting": score.supporting_count,
                "contradicting": score.contradicting_count,
                "neutral": score.neutral_count,
                "supporting_score": score.supporting_score,
                "contradicting_score": score.contradicting_score,
                "summary": meter.generate_summary_text(score),
            }
        except Exception as e:
            console.print(f"[yellow]Warning: Consensus analysis failed: {e}[/yellow]")
            return None

    async def _generate_hypotheses(
        self, problem: str, max_hypotheses: int
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses using agent."""
        try:
            from src.agent import get_agent

            agent = get_agent()
            report = await agent.discover(
                problem=problem, max_hypotheses=max_hypotheses
            )

            return [
                {
                    "id": h.id,
                    "hypothesis": h.hypothesis,
                    "mechanism": h.mechanism,
                    "confidence": h.confidence,
                    "method": h.generation_method,
                    "c4_path": h.c4_path,
                    "triz_principles": h.triz_principles,
                    "validation_cost": h.estimated_validation_cost,
                    "validation_time": h.estimated_time_to_validate,
                }
                for h in report.hypotheses
            ]
        except Exception as e:
            console.print(
                f"[yellow]Warning: Hypothesis generation failed: {e}[/yellow]"
            )
            return []

    async def _create_validation_plan(
        self, hypothesis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create validation plan for top hypothesis."""
        try:
            from src.validation import get_validation_tracker, FalsifiabilityCriterion

            # Generate criteria
            criteria = [
                {
                    "statement": f"Measure key metric of {hypothesis['hypothesis'][:50]}...",
                    "measurement": "Primary outcome variable",
                    "threshold": "20% improvement",
                    "difficulty": "medium",
                },
                {
                    "statement": "Check for side effects or negative outcomes",
                    "measurement": "Secondary metrics and safety indicators",
                    "threshold": "Side effects < 10%",
                    "difficulty": "hard",
                },
            ]

            return {
                "hypothesis_id": hypothesis["id"],
                "estimated_cost": hypothesis.get("validation_cost", 5000),
                "estimated_time": hypothesis.get("validation_time", "4 weeks"),
                "criteria": criteria,
            }
        except Exception as e:
            console.print(f"[yellow]Warning: Validation planning failed: {e}[/yellow]")
            return {}

    def _generate_recommendations(self, result: OneShotResult) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        if result.top_hypothesis:
            h = result.top_hypothesis
            recs.append(
                f"Start with hypothesis {h['id']} (confidence: {h['confidence']:.0%})"
            )

            if h.get("validation_cost"):
                recs.append(f"Budget ${h['validation_cost']:,.0f} for validation")

            if result.consensus_analysis:
                level = result.consensus_analysis.get("level", "unknown")
                if level in ["strong", "moderate"]:
                    recs.append("Strong scientific consensus supports this direction")
                elif level == "contested":
                    recs.append("Contradictory evidence exists - validate carefully")

        if len(result.hypotheses) >= 3:
            recs.append(
                f"Consider parallel validation of top {min(3, len(result.hypotheses))} hypotheses"
            )

        return recs

    def _generate_next_steps(self, result: OneShotResult) -> List[str]:
        """Generate next steps."""
        steps = []

        if result.top_hypothesis:
            steps.append(
                f"1. Review hypothesis: {result.top_hypothesis['hypothesis'][:60]}..."
            )
            steps.append("2. Design experiment based on validation plan")

            if result.relevant_papers:
                steps.append(
                    f"3. Review {len(result.relevant_papers)} relevant papers from literature search"
                )

            steps.append("4. Create validation experiment: turbo validate create")

        return steps

    def _estimate_cost(self, result: OneShotResult) -> float:
        """Estimate total cost of the discovery process."""
        # API call costs
        api_cost = result.total_api_calls * 0.01  # $0.01 per API call

        # Validation costs
        validation_cost = sum(h.get("validation_cost", 0) for h in result.hypotheses)

        return api_cost + validation_cost

    def render_summary(self, result: OneShotResult) -> str:
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

        # Literature
        if result.relevant_papers:
            lines.append(
                f"[bold]Literature:[/bold] {len(result.relevant_papers)} papers found"
            )

        # Consensus
        if result.consensus_analysis:
            ca = result.consensus_analysis
            lines.append(
                f"[bold]Consensus:[/bold] {ca['level'].upper()} "
                f"({ca['confidence']:.0f}% confidence)"
            )

        # Top hypothesis
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

        # Recommendations
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
        self, result: OneShotResult, output_path: str, format: str = "markdown"
    ):
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
            md = f"""# TURBO-CDI Discovery Report

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


# Singleton
_solver: Optional[OneShotSolver] = None


def get_one_shot_solver() -> OneShotSolver:
    """Get singleton one-shot solver."""
    global _solver
    if _solver is None:
        _solver = OneShotSolver()
    return _solver
