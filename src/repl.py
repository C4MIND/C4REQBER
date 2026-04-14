#!/usr/bin/env python3
"""
TURBO-CDI: Interactive REPL Mode
Full-featured research environment
"""

import cmd
import sys
import os
from typing import Optional

sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")

from core.cdi_engine import CDIEngine, PhysicalContradiction, ContradictionType
from core.c4_state import C4State
from extractors.contradiction import ContradictionExtractor
from data.database import PatternDatabase
from projects.manager import ProjectManager, ResearchProject, Task, Milestone
from bibliography.manager import BibliographyManager, Reference
from export.manager import ExportManager
from visualization.c4_viz import C4Visualizer
from adapters.ollama_adapter import LLMProvider


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


class TurboCDIShell(cmd.Cmd):
    """Interactive TURBO-CDI shell."""

    intro = f"""
{Style.CYAN}{Style.BOLD}
╔══════════════════════════════════════════════════════════════╗
║  ⚡ TURBO-CDI Interactive Research Environment v3.0          ║
║  Type 'help' for commands, 'exit' to quit                   ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET}
"""
    prompt = f"{Style.CYAN}turbo-cdi{Style.RESET} ❯ "

    def __init__(self):
        super().__init__()
        self.engine = CDIEngine()
        self.extractor = ContradictionExtractor()
        self.db = PatternDatabase()
        self.projects = ProjectManager()
        self.biblio = BibliographyManager()
        self.exporter = ExportManager()
        self.viz = C4Visualizer()
        self.llm = LLMProvider(
            openrouter_key=os.getenv("OPENROUTER_API_KEY"), prefer_local=False
        )
        self.current_project: Optional[int] = None

    # ========== Core Commands ==========

    def do_solve(self, arg):
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
        if self.llm.active != "mock":
            print(f"\n{Style.BOLD}Synthesizing hypothesis...{Style.RESET}")
            prompt = f"""Problem: {arg}
Contradiction: {contradiction}
C4 Path: {" → ".join([t.operator for t in solution.c4_path])}

Generate a specific scientific hypothesis."""

            response = self.llm.generate(prompt, temperature=0.7, max_tokens=500)
            solution.hypothesis = (
                response.content if hasattr(response, "content") else response
            )

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
            created_at=__import__("datetime").datetime.now().isoformat(),
            notes="",
        )
        disc_id = self.db.save_discovery(discovery)
        print(f"\n{Style.GRAY}Saved to database (ID: {disc_id}){Style.RESET}")

        # Link to current project if any
        if self.current_project:
            self.projects.add_hypothesis_to_project(self.current_project, disc_id)
            print(f"{Style.GRAY}Linked to current project{Style.RESET}")

    def do_visualize(self, arg):
        """Visualize C4 space: visualize [path]"""
        print(f"\n{self.viz.draw_cube_2d()}")

    def do_operators(self, arg):
        """List all 27 C4 operators"""
        from core.operators import Operators

        ops = Operators()

        print(f"\n{Style.BOLD}Base Operators (9):{Style.RESET}")
        for name, op in ops.base.items():
            print(
                f"  {Style.CYAN}{op.symbol:8}{Style.RESET} {name:20} - {op.description}"
            )

        print(f"\n{Style.BOLD}Composed Operators (18):{Style.RESET}")
        for name, op in ops.composed.items():
            print(
                f"  {Style.MAGENTA}{op.symbol:8}{Style.RESET} {name:25} - {op.description}"
            )

    # ========== Project Commands ==========

    def do_project(self, arg):
        """Project management: project <create|list|switch|show> [args]"""
        parts = arg.split(maxsplit=1)
        if not parts:
            print(
                f"{Style.YELLOW}Usage: project <create|list|switch|show> [args]{Style.RESET}"
            )
            return

        cmd = parts[0]

        if cmd == "create":
            if len(parts) < 2:
                print(
                    f"{Style.YELLOW}Usage: project create <name> [--domain=<domain>]{Style.RESET}"
                )
                return

            name = parts[1]
            domain = "general"
            if "--domain=" in name:
                name, domain_part = name.split("--domain=")
                domain = domain_part.strip()
                name = name.strip()

            project = ResearchProject(
                id=None,
                name=name,
                description="",
                domain=domain,
                status="active",
                created_at=__import__("datetime").datetime.now().isoformat(),
                updated_at=__import__("datetime").datetime.now().isoformat(),
                objectives=[],
                hypotheses=[],
                collaborators=[],
                tags=[],
                notes="",
            )

            proj_id = self.projects.create_project(project)
            self.current_project = proj_id
            print(
                f"{Style.GREEN}✓ Created project '{name}' (ID: {proj_id}){Style.RESET}"
            )
            print(f"{Style.GRAY}Switched to new project{Style.RESET}")

        elif cmd == "list":
            projs = self.projects.list_projects()
            print(f"\n{Style.BOLD}Projects:{Style.RESET}")
            for p in projs:
                current = " →" if p.id == self.current_project else ""
                print(f"  [{p.id}] {p.name} ({p.domain}) - {p.status}{current}")

        elif cmd == "switch":
            if len(parts) < 2:
                print(f"{Style.YELLOW}Usage: project switch <project_id>{Style.RESET}")
                return

            try:
                proj_id = int(parts[1])
                proj = self.projects.get_project(proj_id)
                if proj:
                    self.current_project = proj_id
                    print(
                        f"{Style.GREEN}✓ Switched to project '{proj.name}'{Style.RESET}"
                    )
                else:
                    print(f"{Style.RED}✗ Project not found{Style.RESET}")
            except ValueError:
                print(f"{Style.RED}✗ Invalid project ID{Style.RESET}")

        elif cmd == "show":
            if not self.current_project:
                print(
                    f"{Style.YELLOW}No active project. Use 'project switch <id>'{Style.RESET}"
                )
                return

            proj = self.projects.get_project(self.current_project)
            if proj:
                print(f"\n{Style.BOLD}{proj.name}{Style.RESET}")
                print(f"  Domain: {proj.domain}")
                print(f"  Status: {proj.status}")
                print(f"  Created: {proj.created_at}")

                # Stats
                stats = self.projects.get_project_stats(proj.id)
                print(f"\n  Tasks: {stats.get('total_tasks', 0)}")
                print(
                    f"  Milestones: {stats.get('completed_milestones', 0)}/{stats.get('total_milestones', 0)}"
                )
                print(f"  Log entries: {stats.get('log_entries', 0)}")

    def do_task(self, arg):
        """Task management: task <add|list|done> [args]"""
        if not self.current_project:
            print(
                f"{Style.YELLOW}No active project. Use 'project switch <id>'{Style.RESET}"
            )
            return

        parts = arg.split(maxsplit=1)
        if not parts:
            print(f"{Style.YELLOW}Usage: task <add|list|done> [args]{Style.RESET}")
            return

        cmd = parts[0]

        if cmd == "add":
            if len(parts) < 2:
                print(
                    f"{Style.YELLOW}Usage: task add <title> [--priority=1-5]{Style.RESET}"
                )
                return

            title = parts[1]
            priority = 3

            task = Task(
                id=None,
                project_id=self.current_project,
                title=title,
                description="",
                status="todo",
                priority=priority,
                due_date=None,
                created_at=__import__("datetime").datetime.now().isoformat(),
                tags=[],
            )

            task_id = self.projects.create_task(task)
            print(f"{Style.GREEN}✓ Task added (ID: {task_id}){Style.RESET}")

        elif cmd == "list":
            tasks = self.projects.get_project_tasks(self.current_project)
            print(f"\n{Style.BOLD}Tasks:{Style.RESET}")
            for t in tasks:
                status_icon = "✓" if t.status == "done" else "○"
                print(f"  [{status_icon}] [{t.id}] {t.title} (P{t.priority})")

        elif cmd == "done":
            if len(parts) < 2:
                print(f"{Style.YELLOW}Usage: task done <task_id>{Style.RESET}")
                return

            try:
                task_id = int(parts[1])
                self.projects.complete_task(task_id)
                print(f"{Style.GREEN}✓ Task completed{Style.RESET}")
            except ValueError:
                print(f"{Style.RED}✗ Invalid task ID{Style.RESET}")

    # ========== Discovery Commands ==========

    def do_discoveries(self, arg):
        """List discoveries: discoveries [--domain=<domain>] [--limit=N]"""
        domain = None
        limit = 10

        if "--domain=" in arg:
            domain = arg.split("--domain=")[1].split()[0]
        if "--limit=" in arg:
            limit = int(arg.split("--limit=")[1].split()[0])

        discoveries = self.db.get_discoveries(domain=domain)

        print(f"\n{Style.BOLD}Discoveries:{Style.RESET}")
        for d in discoveries[:limit]:
            print(f"\n  {Style.CYAN}[{d.id}]{Style.RESET} {d.hypothesis[:60]}...")
            print(
                f"    Domain: {d.domain} | Confidence: {d.confidence:.2f} | Status: {d.status}"
            )

    def do_export(self, arg):
        """Export discovery: export <discovery_id> [--format=md|json|html]"""
        parts = arg.split()
        if not parts:
            print(
                f"{Style.YELLOW}Usage: export <discovery_id> [--format=md|json]{Style.RESET}"
            )
            return

        try:
            disc_id = int(parts[0])
        except ValueError:
            print(f"{Style.RED}✗ Invalid discovery ID{Style.RESET}")
            return

        # Get discovery
        discoveries = self.db.get_discoveries()
        discovery = next((d for d in discoveries if d.id == disc_id), None)

        if not discovery:
            print(f"{Style.RED}✗ Discovery not found{Style.RESET}")
            return

        # Export
        format_type = "md"
        if "--format=json" in arg:
            format_type = "json"

        if format_type == "md":
            filepath = self.exporter.export_discovery_markdown(discovery.__dict__)
        else:
            filepath = self.exporter.export_json(discovery.__dict__)

        print(f"{Style.GREEN}✓ Exported to: {filepath}{Style.RESET}")

    # ========== Bibliography Commands ==========

    def do_ref(self, arg):
        """Reference management: ref <add|search|list> [args]"""
        parts = arg.split(maxsplit=1)
        if not parts:
            print(f"{Style.YELLOW}Usage: ref <add|search|list> [args]{Style.RESET}")
            return

        cmd = parts[0]

        if cmd == "search":
            if len(parts) < 2:
                print(f"{Style.YELLOW}Usage: ref search <query>{Style.RESET}")
                return

            refs = self.biblio.search_references(parts[1])
            print(f"\n{Style.BOLD}References ({len(refs)}):{Style.RESET}")
            for r in refs[:5]:
                authors = ", ".join(r.authors[:2]) + (
                    " et al." if len(r.authors) > 2 else ""
                )
                print(f"  [{r.cite_key}] {r.title[:50]}... ({r.year})")
                print(f"    {authors}")

        elif cmd == "list":
            refs = self.biblio.search_references("")
            print(f"\n{Style.BOLD}Bibliography ({len(refs)} references):{Style.RESET}")
            for r in refs[:10]:
                print(f"  [{r.cite_key}] {r.title[:50]}...")

    # ========== Stats Commands ==========

    def do_stats(self, arg):
        """Show database statistics"""
        stats = self.db.get_stats()

        print(f"\n{Style.BOLD}Database Statistics:{Style.RESET}")
        print(f"  Discoveries: {stats.get('discoveries', 0)}")
        print(f"  Validated: {stats.get('validated', 0)}")
        print(f"  Patterns: {stats.get('patterns', 0)}")
        print(f"  Avg Confidence: {stats.get('avg_confidence', 0):.2f}")

        # LLM status
        print(f"\n{Style.BOLD}LLM Provider:{Style.RESET} {self.llm.active}")

    # ========== System Commands ==========

    def do_clear(self, arg):
        """Clear screen"""
        os.system("clear" if os.name != "nt" else "cls")
        print(self.intro)

    def do_exit(self, arg):
        """Exit TURBO-CDI"""
        print(f"\n{Style.GREEN}Good luck with your research! ⚡{Style.RESET}\n")
        return True

    def do_EOF(self, arg):
        """Handle Ctrl+D"""
        return self.do_exit(arg)

    def emptyline(self):
        """Handle empty line"""
        pass

    def default(self, line):
        """Handle unknown command"""
        print(f"{Style.RED}Unknown command: {line}{Style.RESET}")
        print(f"Type 'help' for available commands")


def main():
    """Start interactive shell."""
    shell = TurboCDIShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print(f"\n\n{Style.GREEN}Good luck with your research! ⚡{Style.RESET}\n")


if __name__ == "__main__":
    main()
