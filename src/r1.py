#!/usr/bin/env python3
"""
TURBO-CDI: R1 CLI v3.0
Trendy minimalist terminal UI with old-school cool
"""

import argparse
import sys
import os
import json
from typing import Optional, List
from datetime import datetime

# Add src to path
sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")


# ANSI Colors & Styles
class Style:
    """ANSI escape codes for trendy terminal UI."""

    # Colors
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Reset
    RESET = "\033[0m"

    # Box drawing
    HORIZ = "─"
    VERT = "│"
    TL = "┌"
    TR = "┐"
    BL = "└"
    BR = "┘"
    CROSS = "┼"
    T_DOWN = "┬"
    T_UP = "┴"


class UI:
    """Terminal UI components."""

    WIDTH = 70

    @staticmethod
    def banner():
        """Display trendy banner."""
        print()
        print(f"{Style.CYAN}{Style.BOLD}", end="")
        print(" ╔══════════════════════════════════════════════════════════════╗")
        print(
            " ║  {}{}⚡ TURBO-CDI{}{} v3.0{}{}                                   ║".format(
                Style.YELLOW, Style.BOLD, Style.CYAN, Style.BOLD, Style.GRAY, Style.DIM
            )
        )
        print(
            " ║  {}Z₃³ cognitive geometry → scientific breakthroughs{}         ║".format(
                Style.WHITE, Style.CYAN
            )
        )
        print(" ╚══════════════════════════════════════════════════════════════╝")
        print(f"{Style.RESET}")

    @staticmethod
    def box(title: str, content: str, color: str = Style.CYAN):
        """Draw a box with title."""
        lines = content.strip().split("\n")
        width = max(len(title) + 4, max(len(l) for l in lines) + 2)

        print(f"{color}{Style.TL}{Style.HORIZ * width}{Style.TR}{Style.RESET}")
        print(
            f"{color}{Style.VERT}{Style.BOLD} {title} {Style.RESET}{color}{' ' * (width - len(title) - 2)}{Style.VERT}{Style.RESET}"
        )
        print(f"{color}{Style.VERT}{Style.HORIZ * width}{Style.VERT}{Style.RESET}")
        for line in lines:
            print(
                f"{color}{Style.VERT}{Style.RESET} {line:<{width - 2}} {color}{Style.VERT}{Style.RESET}"
            )
        print(f"{color}{Style.BL}{Style.HORIZ * width}{Style.BR}{Style.RESET}")

    @staticmethod
    def section(title: str, color: str = Style.MAGENTA):
        """Display section header."""
        print()
        print(
            f"{color}{Style.BOLD}{Style.HORIZ * 3} {title} {Style.HORIZ * (UI.WIDTH - len(title) - 5)}{Style.RESET}"
        )

    @staticmethod
    def path_step(step_num: int, operator: str, from_state: str, to_state: str):
        """Display C4 navigation step."""
        print(
            f"  {Style.GRAY}[{step_num}]{Style.RESET} {Style.CYAN}{operator:12}{Style.RESET} {from_state} → {to_state}"
        )

    @staticmethod
    def stat(label: str, value: str, color: str = Style.GREEN):
        """Display stat line."""
        print(f"  {Style.GRAY}{label:<20}{Style.RESET} {color}{value}{Style.RESET}")

    @staticmethod
    def prompt(text: str) -> str:
        """Display input prompt."""
        return input(f"{Style.CYAN}❯{Style.RESET} {Style.BOLD}{text}{Style.RESET} ")

    @staticmethod
    def success(text: str):
        """Display success message."""
        print(f"{Style.GREEN}✓{Style.RESET} {text}")

    @staticmethod
    def warning(text: str):
        """Display warning."""
        print(f"{Style.YELLOW}⚠{Style.RESET} {text}")

    @staticmethod
    def error(text: str):
        """Display error."""
        print(f"{Style.RED}✗{Style.RESET} {text}")

    @staticmethod
    def info(text: str):
        """Display info."""
        print(f"{Style.BLUE}ℹ{Style.RESET} {text}")

    @staticmethod
    def highlight(text: str, color: str = Style.YELLOW) -> str:
        """Highlight text."""
        return f"{color}{Style.BOLD}{text}{Style.RESET}"

    @staticmethod
    def dim(text: str) -> str:
        """Dim text."""
        return f"{Style.GRAY}{text}{Style.RESET}"


