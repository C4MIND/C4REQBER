from pathlib import Path


"""
Tests for PatternResultFormatter
"""

import sys

import pytest


_root = Path(__file__).resolve().parent
project_root = _root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.patterns.formatter import PatternResultFormatter


@pytest.fixture
def formatter():
    return PatternResultFormatter()


# --------------------------------------------------------------------------- #
# Fixtures: sample results for each pattern type
# --------------------------------------------------------------------------- #


@pytest.fixture
def agent_based_result():
    return {
        "pattern_id": "agent_based",
        "status": "completed",
        "execution_time_seconds": 1.234,
        "timestamp": "2026-04-25T00:00:00",
        "result": {
            "metrics": {
                "final_mean_wealth": 150.5,
                "final_gini": 0.3421,
                "equilibrium_reached": True,
                "phase_transitions": 2,
                "n_agents": 100,
                "n_steps": 1000,
                "wealth_trend": 0.05,
            },
            "logs": [
                "Simulation ran for 1000 steps",
                "Final mean wealth: 150.50",
            ],
        },
    }


@pytest.fixture
def monte_carlo_result():
    return {
        "pattern_id": "monte_carlo",
        "status": "completed",
        "execution_time_seconds": 2.5,
        "timestamp": "2026-04-25T00:00:00",
        "result": {
            "metrics": {
                "mean": 42.123456,
                "std": 5.6789,
                "ci_lower": 40.0,
                "ci_upper": 44.2,
                "ess": 8500.0,
                "n_samples": 10000,
            },
            "logs": [
                "Completed 10000 samples",
                "Mean: 42.123456 ± 0.056789",
            ],
        },
    }


@pytest.fixture
def system_dynamics_result():
    return {
        "pattern_id": "system_dynamics",
        "status": "completed",
        "execution_time_seconds": 3.0,
        "timestamp": "2026-04-25T00:00:00",
        "result": {
            "metrics": {
                "susceptible_initial": 990.0,
                "susceptible_final": 50.0,
                "susceptible_mean": 400.0,
                "susceptible_std": 300.0,
                "infected_initial": 10.0,
                "infected_final": 5.0,
                "infected_mean": 200.0,
                "infected_std": 150.0,
                "recovered_initial": 0.0,
                "recovered_final": 945.0,
                "recovered_mean": 400.0,
                "recovered_std": 350.0,
                "is_stable": False,
                "is_chaotic": False,
                "chaos_indicator_k": 0.12,
                "n_equilibria": 1,
            },
            "logs": [
                "Simulation completed: 1000 time points",
                "Integration successful",
            ],
        },
    }


@pytest.fixture
def optimization_result():
    return {
        "pattern_id": "optimization_lp",
        "status": "completed",
        "execution_time_seconds": 0.5,
        "timestamp": "2026-04-25T00:00:00",
        "result": {
            "metrics": {
                "optimal_value": 1234.5678,
                "success": True,
                "num_iterations": 42,
                "optimal_variables": [1.0, 2.0, 3.0],
                "sensitivity": {
                    "binding_constraints": 2,
                    "total_constraints": 5,
                },
            },
            "logs": [
                "Optimization succeeded",
                "Optimal value: 1234.5678",
            ],
        },
    }


@pytest.fixture
def failed_result():
    return {
        "pattern_id": "monte_carlo",
        "status": "failed",
        "execution_time_seconds": 0.1,
        "timestamp": "2026-04-25T00:00:00",
        "error": "Division by zero in model evaluation",
        "result": {},
    }


# --------------------------------------------------------------------------- #
# Tests: format()
# --------------------------------------------------------------------------- #


class TestFormatMarkdown:
    def test_markdown_header(self, formatter, agent_based_result):
        md = formatter.format(agent_based_result, "markdown")
        assert "# Pattern Result: `agent_based`" in md
        assert "**Status:** completed" in md

    def test_markdown_metrics_table(self, formatter, monte_carlo_result):
        md = formatter.format(monte_carlo_result, "markdown")
        assert "| Metric | Value |" in md
        assert "mean" in md

    def test_markdown_agent_based_section(self, formatter, agent_based_result):
        md = formatter.format(agent_based_result, "markdown")
        assert "### Agent Summary" in md
        assert "Final mean wealth: 150.50" in md

    def test_markdown_monte_carlo_section(self, formatter, monte_carlo_result):
        md = formatter.format(monte_carlo_result, "markdown")
        assert "### Statistical Summary" in md
        assert "95% CI:" in md

    def test_markdown_system_dynamics_section(self, formatter, system_dynamics_result):
        md = formatter.format(system_dynamics_result, "markdown")
        assert "### Stock Trajectories" in md
        assert "susceptible" in md

    def test_markdown_optimization_section(self, formatter, optimization_result):
        md = formatter.format(optimization_result, "markdown")
        assert "### Optimization Result" in md
        assert "Optimal value:" in md

    def test_markdown_failed(self, formatter, failed_result):
        md = formatter.format(failed_result, "markdown")
        assert "## Error" in md
        assert "Division by zero" in md


class TestFormatText:
    def test_text_basic(self, formatter, agent_based_result):
        text = formatter.format(agent_based_result, "text")
        assert "Pattern: agent_based" in text
        assert "Status: completed" in text
        assert "Metrics:" in text

    def test_text_failed(self, formatter, failed_result):
        text = formatter.format(failed_result, "text")
        assert "Error: Division by zero" in text


