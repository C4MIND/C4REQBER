#!/usr/bin/env python3
"""
C4REQBER CLI - Argument parser construction
"""
from __future__ import annotations

import argparse
from typing import Any


def build_parser() -> Any:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="c4reqber",
        description="C4Reqber: Scientific Hypothesis Generation Engine",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Solve command
    solve_parser = subparsers.add_parser(
        "solve", help="Generate hypothesis for a problem"
    )
    solve_parser.add_argument("problem", help="Problem statement to solve")
    solve_parser.add_argument(
        "--domain",
        default="general",
        help="Scientific domain (physics, biology, materials, etc.)",
    )
    solve_parser.add_argument(
        "--falsifiability",
        action="store_true",
        help="Generate falsifiability criteria (requires LLM)",
    )
    solve_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM synthesis (use template only)",
    )

    # Validate command
    subparsers.add_parser("validate", help="Run Einstein Test validation")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo examples")
    demo_parser.add_argument(
        "--example",
        choices=["battery", "material", "software", "medical"],
        help="Specific example to run",
    )

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Run full discovery cycle with simulations"
    )
    discover_parser.add_argument("problem", help="Research problem to solve")
    discover_parser.add_argument(
        "--max-hypotheses", type=int, default=5, help="Max hypotheses to generate"
    )
    discover_parser.add_argument(
        "--no-validation", action="store_true", help="Skip validation planning"
    )
    discover_parser.add_argument(
        "--no-literature", action="store_true", help="Skip literature search"
    )
    discover_parser.add_argument(
        "--no-consensus", action="store_true", help="Skip consensus analysis"
    )
    discover_parser.add_argument("--output", help="Export report to file path")
    discover_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Export format",
    )

    # Patterns command
    patterns_parser = subparsers.add_parser(
        "patterns", help="Manage v6 simulation patterns"
    )
    pattern_sub = patterns_parser.add_subparsers(
        dest="subcommand", help="Pattern commands"
    )
    pattern_sub.add_parser("list", help="List all available patterns")
    info_parser = pattern_sub.add_parser("info", help="Show pattern metadata")
    info_parser.add_argument("pattern_id", help="Pattern ID")
    run_parser = pattern_sub.add_parser("run", help="Run a simulation pattern")
    run_parser.add_argument("pattern_id", help="Pattern ID")
    run_parser.add_argument("hypothesis", help="Hypothesis text to simulate")

    # Operators command
    subparsers.add_parser("operators", help="List all 27 C4 operators")

    # Test LLM command
    subparsers.add_parser("test-llm", help="Test LLM connection")

    return parser