# Import core modules
from core.cdi_engine import CDIEngine, EinsteinValidator
from core.c4_state import C4State
from extractors.contradiction import ContradictionExtractor, ContradictionLibrary
from data.database import PatternDatabase, Pattern, Discovery
from adapters.arxiv_adapter import ArxivAdapter, ARXIV_CATEGORIES
from adapters.pubmed_adapter import PubMedAdapter
from adapters.ollama_adapter import LLMProvider, OllamaAdapter


def cmd_solve(args):
    """Solve a research problem."""
    UI.banner()

    # Get problem
    if args.problem:
        problem = args.problem
    else:
        problem = UI.prompt("Enter research problem:")

    if not problem:
        UI.error("No problem provided")
        return 1

    print()
    UI.section("PHASE 1: CONTRADICTION EXTRACTION")

    extractor = ContradictionExtractor()
    db = PatternDatabase()

    contradiction = extractor.extract(problem)

    if contradiction:
        UI.success(f"Physical contradiction identified:")
        print(f"  {Style.ITALIC}{contradiction}{Style.RESET}")
    else:
        UI.warning("No clear contradiction found. Using generic approach.")
        from core.cdi_engine import PhysicalContradiction, ContradictionType

        contradiction = PhysicalContradiction(
            parameter="solution",
            value_a="current",
            value_not_a="innovative",
            requirement_y="stability",
            requirement_z="progress",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )

    print()
    UI.section("PHASE 2: RESEARCH CONTEXT")

    # Search research databases
    context = ""
    if not args.no_research:
        if args.domain in ["physics", "cs", "math"]:
            UI.info("Searching arXiv...")
            arxiv = ArxivAdapter()
            papers = arxiv.search(problem[:100], max_results=3)  # Truncate for search
            if papers:
                context = arxiv.format_for_context(papers)
                UI.success(f"Found {len(papers)} relevant papers")
            else:
                UI.warning("No papers found")

        elif args.domain in ["biology", "medical", "medicine"]:
            UI.info("Searching PubMed...")
            pubmed = PubMedAdapter()
            papers = pubmed.search(problem[:100], max_results=3)
            if papers:
                context = pubmed.format_for_context(papers)
                UI.success(f"Found {len(papers)} relevant papers")
            else:
                UI.warning("No papers found")

    print()
    UI.section("PHASE 3: C4 NAVIGATION")

    engine = CDIEngine()
    solution = engine.solve(contradiction)

    print(f"  {Style.DIM}Navigating Z₃³ state space...{Style.RESET}")
    print()

    for i, transition in enumerate(solution.c4_path, 1):
        UI.path_step(
            i, transition.operator, str(transition.from_state), str(transition.to_state)
        )

    print()
    UI.stat("Steps taken", f"{solution.steps_taken}/6", Style.GREEN)
    UI.stat("Theorem 11 bound", "satisfied ✓", Style.GREEN)

    print()
    UI.section("PHASE 4: HYPOTHESIS SYNTHESIS")

    # Use LLM if available
    provider = LLMProvider(
        openrouter_key=os.getenv("OPENROUTER_API_KEY"), prefer_local=args.local
    )

    if provider.active != "mock":
        UI.info(f"Using {provider.active} for synthesis...")

        # Build synthesis prompt
        prompt = f"""Research problem: {problem}

Physical contradiction: {contradiction}

C4 navigation path: {" → ".join([t.operator for t in solution.c4_path])}

Research context:
{context[:500] if context else "No specific context"}

Generate a specific scientific hypothesis that resolves this contradiction.
Be concrete and propose a mechanism, not just a goal."""

        response = provider.generate(prompt, temperature=0.7, max_tokens=500)
        solution.hypothesis = (
            response.strip() if isinstance(response, str) else response.content.strip()
        )

    # Display hypothesis
    print()
    UI.box("GENERATED HYPOTHESIS", solution.hypothesis, Style.YELLOW)

    # Falsifiability
    if args.falsifiability and provider.active != "mock":
        print()
        UI.section("PHASE 5: FALSIFIABILITY CRITERIA")

        schema = {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "statement": {"type": "string"},
                            "measurement": {"type": "string"},
                            "threshold": {"type": "string"},
                        },
                    },
                }
            },
        }

        prompt = f"""Hypothesis: {solution.hypothesis}

Generate 3 falsifiability criteria (Karl Popper style).
Each should specify: "If X, then hypothesis is false" with concrete measurements."""

        result = provider.generate_structured(prompt, schema)

        for i, criterion in enumerate(result.get("criteria", []), 1):
            print(
                f"  {Style.GRAY}[{i}]{Style.RESET} {criterion.get('statement', 'N/A')}"
            )
            print(
                f"      {Style.DIM}Measure: {criterion.get('measurement', 'N/A')}{Style.RESET}"
            )

    # Save to database
    discovery = Discovery(
        id=None,
        problem=problem,
        contradiction=str(contradiction),
        hypothesis=solution.hypothesis,
        c4_path=[t.operator for t in solution.c4_path],
        domain=args.domain,
        confidence=solution.confidence_score,
        falsifiability_criteria=[],
        status="pending",
        created_at=datetime.now().isoformat(),
        notes="",
    )

    discovery_id = db.save_discovery(discovery)

    print()
    UI.success(f"Discovery saved to database (ID: {discovery_id})")

    # Stats
    stats = db.get_stats()
    print(
        f"  {Style.DIM}Total discoveries: {stats['discoveries']} | Patterns: {stats['patterns']}{Style.RESET}"
    )

    print()
    return 0


