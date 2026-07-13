#!/usr/bin/env python3
"""C4REQBER Interactive REPL Mode - Core shell and styling."""

from __future__ import annotations

import cmd
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_key


_project_root = Path(__file__).resolve().parent.parent
_src = _project_root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from adapters.ollama_adapter import LLMProvider
from bibliography.manager import BibliographyManager
from core.cdi_engine import CDIEngine, ContradictionType, PhysicalContradiction
from data.database import PatternDatabase
from export.manager import ExportManager
from extractors.contradiction import ContradictionExtractor
from projects.manager import ProjectManager
from visualization.c4_viz import C4Visualizer


class Style:
    """ANSI styles."""

    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class C4REQBERShell(cmd.Cmd):
    """Interactive C4REQBER shell."""

    intro = f"""
{Style.CYAN}{Style.BOLD}
╔══════════════════════════════════════════════════════════════╗
║  ⚡ C4REQBER Interactive Research Environment v5.4          ║
║  Type 'help' for commands, 'exit' to quit                   ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET}
"""
    prompt = f"{Style.CYAN}c4reqber{Style.RESET} ❯ "

    def __init__(self) -> None:
        super().__init__()
        self.engine = CDIEngine()
        self.extractor = ContradictionExtractor()
        self.db = PatternDatabase()
        self.projects = ProjectManager()
        self.biblio = BibliographyManager()
        self.exporter = ExportManager()
        self.viz = C4Visualizer()
        self.llm = LLMProvider(
            openrouter_key=get_key("openrouter") or os.getenv("OPENROUTER_API_KEY"),
            prefer_local=False,
        )
        self.current_project: int | None = None

    # ========== Core Commands ==========

    def do_solve(self, arg: Any) -> None:
        """Solve a research problem: solve <problem statement> [--domain=<domain>]"""
        if not arg:
            print(f"{Style.YELLOW}Usage: solve <problem statement>{Style.RESET}")
            return

        print(f"\n{Style.BOLD}Analyzing problem...{Style.RESET}")

        # Extract contradiction
        contradiction = self.extractor.extract(arg)
        if not contradiction:
            print(
                f"{Style.YELLOW}No clear contradiction found. Using generic approach.{Style.RESET}"
            )
            contradiction = PhysicalContradiction(
                parameter="solution",
                value_a="current",
                value_not_a="innovative",
                requirement_y="stability",
                requirement_z="progress",
                contradiction_type=ContradictionType.CONFLICTING_GOALS,
            )
        else:
            print(f"{Style.GREEN}✓ Contradiction:{Style.RESET} {contradiction}")

        # Solve
        print(f"\n{Style.BOLD}Navigating C4 space...{Style.RESET}")
        solution = self.engine.solve(contradiction)

        # Visualize path
        print(
            f"\n{self.viz.draw_path_timeline([t.to_state for t in solution.c4_path], [t.operator for t in solution.c4_path])}"
        )

        # Generate hypothesis with LLM if available
        if self.llm.active == "none":
            print(
                f"\n{Style.YELLOW}No LLM provider configured — skipping hypothesis synthesis.{Style.RESET}"
            )
            print(f"{Style.DIM}Set OPENROUTER_API_KEY or start Ollama.{Style.RESET}")  # type: ignore[attr-defined]
        else:
            print(f"\n{Style.BOLD}Synthesizing hypothesis...{Style.RESET}")
            prompt = f"""Problem: {arg}
Contradiction: {contradiction}
C4 Path: {" → ".join([t.operator for t in solution.c4_path])}

Generate a specific scientific hypothesis."""

            response = self.llm.generate(prompt, temperature=0.7, max_tokens=500)
            solution.hypothesis = response.content if hasattr(response, "content") else response

        print(f"\n{Style.GREEN}{Style.BOLD}═ HYPOTHESIS ═{Style.RESET}")
        print(solution.hypothesis)

        # Save
        from data.database import Discovery

        discovery = Discovery(
            id=None,
            problem=arg,
            contradiction=str(contradiction),
            hypothesis=solution.hypothesis,
            c4_path=[t.operator for t in solution.c4_path],
            domain="general",
            confidence=solution.confidence_score,
            falsifiability_criteria=[],
            status="pending",
            created_at=datetime.now().isoformat(),
            notes="",
        )
        disc_id = self.db.save_discovery(discovery)
        print(f"\n{Style.GRAY}Saved to database (ID: {disc_id}){Style.RESET}")

        # Link to current project if any
        if self.current_project:
            self.projects.add_hypothesis_to_project(self.current_project, disc_id)
            print(f"{Style.GRAY}Linked to current project{Style.RESET}")

    def do_visualize(self, arg: Any) -> None:
        """Visualize C4 space: visualize [path]"""
        print(f"\n{self.viz.draw_cube_2d()}")

    def do_operators(self, arg: Any) -> None:
        """List all 27 C4 operators"""
        from core.operators import Operators

        ops = Operators()

        print(f"\n{Style.BOLD}Base Operators (9):{Style.RESET}")
        for name, op in ops.base.items():
            print(f"  {Style.CYAN}{op.symbol:8}{Style.RESET} {name:20} - {op.description}")

        print(f"\n{Style.BOLD}Composed Operators (18):{Style.RESET}")
        for name, op in ops.composed.items():
            print(f"  {Style.MAGENTA}{op.symbol:8}{Style.RESET} {name:25} - {op.description}")

    # ========== System Commands ==========

    def do_clear(self, arg: Any) -> None:
        """Clear screen"""
        import subprocess

        cmd = "cls" if os.name == "nt" else "clear"
        try:
            subprocess.run([cmd], check=False)
        except (OSError, ValueError):
            print("\033[2J\033[H", end="")
        print(self.intro)

    def do_exit(self, arg: Any) -> Any:
        """Exit C4REQBER"""
        print(f"\n{Style.GREEN}Good luck with your research! ⚡{Style.RESET}\n")
        return True

    def do_EOF(self, arg: Any) -> Any:
        """Handle Ctrl+D"""
        return self.do_exit(arg)

    def emptyline(self) -> None:  # type: ignore[override]
        """Handle empty line"""
        pass

    def default(self, line: Any) -> None:
        """Handle unknown command"""
        print(f"{Style.RED}Unknown command: {line}{Style.RESET}")
        print("Type 'help' for available commands")
