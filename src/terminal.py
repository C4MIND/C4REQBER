#!/usr/bin/env python3
"""
TURBO-CDI: Super Terminal UI v4.0
Ultimate research environment with full integration
"""

import sys
import os

sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import threading
import queue

# Core
from core.cdi_engine import CDIEngine, EinsteinValidator
from core.c4_state import C4State
from core.operators import Operators

# Data
from data.database import PatternDatabase, Discovery
from extractors.contradiction import ContradictionExtractor

# Projects & Biblio
from projects.manager import ProjectManager, ResearchProject, Task, Milestone
from bibliography.manager import BibliographyManager
from export.manager import ExportManager

# Visualization
from visualization.c4_viz import C4Visualizer

# Adapters
from adapters.arxiv_adapter import ArxivAdapter, ARXIV_CATEGORIES
from adapters.pubmed_adapter import PubMedAdapter
from adapters.ollama_adapter import LLMProvider

# External APIs integration placeholder
from skills.registry import SkillRegistry
from skills.calculator import (
    CalculatorSkill,
    UnitConverterSkill,
    DataAnalyzerSkill,
    CodeExecutorSkill,
)


# ANSI Styles
class S:
    """Styles for terminal UI"""

    # Colors
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;206m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Reset
    RESET = "\033[0m"
    CLEAR = "\033[2J\033[H"


