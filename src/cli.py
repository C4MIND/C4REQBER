#!/usr/bin/env python3
"""
TURBO-CDI CLI v2.1
Command-line interface with LLM synthesis
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")

from core.cdi_engine import (
    CDIEngine,
    PhysicalContradiction,
    ContradictionType,
    EinsteinValidator,
)
from core.c4_state import C4State
from extractors.contradiction import ContradictionExtractor
from llm.client import LLMClient, MockLLMClient
from llm.synthesizer import HypothesisSynthesizer
from llm.falsifiability import FalsifiabilityGenerator


def get_llm_client():
    """Get LLM client based on environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return LLMClient(api_key)
    return MockLLMClient()


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  TURBO-CDI v8.4 "Prometheus"                                     ║
║  Scientific Discovery Intelligence Platform                      ║
║  C4³ = 27 operators | 100+ v6 Patterns | Discovery Agent | Auth  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def format_solution(solution, with_falsifiability=False) -> str:
    """Format CDI solution for display."""
    output = []
    output.append(f"\n{'=' * 60}")
    output.append("HYPOTHESIS")
    output.append(f"{'=' * 60}")
    output.append(f"\n{solution.hypothesis}\n")

    output.append(f"{'-' * 60}")
    output.append("NAVIGATION PATH (C4 Cognitive Space)")
    output.append(f"{'-' * 60}")

    if solution.c4_path:
        for i, transition in enumerate(solution.c4_path, 1):
            output.append(
                f"  Step {i}: {transition.operator:12} "
                f"{transition.from_state} → {transition.to_state}"
            )
    else:
        output.append("  (No state transitions - identity solution)")

    output.append(f"\nTotal steps: {solution.steps_taken}/6 (Theorem 11 bound)")
    output.append(f"Confidence: {solution.confidence_score:.2f}")

    # Falsifiability criteria
    if with_falsifiability and hasattr(solution, "falsifiability_criteria"):
        output.append(f"\n{'-' * 60}")
        output.append("FALSIFIABILITY CRITERIA (Karl Popper style)")
        output.append(f"{'-' * 60}")
        for i, criterion in enumerate(solution.falsifiability_criteria[:3], 1):
            output.append(f"\n  {i}. {criterion.statement}")
            output.append(f"     Measurement: {criterion.measurement}")
            output.append(f"     Threshold: {criterion.threshold}")
            output.append(f"     Difficulty: {criterion.difficulty}")

    output.append(f"\n{'-' * 60}")
    output.append("PHYSICAL CONTRADICTION RESOLVED")
    output.append(f"{'-' * 60}")
    output.append(f"  {solution.contradiction}")

    output.append(f"\n{'=' * 60}\n")

    return "\n".join(output)


def cmd_solve(args):
    """Solve a problem using CDI with LLM synthesis."""
    print_banner()

    engine = CDIEngine()
    extractor = ContradictionExtractor()
    llm = get_llm_client()

    print(f"Problem: {args.problem}\n")
    print("Extracting physical contradiction...")

    # Extract contradiction
    contradiction = extractor.extract(args.problem)

    if not contradiction:
        print("⚠️  Could not extract clear physical contradiction.")
        print("Attempting generic CDI approach...")

        # Create generic contradiction
        contradiction = PhysicalContradiction(
            parameter="Solution approach",
            value_a="current_method",
            value_not_a="new_method",
            requirement_y="stability",
            requirement_z="innovation",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )
    else:
        print(f"✓ Found: {contradiction}\n")

    # Solve with CDI
    print("Running CDI algorithm (navigating C4 space)...")
    solution = engine.solve(contradiction)

    # Enhance with LLM if available
    if not isinstance(llm, MockLLMClient) and not args.no_llm:
        print("Synthesizing hypothesis with LLM...")
        synthesizer = HypothesisSynthesizer(llm)
        solution.hypothesis = synthesizer.synthesize(solution, args.domain)

        # Add falsifiability
        if args.falsifiability:
            print("Generating falsifiability criteria...")
            falsifiability = FalsifiabilityGenerator(llm)
            report = falsifiability.generate(solution.hypothesis, args.domain)
            solution.falsifiability_criteria = report.criteria

    print(format_solution(solution, with_falsifiability=args.falsifiability))

    return 0


def cmd_validate(args):
    """Run Einstein Test validation."""
    print_banner()

    engine = CDIEngine()
    validator = EinsteinValidator(engine)

    print("Running Einstein Test validation...\n")

    # STR
    print("Special Theory of Relativity (expected: ≤4 steps)...")
    try:
        str_solution = validator.validate_str()
        print(f"  ✓ STR solved in {str_solution.steps_taken} steps")
        print(f"    Path: {' → '.join([t.operator for t in str_solution.c4_path])}")
    except AssertionError as e:
        print(f"  ✗ STR validation failed: {e}")
        return 1

    # GTR
    print("\nGeneral Theory of Relativity (expected: ≤6 steps)...")
    try:
        gtr_solution = validator.validate_gtr()
        print(f"  ✓ GTR solved in {gtr_solution.steps_taken} steps")
        print(f"    Path: {' → '.join([t.operator for t in gtr_solution.c4_path])}")
    except AssertionError as e:
        print(f"  ✗ GTR validation failed: {e}")
        return 1

    print("\n" + "=" * 60)
    print("✓ All validations passed!")
    print("Theorem 11 confirmed: Any solution reachable in ≤6 steps")
    print("=" * 60 + "\n")

    return 0