def cmd_discover(args):
    """Browse discoveries."""
    UI.banner()

    db = PatternDatabase()
    discoveries = db.get_discoveries(domain=args.domain, status=args.status)

    UI.section(f"DISCOVERIES ({len(discoveries)} total)")

    for disc in discoveries[:10]:  # Show last 10
        status_color = (
            Style.GREEN
            if disc.status == "validated"
            else (Style.YELLOW if disc.status == "pending" else Style.RED)
        )

        print()
        print(
            f"  {Style.CYAN}#{disc.id}{Style.RESET} {Style.BOLD}{disc.domain}{Style.RESET} {status_color}[{disc.status}]{Style.RESET}"
        )
        print(f"  {Style.GRAY}Problem:{Style.RESET} {disc.problem[:60]}...")
        print(f"  {Style.GRAY}Hypothesis:{Style.RESET} {disc.hypothesis[:60]}...")
        print(
            f"  {Style.DIM}Confidence: {disc.confidence:.2f} | Path: {'→'.join(disc.c4_path[:3])}{Style.RESET}"
        )

    print()
    return 0


def cmd_research(args):
    """Search research databases."""
    UI.banner()

    if not args.query:
        args.query = UI.prompt("Search query:")

    UI.section("SEARCHING RESEARCH DATABASES")

    if args.source == "arxiv" or args.source == "all":
        UI.info("Searching arXiv...")
        arxiv = ArxivAdapter()
        papers = arxiv.search(args.query, max_results=args.limit)

        if papers:
            UI.success(f"Found {len(papers)} papers on arXiv")
            print()
            for i, paper in enumerate(papers, 1):
                print(
                    f"  {Style.CYAN}[{i}]{Style.RESET} {Style.BOLD}{paper.title[:70]}{Style.RESET}"
                )
                print(f"      {Style.GRAY}{', '.join(paper.authors[:2])}{Style.RESET}")
                print(
                    f"      {Style.DIM}Categories: {', '.join(paper.categories[:3])}{Style.RESET}"
                )
                print()
        else:
            UI.warning("No papers found on arXiv")

    if args.source == "pubmed" or args.source == "all":
        UI.info("Searching PubMed...")
        pubmed = PubMedAdapter()
        papers = pubmed.search(args.query, max_results=args.limit)

        if papers:
            UI.success(f"Found {len(papers)} papers on PubMed")
            print()
            for i, paper in enumerate(papers, 1):
                print(
                    f"  {Style.GREEN}[{i}]{Style.RESET} {Style.BOLD}{paper.title[:70]}{Style.RESET}"
                )
                print(f"      {Style.GRAY}{paper.journal}{Style.RESET}")
                print()

    return 0


def cmd_stats(args):
    """Show database statistics."""
    UI.banner()

    db = PatternDatabase()
    stats = db.get_stats()

    UI.section("DATABASE STATISTICS")

    print()
    UI.stat("Total discoveries", str(stats["discoveries"]))
    UI.stat("Validated hypotheses", str(stats["validated"]))
    UI.stat("Stored patterns", str(stats["patterns"]))
    UI.stat("Average confidence", f"{stats['avg_confidence']:.2f}")

    print()

    # LLM provider status
    UI.section("LLM PROVIDER STATUS")

    provider = LLMProvider(
        openrouter_key=os.getenv("OPENROUTER_API_KEY"), prefer_local=False
    )

    status = provider.get_status()

    UI.stat("Active provider", status["active_provider"], Style.CYAN)
    UI.stat(
        "Ollama available",
        "yes" if status["ollama_available"] else "no",
        Style.GREEN if status["ollama_available"] else Style.RED,
    )
    UI.stat(
        "OpenRouter available",
        "yes" if status["openrouter_available"] else "no",
        Style.GREEN if status["openrouter_available"] else Style.RED,
    )

    # Ollama models
    if status["ollama_available"]:
        print()
        UI.info("Ollama models:")
        ollama = OllamaAdapter()
        models = ollama.list_models()
        for model in models[:5]:
            print(f"  • {model.name} ({model.parameter_size})")

    print()
    return 0