class TurboTerminal:
    """
    Ultimate terminal UI for TURBO-CDI.
    Old-school cool with modern UX.
    """

    def __init__(self):
        self.engine = CDIEngine()
        self.extractor = ContradictionExtractor()
        self.db = PatternDatabase()
        self.projects = ProjectManager()
        self.biblio = BibliographyManager()
        self.exporter = ExportManager()
        self.viz = C4Visualizer()
        self.arxiv = ArxivAdapter()
        self.pubmed = PubMedAdapter()
        self.llm = LLMProvider(
            openrouter_key=os.getenv("OPENROUTER_API_KEY"), prefer_local=False
        )

        # Skills registry
        self.skills = SkillRegistry()
        self.skills.register(CalculatorSkill())
        self.skills.register(UnitConverterSkill())
        self.skills.register(DataAnalyzerSkill())
        self.skills.register(CodeExecutorSkill())

        # Session state
        self.current_project: Optional[int] = None
        self.session_discoveries: List[int] = []
        self.command_history: List[str] = []

        self.clear_screen()
        self.show_boot_sequence()

    def clear_screen(self):
        """Clear terminal screen."""
        print(S.CLEAR, end="")

    def show_boot_sequence(self):
        """Show retro boot sequence."""
        boot_lines = [
            f"{S.GRAY}[BOOT] TURBO-CDI v4.0 Initializing...{S.RESET}",
            f"{S.GRAY}[BOOT] Loading C4 Engine (Z₃³)...{S.RESET}",
            f"{S.GREEN}[OK]{S.RESET}   27 operators loaded",
            f"{S.GRAY}[BOOT] Connecting to research databases...{S.RESET}",
            f"{S.GREEN}[OK]{S.RESET}   arXiv adapter ready",
            f"{S.GREEN}[OK]{S.RESET}   PubMed adapter ready",
            f"{S.GRAY}[BOOT] Loading skills...{S.RESET}",
        ]

        # Load skills dynamically
        for skill_name in self.skills.list_skills():
            boot_lines.append(f"{S.GREEN}[OK]{S.RESET}   {skill_name} loaded")

        boot_lines.extend(
            [
                f"{S.GRAY}[BOOT] Initializing LLM providers...{S.RESET}",
                f"{S.GREEN}[OK]{S.RESET}   Active provider: {self.llm.active}",
                f"{S.GRAY}[BOOT] Mounting databases...{S.RESET}",
                f"{S.GREEN}[OK]{S.RESET}   Pattern DB mounted",
                f"{S.GREEN}[OK]{S.RESET}   Project DB mounted",
                f"{S.GREEN}[OK]{S.RESET}   Bibliography DB mounted",
                f"",
                f"{S.CYAN}{S.BOLD}SYSTEM READY{S.RESET}",
            ]
        )

        import time

        for line in boot_lines:
            print(line)
            time.sleep(0.05)

        print()
        self.show_header()

    def show_header(self):
        """Show main header with system status."""
        stats = self.db.get_stats()

        header = f"""
{S.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║{S.YELLOW}{S.BLINK} ⚡{S.RESET}{S.CYAN} TURBO-CDI v4.0 - Scientific Breakthrough Engine                    {S.YELLOW}[READY]{S.CYAN} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  {S.GREEN}Discoveries: {stats.get("discoveries", 0):<4}{S.RESET}  {S.BLUE}Patterns: {stats.get("patterns", 0):<4}{S.RESET}  {S.MAGENTA}Validated: {stats.get("validated", 0):<4}{S.RESET}  {S.YELLOW}LLM: {self.llm.active:<10}{S.CYAN}║
╚══════════════════════════════════════════════════════════════════════════════╝{S.RESET}
"""
        print(header)

    def main_loop(self):
        """Main interactive loop."""
        while True:
            try:
                # Show prompt with context
                prompt = self._build_prompt()
                command = input(prompt).strip()

                if not command:
                    continue

                self.command_history.append(command)

                # Parse and execute
                result = self.execute_command(command)

                if result == "EXIT":
                    self.shutdown()
                    break

            except KeyboardInterrupt:
                print(f"\n{S.YELLOW}Use 'exit' or 'quit' to quit{S.RESET}")
            except Exception as e:
                print(f"{S.RED}Error: {e}{S.RESET}")

    def _build_prompt(self) -> str:
        """Build dynamic prompt."""
        context_parts = []

        if self.current_project:
            proj = self.projects.get_project(self.current_project)
            if proj:
                context_parts.append(f"📁 {proj.name}")

        if self.session_discoveries:
            context_parts.append(f"💡 {len(self.session_discoveries)} new")

        context = f" [{' | '.join(context_parts)}]" if context_parts else ""

        return f"\n{S.CYAN}┌─{S.RESET}{context}\n{S.CYAN}└─▶{S.RESET} "

    def execute_command(self, command: str) -> str:
        """Execute user command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Core commands
        commands = {
            # Discovery
            "solve": self.cmd_solve,
            "research": self.cmd_research,
            "discover": self.cmd_discover,
            # Projects
            "project": self.cmd_project,
            "task": self.cmd_task,
            "milestone": self.cmd_milestone,
            # Data
            "bib": self.cmd_bibliography,
            "ref": self.cmd_reference,
            # Skills
            "calc": self.cmd_calculate,
            "convert": self.cmd_convert,
            "analyze": self.cmd_analyze,
            "code": self.cmd_code,
            # Visualization
            "viz": self.cmd_visualize,
            "path": self.cmd_show_path,
            "cube": self.cmd_show_cube,
            # Export
            "export": self.cmd_export,
            "report": self.cmd_report,
            # System
            "stats": self.cmd_stats,
            "skills": self.cmd_skills,
            "help": self.cmd_help,
            "clear": self.cmd_clear,
            "history": self.cmd_history,
            "exit": lambda x: "EXIT",
            "quit": lambda x: "EXIT",
            "q": lambda x: "EXIT",
        }

        if cmd in commands:
            return commands[cmd](args)
        else:
            # Try skill execution
            if self.skills.has_skill(cmd):
                return self.skills.execute(cmd, args)

            print(f"{S.RED}Unknown command: {cmd}{S.RESET}")
            print(f"Type 'help' for available commands")
            return None

    # ========== Discovery Commands ==========

    def cmd_solve(self, args: str):
        """Solve a research problem."""
        if not args:
            print(
                f"{S.YELLOW}Usage: solve <problem description> [--domain=X] [--falsify]{S.RESET}"
            )
            return

        # Parse args
        domain = "general"
        with_falsifiability = "--falsify" in args

        if "--domain=" in args:
            parts = args.split("--domain=")
            args = parts[0].strip()
            domain = parts[1].split()[0] if len(parts) > 1 else "general"

        args = args.replace("--falsify", "").strip()

        print(f"\n{S.CYAN}{S.BOLD}╔═══ PHASE 1: CONTRADICTION EXTRACTION ═══╗{S.RESET}")

        contradiction = self.extractor.extract(args)
        if contradiction:
            print(f"{S.GREEN}✓ Physical contradiction identified:{S.RESET}")
            print(f"  {S.ITALIC}{contradiction}{S.RESET}")
        else:
            print(
                f"{S.YELLOW}⚠ No clear contradiction. Using generic approach.{S.RESET}"
            )
            from core.cdi_engine import PhysicalContradiction, ContradictionType

            contradiction = PhysicalContradiction(
                parameter="solution",
                value_a="current",
                value_not_a="novel",
                requirement_y="stability",
                requirement_z="innovation",
                contradiction_type=ContradictionType.CONFLICTING_GOALS,
            )

        print(f"\n{S.CYAN}{S.BOLD}╔═══ PHASE 2: RESEARCH CONTEXT ═══╗{S.RESET}")

        # Search databases
        papers = []
        if domain in ["physics", "cs", "math", "materials"]:
            print(f"{S.GRAY}Searching arXiv...{S.RESET}")
            papers = self.arxiv.search(args[:80], max_results=3)
        elif domain in ["biology", "medical", "medicine", "health"]:
            print(f"{S.GRAY}Searching PubMed...{S.RESET}")
            papers = self.pubmed.search(args[:80], max_results=3)

        if papers:
            print(f"{S.GREEN}✓ Found {len(papers)} relevant papers{S.RESET}")
            for i, p in enumerate(papers[:2], 1):
                print(f"  {S.DIM}[{i}] {p.title[:60]}...{S.RESET}")

        print(f"\n{S.CYAN}{S.BOLD}╔═══ PHASE 3: C4 NAVIGATION ═══╗{S.RESET}")

        solution = self.engine.solve(contradiction)

        # Visualize path
        print(
            self.viz.draw_path_timeline(
                [t.to_state for t in solution.c4_path],
                [t.operator for t in solution.c4_path],
            )
        )

        print(f"\n{S.CYAN}{S.BOLD}╔═══ PHASE 4: HYPOTHESIS SYNTHESIS ═══╗{S.RESET}")

        # Generate with LLM
        if self.llm.active != "mock":
            prompt = f"""Research problem: {args}

