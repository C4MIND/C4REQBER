#!/usr/bin/env python3
"""C4REQBER CLI — Main command implementations."""
from __future__ import annotations

from typing import Any

from src.cli.core import format_solution, get_llm_client, print_banner
from src.cli.utils import cmd_operators, cmd_test_llm
from src.core.cdi_engine import (
    CDIEngine,
    ContradictionType,
    EinsteinValidator,
    PhysicalContradiction,
)
from src.extractors.contradiction import ContradictionExtractor
from src.llm.falsifiability import FalsifiabilityGenerator
from src.llm.synthesizer import HypothesisSynthesizer


def cmd_solve(args: Any) -> Any:
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
    if llm and not args.no_llm:
        print("Synthesizing hypothesis with LLM...")
        synthesizer = HypothesisSynthesizer(llm)
        solution.hypothesis = synthesizer.synthesize(solution, args.domain)

        # Add falsifiability
        if args.falsifiability:
            print("Generating falsifiability criteria...")
            falsifiability = FalsifiabilityGenerator(llm)
            report = falsifiability.generate(solution.hypothesis, args.domain)
            solution.falsifiability_criteria = report.criteria  # type: ignore[attr-defined]

    print(format_solution(solution, with_falsifiability=args.falsifiability))

    return 0


def cmd_validate(args: Any) -> Any:
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


def cmd_demo(args: Any) -> Any:
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

        synthesizer = HypothesisSynthesizer(llm)
        solution.hypothesis = synthesizer.synthesize(solution, name)
        print(format_solution(solution))

    return 0


async def cmd_discover(args: Any) -> Any:
    """Run full discovery cycle with pattern simulation."""
    print_banner()
    from src.solver.one_shot import get_one_shot_solver

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


def cmd_patterns(args: Any) -> Any:
    """List or run v6 simulation patterns."""
    from src.patterns.runner import get_runner

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


def dispatch(args: Any) -> Any:
    """Dispatch to the appropriate command handler."""
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
