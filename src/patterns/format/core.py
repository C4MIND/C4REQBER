"""
C4REQBER: Pattern Result Formatter — Core Formatter
"""
from __future__ import annotations


__all__ = [
    "PatternResultFormatter",
]

import json
from typing import Any

from src.patterns.format.utils import (
    _detect_result_type,
    _extract_agents,
    _extract_behavior,
    _extract_ci,
    _extract_constraints,
    _extract_flows,
    _extract_metrics,
    _extract_objective,
    _extract_samples,
    _extract_solution,
    _extract_steps,
    _extract_stocks,
    _extract_variables,
    _fmt_val,
    _md_agent_based,
    _md_monte_carlo,
    _md_optimization,
    _md_system_dynamics,
    _pick_key_metrics,
)


class PatternResultFormatter:
    """
    Formatter for simulation pattern results.

    Supports multiple output formats:
    - markdown: rich markdown with tables and headers
    - text: plain text
    - html: HTML markup
    - json: JSON string
    - synthesis: compact text for LLM prompts
    - display: structured dict for API responses
    """

    # Mapping from pattern_id to result type for specialized formatting
    PATTERN_TYPE_MAP: dict[str, str] = {
        "agent_based": "agent_based",
        "monte_carlo": "monte_carlo",
        "system_dynamics": "system_dynamics",
        "optimization": "optimization",
        "optimization_lp": "optimization",
        "circuit": "circuit",
        "circuit_simulation": "circuit",
        "fem": "fem",
        "cfd": "cfd",
        "thermal": "thermal",
        "n_body": "n_body",
        "rigid_body": "rigid_body",
        "continuum_mechanics": "continuum_mechanics",
        "acoustic_waves": "acoustic_waves",
        "elasticity_3d": "elasticity_3d",
        "maxwell_fdtd": "maxwell_fdtd",
        "poisson_solver": "poisson_solver",
        "wave_optics": "wave_optics",
        "plasma_pic": "plasma_pic",
        "ising_model": "ising_model",
        "phase_field": "phase_field",
        "percolation": "percolation",
        "lotka_volterra": "lotka_volterra",
        "epidemic_seir": "epidemic_seir",
        "spatial_ecology": "spatial_ecology",
        "hodgkin_huxley": "hodgkin_huxley",
        "neural_mass": "neural_mass",
        "neural_network": "neural_network",
        "game_theory": "game_theory",
        "dsge": "dsge",
        "supply_chain": "supply_chain",
        "climate_gcm": "climate_gcm",
        "quantum": "quantum",
        "molecular_dynamics": "molecular_dynamics",
    }

    def __init__(self) -> None:
        self._formatters: dict[str, callable] = {  # type: ignore[valid-type]
            "markdown": self._format_markdown,
            "text": self._format_text,
            "html": self._format_html,
            "json": self._format_json,
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def format(self, result: dict[str, Any], format_type: str = "markdown") -> str:
        """Format a pattern result into the requested string format."""
        fmt = format_type.lower()
        if fmt not in self._formatters:
            raise ValueError(f"Unknown format '{format_type}'. Supported: {list(self._formatters)}")
        return self._formatters[fmt](result)  # type: ignore[misc, no-any-return]

    def format_for_synthesis(self, result: dict[str, Any]) -> str:
        """Compact text suitable for inclusion in an LLM synthesis prompt."""
        pattern_id = result.get("pattern_id", "unknown")
        result_type = _detect_result_type(result, self.PATTERN_TYPE_MAP)

        lines: list[str] = []
        lines.append(f"Pattern '{pattern_id}' ({result_type}) result:")

        data = result.get("result", {})
        status = result.get("status", "unknown")
        lines.append(f"Status: {status}.")

        if status == "failed":
            error = result.get("error", "unknown error")
            lines.append(f"Execution failed with error: {error}.")
            return " ".join(lines)

        # Type-specific compact summary
        metrics = _extract_metrics(data)
        if metrics:
            key_metrics = _pick_key_metrics(metrics, max_items=6)
            metrics_str = ", ".join(f"{k}={_fmt_val(v)}" for k, v in key_metrics.items())
            lines.append(f"Key metrics: {metrics_str}.")

        # Logs / narrative
        logs = data.get("logs", [])
        if logs:
            lines.append(f"Summary: {logs[0]}")

        return " ".join(lines)

    def format_for_display(self, result: dict[str, Any]) -> dict[str, Any]:
        """Structured dict for JSON API responses."""
        pattern_id = result.get("pattern_id", "unknown")
        status = result.get("status", "unknown")
        data = result.get("result", {})

        display: dict[str, Any] = {
            "pattern_id": pattern_id,
            "status": status,
            "execution_time_seconds": result.get("execution_time_seconds", 0.0),
            "timestamp": result.get("timestamp", ""),
        }

        if status == "failed":
            display["error"] = result.get("error", "")
            return display

        result_type = _detect_result_type(result, self.PATTERN_TYPE_MAP)
        display["result_type"] = result_type

        # Extract structured sections based on type
        display["metrics"] = _extract_metrics(data)
        display["logs"] = data.get("logs", [])

        # Type-specific sections
        if result_type == "agent_based":
            display["agents"] = _extract_agents(data)
            display["steps"] = _extract_steps(data)
        elif result_type == "monte_carlo":
            display["samples"] = _extract_samples(data)
            display["confidence_interval"] = _extract_ci(data)
        elif result_type == "system_dynamics":
            display["stocks"] = _extract_stocks(data)
            display["flows"] = _extract_flows(data)
            display["behavior"] = _extract_behavior(data)
        elif result_type == "optimization":
            display["objective"] = _extract_objective(data)
            display["variables"] = _extract_variables(data)
            display["constraints"] = _extract_constraints(data)
            display["solution"] = _extract_solution(data)

        return display

    # ------------------------------------------------------------------ #
    # Format implementations
    # ------------------------------------------------------------------ #

    def _format_markdown(self, result: dict[str, Any]) -> str:
        """Rich markdown output with tables and headers."""
        pattern_id = result.get("pattern_id", "unknown")
        status = result.get("status", "unknown")
        data = result.get("result", {})
        result_type = _detect_result_type(result, self.PATTERN_TYPE_MAP)

        lines: list[str] = []
        lines.append(f"# Pattern Result: `{pattern_id}`")
        lines.append("")
        lines.append(f"**Status:** {status}  ")
        lines.append(f"**Type:** {result_type}  ")
        lines.append(f"**Execution time:** {result.get('execution_time_seconds', 0):.3f}s  ")
        lines.append("")

        if status == "failed":
            lines.append("## Error")
            lines.append("")
            lines.append(f"```\n{result.get('error', 'unknown error')}\n```")
            return "\n".join(lines)

        # Metrics table
        metrics = _extract_metrics(data)
        if metrics:
            lines.append("## Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in metrics.items():
                lines.append(f"| {k} | {_fmt_val(v)} |")
            lines.append("")

        # Type-specific sections
        if result_type == "agent_based":
            lines.extend(_md_agent_based(data))
        elif result_type == "monte_carlo":
            lines.extend(_md_monte_carlo(data))
        elif result_type == "system_dynamics":
            lines.extend(_md_system_dynamics(data))
        elif result_type == "optimization":
            lines.extend(_md_optimization(data))

        # Logs
        logs = data.get("logs", [])
        if logs:
            lines.append("## Logs")
            lines.append("")
            for log in logs:
                lines.append(f"- {log}")
            lines.append("")

        return "\n".join(lines)

    def _format_text(self, result: dict[str, Any]) -> str:
        """Plain text output."""
        pattern_id = result.get("pattern_id", "unknown")
        status = result.get("status", "unknown")
        data = result.get("result", {})
        result_type = _detect_result_type(result, self.PATTERN_TYPE_MAP)

        lines: list[str] = []
        lines.append(f"Pattern: {pattern_id}")
        lines.append(f"Status: {status}")
        lines.append(f"Type: {result_type}")
        lines.append(f"Execution time: {result.get('execution_time_seconds', 0):.3f}s")
        lines.append("")

        if status == "failed":
            lines.append(f"Error: {result.get('error', 'unknown error')}")
            return "\n".join(lines)

        metrics = _extract_metrics(data)
        if metrics:
            lines.append("Metrics:")
            for k, v in metrics.items():
                lines.append(f"  {k}: {_fmt_val(v)}")
            lines.append("")

        logs = data.get("logs", [])
        if logs:
            lines.append("Logs:")
            for log in logs:
                lines.append(f"  - {log}")

        return "\n".join(lines)

    def _format_html(self, result: dict[str, Any]) -> str:
        """HTML output."""
        pattern_id = result.get("pattern_id", "unknown")
        status = result.get("status", "unknown")
        data = result.get("result", {})
        result_type = _detect_result_type(result, self.PATTERN_TYPE_MAP)

        lines: list[str] = []
        lines.append(f'<div class="pattern-result" data-pattern="{pattern_id}">')
        lines.append(f"  <h2>Pattern Result: <code>{pattern_id}</code></h2>")
        status_span = f'<span class="status-{status}">{status}</span>'
        lines.append(f"  <p><strong>Status:</strong> {status_span}</p>")
        lines.append(f"  <p><strong>Type:</strong> {result_type}</p>")
        exec_time = result.get("execution_time_seconds", 0)
        lines.append(f"  <p><strong>Execution time:</strong> {exec_time:.3f}s</p>")

        if status == "failed":
            lines.append(f'  <pre class="error">{result.get("error", "unknown error")}</pre>')
            lines.append("</div>")
            return "\n".join(lines)

        metrics = _extract_metrics(data)
        if metrics:
            lines.append("  <h3>Metrics</h3>")
            lines.append('  <table class="metrics-table">')
            lines.append("    <tr><th>Metric</th><th>Value</th></tr>")
            for k, v in metrics.items():
                lines.append(f"    <tr><td>{k}</td><td>{_fmt_val(v)}</td></tr>")
            lines.append("  </table>")

        logs = data.get("logs", [])
        if logs:
            lines.append("  <h3>Logs</h3>")
            lines.append("  <ul>")
            for log in logs:
                lines.append(f"    <li>{log}</li>")
            lines.append("  </ul>")

        lines.append("</div>")
        return "\n".join(lines)

    def _format_json(self, result: dict[str, Any]) -> str:
        """Pretty-printed JSON output."""
        return json.dumps(result, indent=2, default=str)