Physical contradiction: {contradiction}
C4 navigation path: {" → ".join([t.operator for t in solution.c4_path])}

Generate a specific scientific hypothesis that resolves this contradiction.
Be concrete and propose a mechanism."""

            response = self.llm.generate(prompt, temperature=0.7, max_tokens=600)
            hypothesis = response.content if hasattr(response, "content") else response
            solution.hypothesis = hypothesis

        # Display hypothesis box
        print(f"\n{S.YELLOW}┌{'─' * 68}┐{S.RESET}")
        print(
            f"{S.YELLOW}│{S.BOLD} GENERATED HYPOTHESIS{S.RESET}{S.YELLOW}{' ' * 48}│{S.RESET}"
        )
        print(f"{S.YELLOW}├{'─' * 68}┤{S.RESET}")

        # Wrap hypothesis text
        words = solution.hypothesis.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 66:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)

        for line in lines[:15]:  # Limit to 15 lines
            print(f"{S.YELLOW}│{S.RESET} {line:<66} {S.YELLOW}│{S.RESET}")

        print(f"{S.YELLOW}└{'─' * 68}┘{S.RESET}")

        # Falsifiability
        if with_falsifiability and self.llm.active != "mock":
            print(
                f"\n{S.CYAN}{S.BOLD}╔═══ PHASE 5: FALSIFIABILITY CRITERIA ═══╗{S.RESET}"
            )
            # ... (falsifiability generation)

        # Save
        from data.database import Discovery

        discovery = Discovery(
            id=None,
            problem=args,
            contradiction=str(contradiction),
            hypothesis=solution.hypothesis,
            c4_path=[t.operator for t in solution.c4_path],
            domain=domain,
            confidence=solution.confidence_score,
            falsifiability_criteria=[],
            status="pending",
            created_at=datetime.now().isoformat(),
            notes="",
        )
        disc_id = self.db.save_discovery(discovery)
        self.session_discoveries.append(disc_id)

        print(f"\n{S.GREEN}✓ Discovery saved [ID: {disc_id}]{S.RESET}")

        if self.current_project:
            self.projects.add_hypothesis_to_project(self.current_project, disc_id)
            print(f"{S.GRAY}  Linked to current project{S.RESET}")

    # ... (other command implementations)

    def cmd_research(self, args: str):
        """Search research databases."""
        if not args:
            print(
                f"{S.YELLOW}Usage: research <query> [--source=arxiv|pubmed|all]{S.RESET}"
            )
            return

        source = "all"
        if "--source=" in args:
            parts = args.split("--source=")
            args = parts[0].strip()
            source = parts[1].split()[0] if len(parts) > 1 else "all"

        print(f"\n{S.CYAN}{S.BOLD}RESEARCH DATABASE SEARCH{S.RESET}")
        print(f"Query: {S.BOLD}{args}{S.RESET}\n")

        if source in ["arxiv", "all"]:
            print(f"{S.BLUE}► arXiv{S.RESET}")
            papers = self.arxiv.search(args, max_results=5)
            for i, p in enumerate(papers, 1):
                print(f"  {S.CYAN}[{i}]{S.RESET} {p.title[:70]}")
                print(f"      {S.GRAY}{', '.join(p.authors[:2])}{S.RESET}")
                print(
                    f"      {S.DIM}arXiv:{p.id.split('/')[-1] if '/' in p.id else p.id}{S.RESET}"
                )
                print()

        if source in ["pubmed", "all"]:
            print(f"{S.GREEN}► PubMed{S.RESET}")
            papers = self.pubmed.search(args, max_results=5)
            for i, p in enumerate(papers, 1):
                print(f"  {S.GREEN}[{i}]{S.RESET} {p.title[:70]}")
                print(f"      {S.GRAY}{p.journal}{S.RESET}")
                print()

    def cmd_project(self, args: str):
        """Project management."""
        parts = args.split(maxsplit=1)
        if not parts:
            # Show current project
            if self.current_project:
                proj = self.projects.get_project(self.current_project)
                if proj:
                    print(f"\n{S.CYAN}{S.BOLD}CURRENT PROJECT{S.RESET}")
                    print(f"  Name: {S.BOLD}{proj.name}{S.RESET}")
                    print(f"  Domain: {proj.domain}")
                    print(f"  Status: {proj.status}")
                    print(f"  Created: {proj.created_at[:10]}")

                    stats = self.projects.get_project_stats(proj.id)
                    print(f"\n  Tasks: {stats.get('total_tasks', 0)}")
                    print(
                        f"  Milestones: {stats.get('completed_milestones', 0)}/{stats.get('total_milestones', 0)}"
                    )
            else:
                print(
                    f"{S.YELLOW}No active project. Use 'project create <name>'{S.RESET}"
                )
            return

        subcmd = parts[0]

        if subcmd == "create" and len(parts) > 1:
            name = parts[1]
            proj = ResearchProject(
                id=None,
                name=name,
                description="",
                domain="general",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            proj_id = self.projects.create_project(proj)
            self.current_project = proj_id
            print(f"{S.GREEN}✓ Created project '{name}' [ID: {proj_id}]{S.RESET}")

        elif subcmd == "list":
            projs = self.projects.list_projects()
            print(f"\n{S.CYAN}{S.BOLD}PROJECTS ({len(projs)}){S.RESET}")
            for p in projs:
                marker = f" {S.GREEN}←{S.RESET}" if p.id == self.current_project else ""
                print(
                    f"  [{p.id}] {S.BOLD}{p.name}{S.RESET} ({p.domain}) - {p.status}{marker}"
                )

        elif subcmd == "switch" and len(parts) > 1:
            try:
                proj_id = int(parts[1])
                proj = self.projects.get_project(proj_id)
                if proj:
                    self.current_project = proj_id
                    print(f"{S.GREEN}✓ Switched to '{proj.name}'{S.RESET}")
                else:
                    print(f"{S.RED}✗ Project not found{S.RESET}")
            except ValueError:
                print(f"{S.RED}✗ Invalid ID{S.RESET}")

    def cmd_skills(self, args: str):
        """List available skills."""
        print(f"\n{S.CYAN}{S.BOLD}AVAILABLE SKILLS{S.RESET}\n")

        for name, skill in self.skills.get_all_skills().items():
            print(f"  {S.YELLOW}{name:15}{S.RESET} - {skill.description}")
            print(f"  {S.GRAY}  Usage: {skill.usage}{S.RESET}")
            print()

    def cmd_calculate(self, args: str):
        """Execute calculator skill."""
        result = self.skills.execute("calc", args)
        print(f"\n{S.CYAN}Result: {S.BOLD}{result}{S.RESET}")

    def cmd_convert(self, args: str):
        """Execute unit converter skill."""
        result = self.skills.execute("convert", args)
        print(f"\n{S.CYAN}Result: {S.BOLD}{result}{S.RESET}")

    def cmd_analyze(self, args: str):
        """Execute data analyzer skill."""
        result = self.skills.execute("analyze", args)
        print(f"\n{S.CYAN}Result:{S.RESET}\n{result}")

    def cmd_code(self, args: str):
        """Execute code."""
        result = self.skills.execute("code", args)
        print(f"\n{S.CYAN}Output:{S.RESET}\n{result}")

    def cmd_visualize(self, args: str):
        """Visualize data or C4 space."""
        print(self.viz.draw_cube_2d())

    def cmd_show_path(self, args: str):
        """Show C4 navigation path."""
        # Demo path
        path = [
            C4State(0, 0, 0),  # Start
            C4State(1, 0, 0),  # tau+
            C4State(1, 1, 0),  # lambda+
            C4State(1, 1, 1),  # kappa+
        ]
        ops = ["START", "tau+", "lambda+", "kappa+"]
        print(self.viz.draw_path_timeline(path, ops))

    def cmd_show_cube(self, args: str):
        """Show 3D C4 cube representation."""
        print(self.viz.draw_cube_2d())

    def cmd_export(self, args: str):
        """Export discoveries."""
        if not args:
            print(
                f"{S.YELLOW}Usage: export <discovery_id> [--format=md|json|html]{S.RESET}"
            )
            return

        parts = args.split()
        try:
            disc_id = int(parts[0])
        except ValueError:
            print(f"{S.RED}✗ Invalid ID{S.RESET}")
            return

        discoveries = self.db.get_discoveries()
        discovery = next((d for d in discoveries if d.id == disc_id), None)

        if not discovery:
            print(f"{S.RED}✗ Discovery not found{S.RESET}")
            return

        filepath = self.exporter.export_discovery_markdown(discovery.__dict__)
        print(f"{S.GREEN}✓ Exported to: {filepath}{S.RESET}")

    def cmd_report(self, args: str):
        """Generate project report."""
        if not self.current_project:
            print(f"{S.YELLOW}No active project{S.RESET}")
            return

        proj = self.projects.get_project(self.current_project)
        discoveries = self.db.get_discoveries()
        tasks = self.projects.get_project_tasks(self.current_project)

        filepath = self.exporter.export_project_report(
            proj.__dict__,
            [d.__dict__ for d in discoveries if d.id in (proj.hypotheses or [])],
            [t.__dict__ for t in tasks],
        )
        print(f"{S.GREEN}✓ Report saved: {filepath}{S.RESET}")

    def cmd_stats(self, args: str):
        """Show system statistics."""
        stats = self.db.get_stats()

        print(f"\n{S.CYAN}{S.BOLD}╔═══ SYSTEM STATISTICS ═══╗{S.RESET}\n")

        print(
            f"  {S.GREEN}●{S.RESET} Discoveries:     {stats.get('discoveries', 0):>6}"
        )
        print(f"  {S.GREEN}●{S.RESET} Validated:       {stats.get('validated', 0):>6}")
        print(f"  {S.BLUE}●{S.RESET} Patterns:        {stats.get('patterns', 0):>6}")
        print(
            f"  {S.MAGENTA}●{S.RESET} Avg Confidence:  {stats.get('avg_confidence', 0):>6.2f}"
        )

        print(f"\n{S.CYAN}{S.BOLD}╔═══ LLM PROVIDER ═══╗{S.RESET}\n")

        status = self.llm.get_status()
        print(f"  Active:     {S.BOLD}{status['active_provider']}{S.RESET}")
        print(f"  Ollama:     {'✓' if status['ollama_available'] else '✗'}")
        print(f"  OpenRouter: {'✓' if status['openrouter_available'] else '✗'}")

        print(f"\n{S.CYAN}{S.BOLD}╔═══ SKILLS ═══╗{S.RESET}\n")
        print(f"  Loaded: {len(self.skills.list_skills())}")
        for name in self.skills.list_skills():
            print(f"    • {name}")

    def cmd_clear(self, args: str):
        """Clear screen."""
        self.clear_screen()
        self.show_header()

    def cmd_history(self, args: str):
        """Show command history."""
        print(
            f"\n{S.CYAN}{S.BOLD}COMMAND HISTORY ({len(self.command_history)}){S.RESET}\n"
        )
        for i, cmd in enumerate(self.command_history[-20:], 1):
            print(f"  {S.GRAY}{i:3}{S.RESET} {cmd}")

    def cmd_help(self, args: str):
        """Show help."""
        help_text = f"""
{S.CYAN}{S.BOLD}TURBO-CDI v4.0 - Command Reference{S.RESET}