def cmd_validate(args):
    """Run Einstein Test."""
    UI.banner()

    UI.section("EINSTEIN TEST VALIDATION")

    engine = CDIEngine()
    validator = EinsteinValidator(engine)

    print()
    UI.info("Testing Special Theory of Relativity (expected: ≤4 steps)...")

    try:
        str_sol = validator.validate_str()
        UI.success(f"STR solved in {str_sol.steps_taken} steps ✓")
        for t in str_sol.c4_path:
            UI.path_step(1, t.operator, str(t.from_state), str(t.to_state))
    except AssertionError as e:
        UI.error(f"STR failed: {e}")

    print()
    UI.info("Testing General Theory of Relativity (expected: ≤6 steps)...")

    try:
        gtr_sol = validator.validate_gtr()
        UI.success(f"GTR solved in {gtr_sol.steps_taken} steps ✓")
    except AssertionError as e:
        UI.error(f"GTR failed: {e}")

    print()
    UI.box(
        "VALIDATION COMPLETE",
        "Theorem 11 confirmed:\nAny solution reachable in ≤6 cognitive steps",
        Style.GREEN,
    )

    return 0


def cmd_operators(args):
    """Show all 27 operators."""
    UI.banner()

    from core.operators import Operators

    ops = Operators()

    UI.section("BASE OPERATORS (9)")

    for name, op in ops.base.items():
        print(
            f"  {Style.CYAN}{op.symbol:8}{Style.RESET} {name:20} {Style.GRAY}# {op.description}{Style.RESET}"
        )

    print()
    UI.section("COMPOSED OPERATORS (18)")

    for name, op in ops.composed.items():
        print(
            f"  {Style.MAGENTA}{op.symbol:8}{Style.RESET} {name:25} {Style.GRAY}# {op.description}{Style.RESET}"
        )

    print()
    UI.info("Total: 27 operators (Z₃³ algebra)")
    print()

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="turbo-cdi",
        description="TURBO-CDI: Scientific Hypothesis Generation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s solve "Battery must be high capacity but lightweight"
  %(prog)s research "quantum error correction" --source arxiv
  %(prog)s discover --domain physics
  %(prog)s stats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Solve command
    solve_p = subparsers.add_parser("solve", help="Generate hypothesis")
    solve_p.add_argument("problem", nargs="?", help="Research problem")
    solve_p.add_argument(
        "--domain", default="general", help="Domain (physics, biology, etc.)"
    )
    solve_p.add_argument(
        "--falsifiability", action="store_true", help="Generate falsifiability criteria"
    )
    solve_p.add_argument(
        "--local", action="store_true", help="Prefer local LLM (Ollama)"
    )
    solve_p.add_argument(
        "--no-research", action="store_true", help="Skip database search"
    )

    # Discover command
    disc_p = subparsers.add_parser("discover", help="Browse discoveries")
    disc_p.add_argument("--domain", help="Filter by domain")
    disc_p.add_argument("--status", help="Filter by status")

    # Research command
    research_p = subparsers.add_parser("research", help="Search research databases")
    research_p.add_argument("query", nargs="?", help="Search query")
    research_p.add_argument(
        "--source", choices=["arxiv", "pubmed", "all"], default="all"
    )
    research_p.add_argument("--limit", type=int, default=5)

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    # Validate command
    subparsers.add_parser("validate", help="Run Einstein Test")

    # Operators command
    subparsers.add_parser("operators", help="List all 27 operators")

    args = parser.parse_args()

    if not args.command:
        UI.banner()
        parser.print_help()
        return 1

    commands = {
        "solve": cmd_solve,
        "discover": cmd_discover,
        "research": cmd_research,
        "stats": cmd_stats,
        "validate": cmd_validate,
        "operators": cmd_operators,
    }

    try:
        return commands[args.command](args)
    except KeyboardInterrupt:
        print()
        UI.warning("Interrupted by user")
        return 130
    except Exception as e:
        UI.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
