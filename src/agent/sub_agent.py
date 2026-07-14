"""SubAgent — lightweight spawned agent for parallel/background tasks."""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass

from src.agent.config import AgentConfig


@dataclass
class SubAgentResult:
    name: str
    status: str  # running, completed, failed
    task: str = ""
    result: str = ""
    duration_sec: float = 0.0
    error: str = ""


class SubAgentManager:
    """Manages spawned sub-agents for parallel execution.

    Sub-agents are lightweight: no MCP bridge, no soul, just skills + LLM.
    """

    def __init__(self) -> None:
        self._agents: dict[str, SubAgentResult] = {}
        self._lock = threading.Lock()

    def spawn(self, task: str, model: str | None = None) -> str:
        """Spawn a sub-agent for a background task."""
        name = f"sub-{uuid.uuid4().hex[:8]}"
        result = SubAgentResult(name=name, status="running", task=task)
        with self._lock:
            self._agents[name] = result

        thread = threading.Thread(
            target=self._run_sub_agent,
            args=(name, task, model),
            daemon=True,
        )
        thread.start()
        return name

    def _run_sub_agent(self, name: str, task: str, model: str | None = None) -> None:
        """Run a sub-agent in background thread."""
        start = time.perf_counter()
        try:
            from src.agent.core import AgentCore

            config = AgentConfig.load()
            if model:
                config.provider.model = model

            agent = AgentCore()
            response = agent.process(f"Execute this task: {task}")
            result = SubAgentResult(
                name=name,
                status="completed",
                task=task,
                result=response.content,
                duration_sec=time.perf_counter() - start,
            )
        except Exception as e:
            result = SubAgentResult(
                name=name,
                status="failed",
                task=task,
                result="",
                duration_sec=time.perf_counter() - start,
                error=str(e),
            )

        with self._lock:
            self._agents[name] = result

    def get(self, name: str) -> SubAgentResult | None:
        """Get sub-agent status and result."""
        with self._lock:
            return self._agents.get(name)

    def list_all(self) -> list[SubAgentResult]:
        """List all sub-agents."""
        with self._lock:
            return list(self._agents.values())

    def list_active(self) -> list[SubAgentResult]:
        """List running sub-agents."""
        with self._lock:
            return [a for a in self._agents.values() if a.status == "running"]

    def list_completed(self) -> list[SubAgentResult]:
        """List completed sub-agents."""
        with self._lock:
            return [a for a in self._agents.values() if a.status == "completed"]