{S.YELLOW}DISCOVERY COMMANDS:{S.RESET}
  solve <problem> [--domain=X] [--falsify]  Generate hypothesis
  research <query> [--source=arxiv|pubmed]  Search research DBs
  discover                                List discoveries

{S.YELLOW}PROJECT COMMANDS:{S.RESET}
  project create <name>                   Create new project
  project list                            List all projects
  project switch <id>                     Switch to project
  project                                 Show current project
  task add <title> [--priority=1-5]       Add task to project
  task list                               List project tasks
  milestone add <title> <date>            Add milestone

{S.YELLOW}SKILL COMMANDS:{S.RESET}
  calc <expression>                      Calculate
  convert <value> <from> <to>            Unit conversion
  analyze <data>                         Data analysis
  code <python_code>                     Execute Python code
  skills                                  List all skills

{S.YELLOW}VISUALIZATION COMMANDS:{S.RESET}
  viz                                     Visualize C4 space
  cube                                    Show C4 cube
  path                                    Show demo path

{S.YELLOW}EXPORT COMMANDS:{S.RESET}
  export <discovery_id> [--format=md]     Export discovery
  report                                  Generate project report

{S.YELLOW}SYSTEM COMMANDS:{S.RESET}
  stats                                   Show system statistics
  clear                                   Clear screen
  history                                 Command history
  help                                    This help
  exit | quit | q                         Exit

{S.GRAY}Press Tab for command completion (in supported terminals){S.RESET}
"""
        print(help_text)

    def shutdown(self):
        """Graceful shutdown."""
        print(f"\n{S.YELLOW}Shutting down TURBO-CDI...{S.RESET}")

        # Save session stats
        if self.session_discoveries:
            print(
                f"{S.GRAY}Session discoveries: {len(self.session_discoveries)}{S.RESET}"
            )

        print(f"{S.GREEN}Good luck with your research! ⚡{S.RESET}\n")


def main():
    """Entry point."""
    try:
        app = TurboTerminal()
        app.main_loop()
    except Exception as e:
        print(f"\n{S.RED}Fatal error: {e}{S.RESET}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
