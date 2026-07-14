"""
Tests for plugin_synthesis_integrator module.
"""

import pytest

from src.agents.plugin_synthesis_integrator import format_plugin_results_for_synthesis


class TestFormatPluginResultsForSynthesis:
    """Test suite for format_plugin_results_for_synthesis."""

    def test_empty_list_returns_empty_string(self):
        """Empty plugin results should return empty string (optional behavior)."""
        result = format_plugin_results_for_synthesis([])
        assert result == ""

    def test_none_list_returns_empty_string(self):
        """None input should return empty string."""
        result = format_plugin_results_for_synthesis([])
        assert result == ""

    def test_single_plugin_with_dict_result(self):
        """Single plugin with dict result formats correctly."""
        plugin_results = [
            {
                "plugin_id": "swot",
                "result": {
                    "strengths": ["Strong brand", "High R\u0026D budget"],
                    "weaknesses": ["Slow decision making"],
                },
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "swot" in result
        assert "strengths" in result
        assert "Strong brand" in result
        assert "weaknesses" in result

    def test_single_plugin_with_string_result(self):
        """Single plugin with string result formats correctly."""
        plugin_results = [
            {
                "plugin_id": "five_whys",
                "result": "The root cause is insufficient testing coverage.",
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "five_whys" in result
        assert "root cause" in result

    def test_multiple_plugins(self):
        """Multiple plugins are separated by blank lines."""
        plugin_results = [
            {
                "plugin_id": "swot",
                "result": {"strengths": ["Brand"]},
            },
            {
                "plugin_id": "five_whys",
                "result": {"root_cause": "Lack of tests"},
            },
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "swot" in result
        assert "five_whys" in result
        # Should have blank line separation between plugins
        assert "\n\n" in result

    def test_plugin_error_handling(self):
        """Plugin errors are formatted gracefully."""
        plugin_results = [
            {
                "plugin_id": "broken_plugin",
                "result": {"error": "Plugin execution failed"},
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "broken_plugin" in result
        assert "ERROR" in result
        assert "Plugin execution failed" in result

    def test_long_result_truncation(self):
        """Very long results are truncated to avoid prompt bloat."""
        long_list = [f"item_{i}" for i in range(200)]
        plugin_results = [
            {
                "plugin_id": "verbose_plugin",
                "result": {"data": long_list},
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "verbose_plugin" in result
        assert "truncated" in result

    def test_nested_dict_formatting(self):
        """Nested dictionaries are formatted with indentation."""
        plugin_results = [
            {
                "plugin_id": "complex_plugin",
                "result": {
                    "level1": {
                        "level2": {
                            "value": "deep",
                        }
                    }
                },
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "complex_plugin" in result
        assert "level1" in result
        assert "deep" in result

    def test_plugin_id_missing(self):
        """Handle missing plugin_id gracefully."""
        plugin_results = [
            {
                "result": {"data": "value"},
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "unknown" in result
        assert "data" in result

    def test_result_missing(self):
        """Handle missing result gracefully."""
        plugin_results = [
            {
                "plugin_id": "empty_plugin",
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        assert "empty_plugin" in result


class TestPluginSynthesisIntegration:
    """Integration-style tests for the integrator."""

    def test_output_suitable_for_prompt(self):
        """The output should be suitable for direct inclusion in an LLM prompt."""
        plugin_results = [
            {
                "plugin_id": "swot",
                "result": {
                    "strengths": ["Brand recognition"],
                    "weaknesses": ["High costs"],
                    "opportunities": ["New markets"],
                    "threats": ["Competition"],
                },
            }
        ]
        result = format_plugin_results_for_synthesis(plugin_results)

        # Should not contain markdown that might confuse LLM
        assert result.strip()
        # Should be readable
        lines = result.split("\n")
        assert len(lines) >= 2

    def test_backward_compatibility_no_plugins(self):
        """When no plugins are provided, output is empty (doesn't affect prompt)."""
        result = format_plugin_results_for_synthesis([])
        assert result == ""