def cmd_demo(args):
    """Run demo examples."""
    print_banner()

    demos = {
        "battery": "How to achieve both high energy density (>500 Wh/kg) and fast charging (<10 min) in EV batteries?",
        "material": "How to create a material that is both extremely strong and very lightweight?",
        "software": "How to make software that is both highly secure and very easy to use?",
        "medical": "How to design a drug that is highly effective but has minimal side effects?",
    }

    engine = CDIEngine()
    extractor = ContradictionExtractor()
    llm = get_llm_client()

    if args.example and args.example in demos:
        examples = {args.example: demos[args.example]}
    else:
        examples = demos

    for name, problem in examples.items():
        print(f"\n{'=' * 60}")
        print(f"DEMO: {name.upper()}")
        print(f"{'=' * 60}")
        print(f"Problem: {problem}\n")

        contradiction = extractor.extract(problem)
        if contradiction:
            print(f"Contradiction: {contradiction}\n")
            solution = engine.solve(contradiction)

            # Enhance with LLM if available
            if not isinstance(llm, MockLLMClient):
                synthesizer = HypothesisSynthesizer(llm)
                solution.hypothesis = synthesizer.synthesize(solution, name)

            print(format_solution(solution))
        else:
            print("⚠️  Could not extract contradiction for this demo.")

    return 0


async def cmd_discover(args):
    """Run full discovery cycle with pattern simulation."""
    print_banner()
    from solver.one_shot import get_one_shot_solver

    solver = get_one_shot_solver()
    result = await solver.solve(
        problem=args.problem,
        max_hypotheses=args.max_hypotheses,
        include_validation=not args.no_validation,
        literature_search=not args.no_literature,
        consensus_analysis=not args.no_consensus,
    )

    print(solver.render_summary(result))

    if result.top_hypothesis:
        sim = result.top_hypothesis.get("simulation")
        if sim and sim.get("pattern_id"):
            print(
                f"\n[bold]Pattern Simulation:[/bold] {sim['pattern_id']} → {sim['status']}"
            )
            if sim.get("metrics"):
                for k, v in sim["metrics"].items():
                    print(f"  {k}: {v}")

    if args.output:
        solver.export_report(result, args.output, format=args.format)

    return 0


def cmd_patterns(args):
    """List or run v6 simulation patterns."""
    from patterns.runner import get_runner

    runner = get_runner()

    if args.subcommand == "list":
        print("\n" + "=" * 60)
        print("V6 SIMULATION PATTERNS")
        print("=" * 60)
        patterns = runner.list_patterns()
        print(f"\nTotal loaded: {len(patterns)}\n")
        for pid in patterns:
            meta = runner.get_metadata(pid)
            print(f"  {pid:30} | {meta['class'] if meta else 'Unknown'}")
        print("\n" + "=" * 60 + "\n")

    elif args.subcommand == "info":
        meta = runner.get_metadata(args.pattern_id)
        if not meta:
            print(f"Pattern '{args.pattern_id}' not found.")
            return 1
        resources = runner.estimate_resources(args.pattern_id)
        print("\n" + "=" * 60)
        print(f"PATTERN: {args.pattern_id}")
        print("=" * 60)
        print(f"  Class:       {meta['class']}")
        print(f"  Domain:      {meta.get('domain', 'unknown')}")
        print(f"  Description: {meta.get('description', 'N/A')}")
        print(f"  Memory:      {resources.get('memory_mb', 100)} MB")
        print(f"  GPU:         {'Yes' if resources.get('gpu_required') else 'No'}")
        print(f"  Est. time:   {resources.get('estimated_time_seconds', 60)}s")
        print("=" * 60 + "\n")

    elif args.subcommand == "run":
        import asyncio

        print(f"\nRunning pattern: {args.pattern_id}...")
        result = asyncio.run(
            runner.run_pattern(
                args.pattern_id,
                hypothesis={"title": args.hypothesis, "description": args.hypothesis},
                params={},
            )
        )
        print(f"Status: {result['status']}")
        print(f"Time:   {result.get('execution_time_seconds', 0):.3f}s")
        if result.get("result"):
            metrics = result["result"].get("metrics", {})
            if metrics:
                print("\nMetrics:")
                for k, v in metrics.items():
                    print(f"  {k}: {v}")
        if result.get("error"):
            print(f"\nError: {result['error']}")

    return 0


def cmd_operators(args):
    """List all 27 operators."""
    from core.operators import Operators

    ops = Operators()

    print("\n" + "=" * 60)
    print("TURBO-CDI OPERATORS (27 total)")
    print("=" * 60)

    print("\n--- Base Operators (9) ---")
    for name, op in ops.base.items():
        print(f"  {op.symbol:8} | {name:20} | {op.description}")

    print("\n--- Composed Operators (18) ---")
    for name, op in ops.composed.items():
        print(f"  {op.symbol:8} | {name:25} | {op.description}")

    print("\n" + "=" * 60 + "\n")

    return 0


def cmd_test_llm(args):
    """Test LLM connection."""
    print_banner()

    print("Testing LLM connection...")

    llm = get_llm_client()

    if isinstance(llm, MockLLMClient):
        print("⚠️  No OPENROUTER_API_KEY found. Using Mock LLM.")
        print("    Set OPENROUTER_API_KEY environment variable for real LLM.\n")
        return 1

    if llm.test_connection():
        print("✓ LLM connection successful!")
        print(f"  Default model: {llm.DEFAULT_MODEL}\n")
        return 0
    else:
        print("✗ LLM connection failed. Check your API key.\n")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="turbo-cdi",
        description="TURBO-CDI: Scientific Hypothesis Generation Engine",
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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "solve": cmd_solve,
        "validate": cmd_validate,
        "demo": cmd_demo,
        "discover": cmd_discover,
        "patterns": cmd_patterns,
        "operators": cmd_operators,
        "test-llm": cmd_test_llm,
    }

    import asyncio

    if args.command == "discover":
        return asyncio.run(commands[args.command](args))
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
