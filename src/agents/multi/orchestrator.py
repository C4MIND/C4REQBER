"""
C4REQBER: Multi-Agent System — Orchestrator
"""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from src.agents.multi.agents import (
    AnalystAgent,
    CriticAgent,
    ScientistAgent,
    SynthesizerAgent,
)
from src.agents.multi.core import AgentMessage, AgentOutput, AgentRole


console = Console()


class MultiAgentSystem:
    """Multi-Agent Scientific Discovery System."""

    def __init__(self) -> None:
        self.agents: dict[AgentRole, Any] = {
            AgentRole.ANALYST: AnalystAgent(),
            AgentRole.SCIENTIST: ScientistAgent(),
            AgentRole.CRITIC: CriticAgent(),
            AgentRole.SYNTHESIZER: SynthesizerAgent(),
        }
        self.message_bus: list[AgentMessage] = []

    async def discover(self, problem: str) -> dict[str, Any]:
        """Run multi-agent discovery process."""
        console.print(
            Panel.fit(
                f"[bold blue]🤖 Multi-Agent Discovery System[/bold blue]\n\n"
                f"Problem: {problem}\n"
                f"Agents: Analyst → Scientist → Critic → Synthesizer",
                title="Starting Discovery",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("[cyan]Analyst analyzing problem...", total=None)
            analysis = await self.agents[AgentRole.ANALYST].process({"problem": problem})
            self._broadcast(analysis, AgentRole.ANALYST)
            progress.update(task1, completed=True)

            task2 = progress.add_task("[cyan]Scientist generating hypotheses...", total=None)
            hypotheses = await self.agents[AgentRole.SCIENTIST].process({"analysis": analysis.content})
            self._broadcast(hypotheses, AgentRole.SCIENTIST)
            progress.update(task2, completed=True)

            task3 = progress.add_task("[cyan]Critic evaluating hypotheses...", total=None)
            critique = await self.agents[AgentRole.CRITIC].process({})
            self._broadcast(critique, AgentRole.CRITIC)
            progress.update(task3, completed=True)

            task4 = progress.add_task("[cyan]Synthesizer creating recommendations...", total=None)
            synthesis = await self.agents[AgentRole.SYNTHESIZER].process({})
            progress.update(task4, completed=True)

        return {
            "problem": problem,
            "analysis": analysis.content,
            "hypotheses": hypotheses.content,
            "critique": critique.content,
            "synthesis": synthesis.content,
            "agent_count": len(self.agents),
        }

    def _broadcast(self, output: AgentOutput, from_role: AgentRole) -> None:
        """Broadcast output to all other agents."""
        message = AgentMessage(
            from_agent=output.agent_name,
            to_agent="all",
            message_type=output.output_type,
            content=output.content,
        )
        for role, agent in self.agents.items():
            if role != from_role:
                agent.receive_message(message)
        self.message_bus.append(message)

    def render_conversation_tree(self) -> str:
        """Render conversation tree for visualization."""
        tree = Tree("[bold]Multi-Agent Conversation[/bold]")
        for msg in self.message_bus:
            branch = tree.add(f"[cyan]{msg.from_agent}[/cyan] → {msg.message_type}")
            if isinstance(msg.content, list):
                branch.add(f"[{len(msg.content)} items]")
            elif isinstance(msg.content, dict):
                branch.add(f"[{len(msg.content)} keys]")
        return str(tree)


def get_multi_agent_system() -> MultiAgentSystem:
    """Get singleton multi-agent system (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("multi_agent_system", MultiAgentSystem)