class TestFormatHtml:
    def test_html_structure(self, formatter, agent_based_result):
        html = formatter.format(agent_based_result, "html")
        assert '<div class="pattern-result"' in html
        assert "agent_based" in html

    def test_html_failed(self, formatter, failed_result):
        html = formatter.format(failed_result, "html")
        assert '<pre class="error">' in html


class TestFormatJson:
    def test_json_output(self, formatter, agent_based_result):
        js = formatter.format(agent_based_result, "json")
        assert '"pattern_id": "agent_based"' in js
        assert '"status": "completed"' in js


class TestFormatUnknown:
    def test_unknown_format_raises(self, formatter, agent_based_result):
        with pytest.raises(ValueError, match="Unknown format"):
            formatter.format(agent_based_result, "xml")


# --------------------------------------------------------------------------- #
# Tests: format_for_synthesis()
# --------------------------------------------------------------------------- #


class TestFormatForSynthesis:
    def test_synthesis_compact(self, formatter, agent_based_result):
        synth = formatter.format_for_synthesis(agent_based_result)
        assert "Pattern 'agent_based'" in synth
        assert "Status: completed" in synth
        assert "Key metrics:" in synth

    def test_synthesis_failed(self, formatter, failed_result):
        synth = formatter.format_for_synthesis(failed_result)
        assert "Execution failed with error:" in synth
        assert "Division by zero" in synth

    def test_synthesis_monte_carlo(self, formatter, monte_carlo_result):
        synth = formatter.format_for_synthesis(monte_carlo_result)
        assert "mean=" in synth or "Key metrics:" in synth


# --------------------------------------------------------------------------- #
# Tests: format_for_display()
# --------------------------------------------------------------------------- #


class TestFormatForDisplay:
    def test_display_structure(self, formatter, agent_based_result):
        disp = formatter.format_for_display(agent_based_result)
        assert disp["pattern_id"] == "agent_based"
        assert disp["status"] == "completed"
        assert "metrics" in disp
        assert "agents" in disp
        assert "steps" in disp

    def test_display_monte_carlo(self, formatter, monte_carlo_result):
        disp = formatter.format_for_display(monte_carlo_result)
        assert disp["result_type"] == "monte_carlo"
        assert "samples" in disp
        assert "confidence_interval" in disp

    def test_display_system_dynamics(self, formatter, system_dynamics_result):
        disp = formatter.format_for_display(system_dynamics_result)
        assert disp["result_type"] == "system_dynamics"
        assert "stocks" in disp
        assert "behavior" in disp

    def test_display_optimization(self, formatter, optimization_result):
        disp = formatter.format_for_display(optimization_result)
        assert disp["result_type"] == "optimization"
        assert "objective" in disp
        assert "variables" in disp
        assert "constraints" in disp
        assert "solution" in disp

    def test_display_failed(self, formatter, failed_result):
        disp = formatter.format_for_display(failed_result)
        assert disp["status"] == "failed"
        assert "error" in disp
        assert "metrics" not in disp


# --------------------------------------------------------------------------- #
# Tests: type detection heuristics
# --------------------------------------------------------------------------- #

from src.patterns.format.utils import _detect_result_type, _fmt_val, _pick_key_metrics


class TestTypeDetection:
    def test_detect_agent_based(self, formatter, agent_based_result):
        assert _detect_result_type(agent_based_result, formatter.PATTERN_TYPE_MAP) == "agent_based"

    def test_detect_monte_carlo(self, formatter, monte_carlo_result):
        assert _detect_result_type(monte_carlo_result, formatter.PATTERN_TYPE_MAP) == "monte_carlo"

    def test_detect_system_dynamics(self, formatter, system_dynamics_result):
        assert (
            _detect_result_type(system_dynamics_result, formatter.PATTERN_TYPE_MAP)
            == "system_dynamics"
        )

    def test_detect_optimization(self, formatter, optimization_result):
        assert (
            _detect_result_type(optimization_result, formatter.PATTERN_TYPE_MAP) == "optimization"
        )

    def test_detect_generic(self, formatter):
        generic = {"pattern_id": "unknown", "result": {"metrics": {"foo": 1}}}
        assert _detect_result_type(generic, formatter.PATTERN_TYPE_MAP) == "generic"


# --------------------------------------------------------------------------- #
# Tests: helper utilities
# --------------------------------------------------------------------------- #


class TestHelpers:
    def test_fmt_val_float(self, formatter):
        assert _fmt_val(3.14159) == "3.1416"

    def test_fmt_val_large_float(self, formatter):
        assert "e" in _fmt_val(1e9)

    def test_fmt_val_bool(self, formatter):
        assert _fmt_val(True) == "Yes"
        assert _fmt_val(False) == "No"

    def test_fmt_val_none(self, formatter):
        assert _fmt_val(None) == "N/A"

    def test_pick_key_metrics(self, formatter):
        metrics = {"mean": 1.0, "std": 0.1, "extra": 42}
        picked = _pick_key_metrics(metrics, max_items=2)
        assert len(picked) == 2
        assert "mean" in picked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
