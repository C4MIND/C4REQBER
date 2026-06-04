"""
Grafana Dashboard Generator for C44TCDI v4.2
Generates dashboard JSON for monitoring LLM costs, simulation performance,
and verification success rates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DashboardPanel:
    """Represents a Grafana dashboard panel."""
    title: str
    panel_type: str = "timeseries"
    targets: list[dict[str, Any]] = field(default_factory=list)
    grid_pos: dict[str, int] = field(default_factory=dict)
    id: int = 0
    description: str = ""
    unit: str = ""
    decimals: int | None = None
    thresholds: list[dict[str, Any]] | None = None
    overrides: list[dict[str, Any]] = field(default_factory=list)
    field_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class GrafanaDashboard:
    """Represents a complete Grafana dashboard."""
    title: str
    panels: list[DashboardPanel] = field(default_factory=list)
    uid: str = "C44TCDI-overview"
    tags: list[str] = field(default_factory=lambda: ["C44TCDI", "c4", "monitoring"])
    timezone: str = "browser"
    refresh: str = "30s"
    time: dict[str, str] = field(default_factory=lambda: {"from": "now-1h", "to": "now"})


class GrafanaDashboardGenerator:
    """Generates Grafana dashboard JSON for C44TCDI monitoring."""

    def __init__(self, prometheus_datasource: str = "Prometheus") -> None:
        self.prometheus_datasource = prometheus_datasource
        self.panels: list[DashboardPanel] = []
        self.next_panel_id = 1

    def _next_id(self) -> int:
        """Get next panel ID."""
        id_val = self.next_panel_id
        self.next_panel_id += 1
        return id_val

    def _create_prometheus_target(
        self,
        expr: str,
        legend: str = "",
        ref_id: str = "A",
    ) -> dict[str, Any]:
        """Create a Prometheus query target."""
        return {
            "refId": ref_id,
            "expr": expr,
            "legendFormat": legend,
            "datasource": {"type": "prometheus", "uid": self.prometheus_datasource},
        }

    def add_llm_cost_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add LLM costs over time panel."""
        panel = DashboardPanel(
            title="LLM Costs Over Time",
            panel_type="timeseries",
            description="Cumulative and per-model LLM API costs",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 0, "y": 0},
            id=self._next_id(),
            unit="USD",
            targets=[
                self._create_prometheus_target(
                    "rate(llm_cost_usd_total[5m])",
                    "Cost Rate ($/s) - {{model}}",
                ),
                self._create_prometheus_target(
                    "llm_cost_usd_total",
                    "Total Cost - {{model}}",
                ),
                self._create_prometheus_target(
                    "sum(llm_cost_usd_total) by (provider)",
                    "Total Cost by Provider",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "USD",
                    "decimals": 4,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1},
                            {"color": "red", "value": 10},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_llm_tokens_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add LLM token usage panel."""
        panel = DashboardPanel(
            title="LLM Token Usage",
            panel_type="timeseries",
            description="Input and output token usage over time",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 12, "y": 0},
            id=self._next_id(),
            targets=[
                self._create_prometheus_target(
                    "rate(llm_tokens_total_input[5m])",
                    "Input Tokens/s - {{model}}",
                ),
                self._create_prometheus_target(
                    "rate(llm_tokens_total_output[5m])",
                    "Output Tokens/s - {{model}}",
                ),
                self._create_prometheus_target(
                    "llm_tokens_total_input",
                    "Total Input Tokens - {{model}}",
                ),
                self._create_prometheus_target(
                    "llm_tokens_total_output",
                    "Total Output Tokens - {{model}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "short",
                    "decimals": 0,
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_llm_latency_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add LLM latency panel."""
        panel = DashboardPanel(
            title="LLM Latency",
            panel_type="timeseries",
            description="LLM API call latency in milliseconds",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 0, "y": 8},
            id=self._next_id(),
            unit="ms",
            targets=[
                self._create_prometheus_target(
                    "histogram_quantile(0.50, llm_latency_ms)",
                    "p50 Latency - {{model}}",
                ),
                self._create_prometheus_target(
                    "histogram_quantile(0.90, llm_latency_ms)",
                    "p90 Latency - {{model}}",
                ),
                self._create_prometheus_target(
                    "histogram_quantile(0.99, llm_latency_ms)",
                    "p99 Latency - {{model}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "ms",
                    "decimals": 0,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1000},
                            {"color": "red", "value": 5000},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_llm_calls_count_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add LLM calls count panel."""
        panel = DashboardPanel(
            title="LLM Calls Count",
            panel_type="stat",
            description="Total LLM API calls",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 12, "y": 8},
            id=self._next_id(),
            targets=[
                self._create_prometheus_target(
                    "llm_calls_total",
                    "Total Calls",
                ),
                self._create_prometheus_target(
                    "rate(llm_calls_total[5m])",
                    "Calls Rate (calls/s)",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "short",
                    "decimals": 0,
                    "color": {"mode": "thresholds"},
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "blue", "value": None},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_simulation_performance_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add simulation performance by engine panel."""
        panel = DashboardPanel(
            title="Simulation Performance by Engine",
            panel_type="timeseries",
            description="Execution time for different physics simulation engines",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 0, "y": 16},
            id=self._next_id(),
            unit="ms",
            targets=[
                self._create_prometheus_target(
                    "histogram_quantile(0.50, simulation_execution_time_ms)",
                    "p50 - {{engine_type}}",
                ),
                self._create_prometheus_target(
                    "histogram_quantile(0.90, simulation_execution_time_ms)",
                    "p90 - {{engine_type}}",
                ),
                self._create_prometheus_target(
                    "rate(simulations_total[5m])",
                    "Simulations Rate - {{engine_type}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "ms",
                    "decimals": 0,
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_simulation_success_rate_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add simulation success rate panel."""
        panel = DashboardPanel(
            title="Simulation Success Rate",
            panel_type="timeseries",
            description="Success rate of simulations by engine type",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 12, "y": 16},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "rate(simulations_success_total[5m]) / rate(simulations_total[5m]) * 100",
                    "Success Rate % - {{engine_type}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": 80},
                            {"color": "green", "value": 95},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_verification_success_rate_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add verification success rate by backend panel."""
        panel = DashboardPanel(
            title="Verification Success Rate by Backend",
            panel_type="timeseries",
            description="Success rate of formal verification by backend (Lean4, Coq, Dafny, etc.)",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 0, "y": 24},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "rate(verifications_verified_total[5m]) / rate(verifications_total[5m]) * 100",
                    "Success Rate % - {{backend}}",
                ),
                self._create_prometheus_target(
                    "verification_success_rate",
                    "Current Success Rate - {{backend}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": 70},
                            {"color": "green", "value": 90},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_verification_counts_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add verification counts panel."""
        panel = DashboardPanel(
            title="Verification Counts by Backend",
            panel_type="bargauge",
            description="Verified vs Failed counts by verification backend",
            grid_pos=grid_pos or {"h": 8, "w": 12, "x": 12, "y": 24},
            id=self._next_id(),
            targets=[
                self._create_prometheus_target(
                    "verifications_verified_total",
                    "Verified - {{backend}}",
                ),
                self._create_prometheus_target(
                    "verifications_failed_total",
                    "Failed - {{backend}}",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "short",
                    "decimals": 0,
                    "displayMode": "gradient",
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "Verified"},
                        "properties": [
                            {"id": "color", "value": {"mode": "fixed", "fixedColor": "green"}},
                        ],
                    },
                    {
                        "matcher": {"id": "byName", "options": "Failed"},
                        "properties": [
                            {"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}},
                        ],
                    },
                ],
            },
        )
        self.panels.append(panel)
        return panel

    def add_cache_hit_rate_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add cache hit rate panel."""
        panel = DashboardPanel(
            title="Cache Hit Rate",
            panel_type="stat",
            description="Prompt caching hit rate (target >80%)",
            grid_pos=grid_pos or {"h": 4, "w": 6, "x": 0, "y": 32},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "cache_hit_rate * 100",
                    "Cache Hit Rate",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": 60},
                            {"color": "green", "value": 80},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_task_completion_rate_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add task completion rate panel."""
        panel = DashboardPanel(
            title="Task Completion Rate",
            panel_type="stat",
            description="Task completion rate (target >90%)",
            grid_pos=grid_pos or {"h": 4, "w": 6, "x": 6, "y": 32},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "task_completion_rate * 100",
                    "Task Completion Rate",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": 80},
                            {"color": "green", "value": 90},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_approval_rate_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add approval rate panel."""
        panel = DashboardPanel(
            title="Approval Rate",
            panel_type="stat",
            description="Human approval rate (target <30%)",
            grid_pos=grid_pos or {"h": 4, "w": 6, "x": 12, "y": 32},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "approval_rate * 100",
                    "Approval Rate",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 30},
                            {"color": "red", "value": 50},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def add_context_drift_panel(
        self,
        grid_pos: dict[str, int] | None = None,
    ) -> DashboardPanel:
        """Add context drift panel."""
        panel = DashboardPanel(
            title="Context Drift",
            panel_type="stat",
            description="Semantic drift between plan and execution (target <5%)",
            grid_pos=grid_pos or {"h": 4, "w": 6, "x": 18, "y": 32},
            id=self._next_id(),
            unit="percent",
            targets=[
                self._create_prometheus_target(
                    "context_drift * 100",
                    "Context Drift",
                ),
            ],
            field_config={
                "defaults": {
                    "unit": "percent",
                    "decimals": 1,
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 3},
                            {"color": "red", "value": 5},
                        ],
                    },
                },
                "overrides": [],
            },
        )
        self.panels.append(panel)
        return panel

    def generate_dashboard(self, title: str = "C44TCDI Overview") -> dict[str, Any]:
        """Generate the complete Grafana dashboard JSON."""
        dashboard: dict[str, Any] = {
            "id": None,
            "uid": "C44TCDI-overview",
            "title": title,
            "tags": ["C44TCDI", "c4", "monitoring", "llm", "simulation", "verification"],
            "timezone": "browser",
            "refresh": "30s",
            "schemaVersion": 38,
            "version": 1,
            "time": {"from": "now-1h", "to": "now"},
            "panels": [],
        }

        for panel in self.panels:
            panel_dict: dict[str, Any] = {
                "id": panel.id,
                "title": panel.title,
                "type": panel.panel_type,
                "description": panel.description,
                "gridPos": panel.grid_pos,
                "targets": panel.targets,
                "fieldConfig": panel.field_config or {
                    "defaults": {},
                    "overrides": panel.overrides,
                },
            }

            # Add thresholds if specified
            if panel.thresholds:
                if "defaults" not in panel_dict["fieldConfig"]:
                    panel_dict["fieldConfig"]["defaults"] = {}
                panel_dict["fieldConfig"]["defaults"]["thresholds"] = {
                    "mode": "absolute",
                    "steps": panel.thresholds,
                }

            dashboard["panels"].append(panel_dict)

        return dashboard

    def save_dashboard(self, output_path: str, title: str = "C44TCDI Overview") -> None:
        """Save the dashboard JSON to file."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        dashboard_json = self.generate_dashboard(title)

        with open(output, "w") as f:
            json.dump(dashboard_json, f, indent=2)

    def create_default_dashboard(self) -> GrafanaDashboardGenerator:
        """Create the default C44TCDI overview dashboard with all panels."""
        # Row 1: LLM Metrics
        self.add_llm_cost_panel()
        self.add_llm_tokens_panel()

        # Row 2: LLM Latency and Calls
        self.add_llm_latency_panel()
        self.add_llm_calls_count_panel()

        # Row 3: Simulation Metrics
        self.add_simulation_performance_panel()
        self.add_simulation_success_rate_panel()

        # Row 4: Verification Metrics
        self.add_verification_success_rate_panel()
        self.add_verification_counts_panel()

        # Row 5: Summary Stats
        self.add_cache_hit_rate_panel()
        self.add_task_completion_rate_panel()
        self.add_approval_rate_panel()
        self.add_context_drift_panel()

        return self


def generate_c4reqber_dashboard(
    output_path: str = "monitoring/grafana/dashboards/c4reqber_overview.json",
    prometheus_datasource: str = "Prometheus",
) -> dict[str, Any]:
    """
    Generate the complete C44TCDI Grafana dashboard.

    Args:
        output_path: Path to save the dashboard JSON
        prometheus_datasource: Name/UID of the Prometheus datasource in Grafana

    Returns:
        The dashboard JSON dictionary
    """
    generator = GrafanaDashboardGenerator(prometheus_datasource)
    generator.create_default_dashboard()
    generator.save_dashboard(output_path)

    return generator.generate_dashboard()


def generate_minimal_dashboard(
    output_path: str = "monitoring/grafana/dashboards/c4reqber_minimal.json",
    prometheus_datasource: str = "Prometheus",
) -> dict[str, Any]:
    """
    Generate a minimal C44TCDI Grafana dashboard with key metrics only.

    Args:
        output_path: Path to save the dashboard JSON
        prometheus_datasource: Name/UID of the Prometheus datasource in Grafana

    Returns:
        The dashboard JSON dictionary
    """
    generator = GrafanaDashboardGenerator(prometheus_datasource)

    # Only add the most important panels
    generator.add_llm_cost_panel()
    generator.add_simulation_performance_panel()
    generator.add_verification_success_rate_panel()
    generator.add_cache_hit_rate_panel()

    generator.save_dashboard(output_path, title="C44TCDI Minimal")

    return generator.generate_dashboard()


if __name__ == "__main__":
    # Generate dashboards when run directly
    print("Generating C44TCDI Grafana dashboards...")

    # Full dashboard
    full_path = "monitoring/grafana/dashboards/c4reqber_overview.json"
    generate_c4reqber_dashboard(full_path)
    print(f"✓ Full dashboard saved to: {full_path}")

    # Minimal dashboard
    minimal_path = "monitoring/grafana/dashboards/c4reqber_minimal.json"
    generate_minimal_dashboard(minimal_path)
    print(f"✓ Minimal dashboard saved to: {minimal_path}")

    print("\nDashboard generation complete!")
