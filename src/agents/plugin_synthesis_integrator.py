"""
C4REQBER: Plugin Synthesis Integrator
Formats plugin execution results for inclusion in LLM synthesis prompts.
"""

from __future__ import annotations

import json
from typing import Any


__all__ = ["format_plugin_results_for_synthesis"]


def _format_single_result(plugin_result: dict[str, Any]) -> str:
    """Format a single plugin result into structured text."""
    plugin_id = plugin_result.get("plugin_id", "unknown")
    result = plugin_result.get("result", {})

    if isinstance(result, dict) and "error" in result:
        return f"- {plugin_id}: ERROR — {result['error']}"

    lines = [f"- {plugin_id}:"]

    if isinstance(result, dict):
        for key, value in result.items():
            if key in ("plugin_id", "error"):
                continue
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
                # Truncate long nested structures
                if len(value_str) > 400:
                    value_str = value_str[:400] + "\n  ... [truncated]"
                lines.append(f"  - {key}: {value_str}")
            else:
                lines.append(f"  - {key}: {value}")
    else:
        str_result = str(result)
        if len(str_result) > 500:
            str_result = str_result[:500] + "\n  ... [truncated]"
        lines.append(f"  - result: {str_result}")

    return "\n".join(lines)


def format_plugin_results_for_synthesis(plugin_results: list[dict[str, Any]]) -> str:
    """
    Format a list of plugin execution results into structured text
    suitable for inclusion in an LLM synthesis prompt.

    Args:
        plugin_results: List of dicts with keys 'plugin_id' and 'result'.

    Returns:
        A formatted string with plugin analysis sections.
        Returns empty string if plugin_results is empty.
    """
    if not plugin_results:
        return ""

    sections: list[str] = []

    for pr in plugin_results:
        sections.append(_format_single_result(pr))

    return "\n\n".join(sections)
