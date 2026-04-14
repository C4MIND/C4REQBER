"""
TURBO-CDI: Dashboard Module
Business metrics, ROI tracking, and analytics
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, BarColumn


console = Console()


@dataclass
class DashboardMetrics:
    """Key dashboard metrics."""

    # Discovery metrics
    total_hypotheses: int
    validated_hypotheses: int
    falsified_hypotheses: int
    pending_validation: int

    # Time metrics
    avg_time_to_hypothesis: float  # minutes
    avg_time_to_validation: float  # days

    # Quality metrics
    validation_rate: float  # 0-1
    avg_confidence_score: float  # 0-1
    calibration_score: float  # Brier score

    # Cost metrics
    total_estimated_cost: float  # USD
    avg_cost_per_hypothesis: float  # USD
    roi_estimate: float  # percentage

    # Activity metrics
    discoveries_this_week: int
    discoveries_this_month: int
    active_experiments: int

    # Domain breakdown
    domain_distribution: Dict[str, int]

    # Method effectiveness
    method_success_rates: Dict[str, float]


class Dashboard:
    """
    TURBO-CDI Analytics Dashboard.

    Tracks business metrics:
    - Time-to-hypothesis
    - Validation rates
    - ROI estimates
    - Domain performance
    - Method effectiveness
    """

    def __init__(self):
        self.kg = None  # Lazy import
        self.metrics_cache: Optional[DashboardMetrics] = None
        self.last_update: Optional[datetime] = None

    def _get_kg(self):
        """Lazy import knowledge graph."""
        if self.kg is None:
            from src.graph.knowledge_graph import get_knowledge_graph

            self.kg = get_knowledge_graph()
        return self.kg

    def calculate_metrics(self, force_refresh: bool = False) -> DashboardMetrics:
        """Calculate all dashboard metrics."""
        # Use cache if fresh (5 minutes)
        if (
            not force_refresh
            and self.metrics_cache
            and self.last_update
            and (datetime.now() - self.last_update) < timedelta(minutes=5)
        ):
            return self.metrics_cache

        kg = self._get_kg()

        # Get all discoveries
        discoveries = kg.get_nodes_by_type("discovery")
        experiments = kg.get_nodes_by_type("experiment")

        # Calculate metrics
        metrics = DashboardMetrics(
            total_hypotheses=len(discoveries),
            validated_hypotheses=self._count_validated(discoveries),
            falsified_hypotheses=self._count_falsified(discoveries),
            pending_validation=len(experiments),
            avg_time_to_hypothesis=self._calc_avg_time_to_hypothesis(discoveries),
            avg_time_to_validation=self._calc_avg_time_to_validation(experiments),
            validation_rate=self._calc_validation_rate(discoveries),
            avg_confidence_score=self._calc_avg_confidence(discoveries),
            calibration_score=self._calc_calibration_score(),
            total_estimated_cost=self._calc_total_cost(discoveries),
            avg_cost_per_hypothesis=self._calc_avg_cost(discoveries),
            roi_estimate=self._estimate_roi(discoveries),
            discoveries_this_week=self._count_recent(discoveries, days=7),
            discoveries_this_month=self._count_recent(discoveries, days=30),
            active_experiments=self._count_active_experiments(experiments),
            domain_distribution=self._calc_domain_distribution(discoveries),
            method_success_rates=self._calc_method_success_rates(discoveries),
        )

        self.metrics_cache = metrics
        self.last_update = datetime.now()
        return metrics

    def _count_validated(self, discoveries: List[Dict]) -> int:
        """Count validated discoveries."""
        count = 0
        for d in discoveries:
            status = d.get("metadata", {}).get("status", "")
            if status == "validated":
                count += 1
        return count

    def _count_falsified(self, discoveries: List[Dict]) -> int:
        """Count falsified discoveries."""
        count = 0
        for d in discoveries:
            status = d.get("metadata", {}).get("status", "")
            if status == "falsified":
                count += 1
        return count

    def _calc_avg_time_to_hypothesis(self, discoveries: List[Dict]) -> float:
        """Calculate average time to generate hypothesis."""
        # Placeholder - would track actual generation time
        return 2.5  # minutes

    def _calc_avg_time_to_validation(self, experiments: List[Dict]) -> float:
        """Calculate average time to validate."""
        # Placeholder
        return 14.0  # days

    def _calc_validation_rate(self, discoveries: List[Dict]) -> float:
        """Calculate validation rate."""
        total = len(discoveries)
        if total == 0:
            return 0.0

        validated = self._count_validated(discoveries)
        falsified = self._count_falsified(discoveries)
        decided = validated + falsified

        return decided / total if total > 0 else 0.0

    def _calc_avg_confidence(self, discoveries: List[Dict]) -> float:
        """Calculate average confidence score."""
        if not discoveries:
            return 0.0

        scores = []
        for d in discoveries:
            score = d.get("metadata", {}).get("confidence_score", 0.5)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _calc_calibration_score(self) -> float:
        """Get calibration score from validation tracker."""
        try:
            from src.validation import get_validation_tracker

            tracker = get_validation_tracker()
            # Brier score (lower is better, so we invert)
            brier = tracker.calibration_tracker.calculate_brier_score()
            return max(0, 1 - brier)  # Convert to 0-1 scale
        except (ImportError, AttributeError, ZeroDivisionError) as e:
            return 0.5

    def _calc_total_cost(self, discoveries: List[Dict]) -> float:
        """Calculate total estimated validation cost."""
        total = 0.0
        for d in discoveries:
            cost = d.get("metadata", {}).get("estimated_validation_cost", 5000)
            total += cost
        return total

    def _calc_avg_cost(self, discoveries: List[Dict]) -> float:
        """Calculate average cost per hypothesis."""
        if not discoveries:
            return 0.0
        return self._calc_total_cost(discoveries) / len(discoveries)

    def _estimate_roi(self, discoveries: List[Dict]) -> float:
        """Estimate ROI based on validation rates."""
        validation_rate = self._calc_validation_rate(discoveries)
        # Simplified ROI model
        # Assume validated hypotheses worth $100k on average
        # Total cost is investment
        total_cost = self._calc_total_cost(discoveries)
        if total_cost == 0:
            return 0.0

        validated_value = self._count_validated(discoveries) * 100000
        roi = (validated_value - total_cost) / total_cost * 100
        return roi

    def _count_recent(self, discoveries: List[Dict], days: int) -> int:
        """Count discoveries from last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        count = 0

        for d in discoveries:
            created = d.get("created_at", "")
            if isinstance(created, str):
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created_dt > cutoff:
                        count += 1
                except (ValueError, TypeError):
                    pass

        return count

    def _count_active_experiments(self, experiments: List[Dict]) -> int:
        """Count currently active experiments."""
        count = 0
        for e in experiments:
            status = e.get("metadata", {}).get("status", "")
            if status == "running":
                count += 1
        return count

    def _calc_domain_distribution(self, discoveries: List[Dict]) -> Dict[str, int]:
        """Calculate distribution across domains."""
        distribution = {}
        for d in discoveries:
            domain = d.get("metadata", {}).get("domain", "general")
            distribution[domain] = distribution.get(domain, 0) + 1
        return distribution

    def _calc_method_success_rates(self, discoveries: List[Dict]) -> Dict[str, float]:
        """Calculate success rate by generation method."""
        # Group by method
        by_method = {}
        for d in discoveries:
            method = d.get("metadata", {}).get("generation_method", "unknown")
            status = d.get("metadata", {}).get("status", "pending")

            if method not in by_method:
                by_method[method] = {"total": 0, "validated": 0}

            by_method[method]["total"] += 1
            if status == "validated":
                by_method[method]["validated"] += 1

        # Calculate rates
        rates = {}
        for method, counts in by_method.items():
            rates[method] = (
                counts["validated"] / counts["total"] if counts["total"] > 0 else 0.0
            )

        return rates

    def render_dashboard(self):
        """Render full dashboard to console."""
        metrics = self.calculate_metrics()

        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        # Header
        layout["header"].update(
            Panel(
                "[bold blue]🔬 TURBO-CDI Analytics Dashboard[/bold blue]",
                subtitle=f"Last updated: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'Never'}",
            )
        )

        # Left column - Key metrics
        left_content = self._render_metrics_panel(metrics)
        layout["left"].update(left_content)

        # Right column - Charts and breakdowns
        right_content = self._render_breakdown_panel(metrics)
        layout["right"].update(right_content)

        # Footer
        layout["footer"].update(
            Panel(
                f"[dim]Total discoveries: {metrics.total_hypotheses} | "
                f"Validation rate: {metrics.validation_rate:.1%} | "
                f"ROI estimate: {metrics.roi_estimate:+.0f}%[/dim]",
                title="Summary",
            )
        )

        console.print(layout)

    def _render_metrics_panel(self, metrics: DashboardMetrics) -> Panel:
        """Render key metrics panel."""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta", justify="right")

        table.add_row("Total Hypotheses", str(metrics.total_hypotheses))
        table.add_row("Validated", f"[green]{metrics.validated_hypotheses}[/green]")
        table.add_row("Falsified", f"[red]{metrics.falsified_hypotheses}[/red]")
        table.add_row("Pending", str(metrics.pending_validation))
        table.add_row("", "")
        table.add_row(
            "Avg Time to Hypothesis", f"{metrics.avg_time_to_hypothesis:.1f} min"
        )
        table.add_row(
            "Avg Time to Validation", f"{metrics.avg_time_to_validation:.0f} days"
        )
        table.add_row("", "")
        table.add_row("Validation Rate", f"{metrics.validation_rate:.1%}")
        table.add_row("Avg Confidence", f"{metrics.avg_confidence_score:.1%}")
        table.add_row("Calibration Score", f"{metrics.calibration_score:.1%}")
        table.add_row("", "")
        table.add_row("Total Est. Cost", f"${metrics.total_estimated_cost:,.0f}")
        table.add_row("Avg Cost/Hypothesis", f"${metrics.avg_cost_per_hypothesis:,.0f}")
        table.add_row(
            "ROI Estimate",
            f"[{'green' if metrics.roi_estimate > 0 else 'red'}]{metrics.roi_estimate:+.0f}%[/]",
        )

        return Panel(table, title="[bold]Key Metrics[/bold]")

    def _render_breakdown_panel(self, metrics: DashboardMetrics) -> Panel:
        """Render breakdown panel."""
        # Domain distribution
        domain_table = Table(title="Domain Distribution", show_header=False, box=None)
        domain_table.add_column("Domain", style="cyan")
        domain_table.add_column("Count", style="magenta", justify="right")

        for domain, count in sorted(
            metrics.domain_distribution.items(), key=lambda x: -x[1]
        )[:5]:
            domain_table.add_row(domain, str(count))

        # Method effectiveness
        method_table = Table(title="Method Success Rates", show_header=False, box=None)
        method_table.add_column("Method", style="cyan")
        method_table.add_column("Rate", style="magenta", justify="right")

        for method, rate in sorted(
            metrics.method_success_rates.items(), key=lambda x: -x[1]
        ):
            method_table.add_row(method, f"{rate:.1%}")

        # Recent activity
        activity_text = (
            f"This week: [cyan]{metrics.discoveries_this_week}[/] discoveries\n"
            f"This month: [cyan]{metrics.discoveries_this_month}[/] discoveries\n"
            f"Active experiments: [yellow]{metrics.active_experiments}[/]"
        )

        from rich.columns import Columns

        content = Columns([domain_table, method_table])

        return Panel(content, title="[bold]Breakdown[/bold]")

    def export_metrics(self, output_path: str, format: str = "json"):
        """Export metrics to file."""
        metrics = self.calculate_metrics(force_refresh=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_hypotheses": metrics.total_hypotheses,
                "validated_hypotheses": metrics.validated_hypotheses,
                "falsified_hypotheses": metrics.falsified_hypotheses,
                "pending_validation": metrics.pending_validation,
                "avg_time_to_hypothesis": metrics.avg_time_to_hypothesis,
                "avg_time_to_validation": metrics.avg_time_to_validation,
                "validation_rate": metrics.validation_rate,
                "avg_confidence_score": metrics.avg_confidence_score,
                "calibration_score": metrics.calibration_score,
                "total_estimated_cost": metrics.total_estimated_cost,
                "avg_cost_per_hypothesis": metrics.avg_cost_per_hypothesis,
                "roi_estimate": metrics.roi_estimate,
                "discoveries_this_week": metrics.discoveries_this_week,
                "discoveries_this_month": metrics.discoveries_this_month,
                "active_experiments": metrics.active_experiments,
                "domain_distribution": metrics.domain_distribution,
                "method_success_rates": metrics.method_success_rates,
            },
        }

        if format == "json":
            Path(output_path).write_text(json.dumps(data, indent=2))

        console.print(f"[green]✓ Metrics exported to {output_path}[/green]")


# Singleton
_dashboard: Optional[Dashboard] = None


def get_dashboard() -> Dashboard:
    """Get singleton dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = Dashboard()
    return _dashboard
