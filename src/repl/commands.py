#!/usr/bin/env python3
"""C4REQBER Interactive REPL Mode - Command implementations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from repl.core import C4REQBERShell, Style


@dataclass
class ResearchProject:
    id: Any = None
    name: str = ""
    description: str = ""
    domain: str = "general"
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    objectives: list = field(default_factory=list)
    hypotheses: list = field(default_factory=list)
    collaborators: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    notes: str = ""


@dataclass
class Task:
    id: Any = None
    project_id: Any = None
    title: str = ""
    description: str = ""
    status: str = "todo"
    priority: int = 3
    due_date: Any = None
    created_at: str = ""
    tags: list = field(default_factory=list)


class C4REQBERCommands(C4REQBERShell):  # type: ignore[misc]
    """REPL commands mixed into the shell."""

    # ========== Project Commands ==========

    def do_project(self, arg: Any) -> None:
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
                created_at=datetime.now().isoformat(),
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

    def do_task(self, arg: Any) -> None:
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
                created_at=datetime.now().isoformat(),
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

    def do_discoveries(self, arg: Any) -> None:
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

    def do_export(self, arg: Any) -> None:
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

    def do_ref(self, arg: Any) -> None:
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

    def do_stats(self, arg: Any) -> None:
        """Show database statistics"""
        stats = self.db.get_stats()

        print(f"\n{Style.BOLD}Database Statistics:{Style.RESET}")
        print(f"  Discoveries: {stats.get('discoveries', 0)}")
        print(f"  Validated: {stats.get('validated', 0)}")
        print(f"  Patterns: {stats.get('patterns', 0)}")
        print(f"  Avg Confidence: {stats.get('avg_confidence', 0):.2f}")

        # LLM status
        print(f"\n{Style.BOLD}LLM Provider:{Style.RESET} {self.llm.active}")
